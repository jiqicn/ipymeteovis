"""Methods and Classes definition related to view
"""
from IPython.display import display
import ipyleaflet as ill
import ipywidgets as widgets
from base64 import b64encode
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from dateutil import parser

from .temp import Temp
from .task import Task


class View(object):
    def __init__(self, *args, num_col=1):
        self.c = None
        self.b = None
        self.l = None
        self.w = None

        for arg in args:
            # dual view
            if isinstance(arg, tuple):
                v_list = [View(a) for a in arg]
                self.dual_view(v_list)
                self.c.set_cols(num_col)
                return
            # overlay view
            elif isinstance(arg, list):
                v_list = [View(a) for a in arg]
                self.overlay_view(v_list)
                return

        # if args are View instances or indices
        if isinstance(args[0], View):
            self.c = args[0].c
            self.b = args[0].b
            self.l = args[0].l
            self.w = args[0].w
        else:
            self.unit_view(id=args[0])
        self.c.set_cols(num_col)

    def unit_view(self, id):
        t = Temp(id)
        b = t.profile["task"]["options"]["Bounds"]
        center = [
            (b[0][0] + b[1][0]) * 0.5,
            (b[0][1] + b[1][1]) * 0.5,
        ]
        self.b = Basemap(center)
        self.l = Layer(t.profile)
        self.w = Widgets(t.profile)
        self.c = Container()

        # link container, basemap, layer and widget
        self.w.add_control(self.l)
        self.b.add_layer(self.l)
        self.b.add_control(self.w)
        self.c.add_child(self.b)
        # self.c.add_child(self.w)

    def dual_view(self, v_list):
        self.c = Container()
        for v in v_list:
            self.c.add_child(v.c)

    def overlay_view(self, v_list):
        self.c = Container()
        # compute center of map
        centers = [v.b.center for v in v_list]
        center = [
            sum([c[0] for c in centers]) / len(centers),
            sum([c[1] for c in centers]) / len(centers)
        ]
        self.b = Basemap(center)

        # link
        for v in v_list:
            self.b.add_layer(v.l)
        self.c.add_child(self.b)

    def show(self):
        """Show the view
        :return:
        """
        # display(self.container)
        display(self.c.grid)


class Container(object):
    def __init__(self):
        self.grid = widgets.GridBox(
            children=[],
            layout=widgets.Layout(
                grid_template_columns="100%"  # default to be one column
            )
        )

    def add_child(self, c):
        self.grid.children += (c.get(),)

    def set_cols(self, nc):
        """Adjust template of grid based on number of columns
        :param nc:
        :return:
        """
        w = round(100.0 / nc, 2)
        fmt = ""
        for i in range(nc):
            fmt += str(w) + "% "
        self.grid.layout.grid_template_columns = fmt

    def get(self):
        return self.grid


class Layer(object):
    def __init__(self, p):
        # get the temp file list
        self.temp_path = p["temp_path"]
        self.file_list = []
        for f in os.listdir(self.temp_path):
            fp = os.path.join(self.temp_path, f)
            if os.path.isfile(fp) and not f.startswith("."):
                self.file_list.append(f)
        self.file_list.sort()

        task = p["task"]["task"]
        task_list = Task.tasks
        # temp set of task 1 and 2 (raster with image temp files)
        if task == task_list[0] or task == task_list[1]:
            self.temp_path = p["temp_path"]
            self.bounds = p["task"]["options"]["Bounds"]
            self.layer = ill.ImageOverlay(
                url="",
                bounds=self.bounds
            )

            if p["task"]["options"]["Appearance"] == "static":
                self.image_static()
            else:
                self.image_dynamic()

    def image_static(self):
        """Single image or ghost view of multiple images
        :return:
        """
        plt.subplot()
        n = len(self.file_list)
        offset = 0.1 / n
        for i in range(n):
            f = self.file_list[i]
            fp = os.path.join(self.temp_path, f)
            img = mpimg.imread(fp)
            alpha = offset * (i + 1)
            if i == n - 1:
                alpha = 1
            plt.imshow(img, alpha=alpha)
            plt.axis("off")
        target_path = os.path.join(self.temp_path, "ghost.png")
        plt.savefig(target_path, transparent=True,
                    bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close()
        self.layer.url = self.read_image(target_path)
        os.remove(target_path)

    def image_dynamic(self):
        """Animation of images, initialize layer with the first image in temp
        :return:
        """
        first_img = os.path.join(self.temp_path, self.file_list[0])
        self.layer.url = self.read_image(first_img)

    @staticmethod
    def read_image(img_path):
        """
        read image file as base64 string
        :param img_path:
        :return:
        """
        with open(img_path, "rb") as img_file:
            result = "data:image/png;base64," + b64encode(
                img_file.read()).decode("ascii")
        return result

    def get(self):
        return self.layer


class Basemap(object):
    def __init__(self, center):
        self.center = center
        self.map = ill.Map(
            basemap=ill.basemaps.CartoDB.Positron,
            center=self.center,
            scroll_wheel_zoom=True,
            zoom=7,
            layout=widgets.Layout(
                min_height="200px",
            )
        )
        self.container = widgets.VBox([self.map])

    def add_layer(self, l):
        self.map.add_layer(l.get())

    def add_control(self, w):
        self.container.children += (w.get(), )

    def set_height(self, h):
        self.map.layout.height = h

    def get(self):
        return self.container


class Widgets(object):
    def __init__(self, p):
        # container of control widgets
        self.control = widgets.VBox(children=[])

        # check flags
        self.app = p["task"]["options"]["Appearance"]
        self.cmap = None
        if "Colormap" in p["task"]["options"]:
            self.cmap = p["task"]["options"]["Colormap"]

    def add_control(self, l):
        """Check the possible widget list and add to layer
        :param l:
        :return:
        """
        # add player if it is a dynamic view
        if self.cmap is not None:
            c = self.color_map(l)
            self.control.children += (c,)
        if self.app == "dynamic":
            p = self.player(l)
            self.control.children += (p,)

    def player(self, l):
        """Build player of animation
        :param l:
        :return:
        """
        timeline = [t.split(".")[0] for t in l.file_list]
        timeline = [parser.parse(t) for t in timeline]

        # initialize widgets
        player = widgets.Play(value=0, min=0, max=len(timeline) - 1,
                              interval=150)
        slider = widgets.SelectionSlider(value=timeline[0], options=timeline)
        speed = widgets.Dropdown(
            options=[("1", 250), ("2", 200), ("3", 150), ("4", 100), ("5", 50)],
            value=150,
            description="Speed:",
            layout=widgets.Layout(
                width="100px"
            ),
            style={
                "description_width": "45px"
            }
        )

        # handle events
        layer = l.get()
        temp_path = l.temp_path
        file_list = l.file_list

        def on_slider_change(change):
            i = timeline.index(change.new)
            player.value = i  # regarding change on player
            img = os.path.join(temp_path, file_list[i])
            layer.url = Layer.read_image(img)

        def on_player_change(change):
            t = timeline[change.new]
            slider.value = t  # regarding change on slider
            img = os.path.join(temp_path, file_list[change.new])
            layer.url = Layer.read_image(img)

        slider.observe(on_slider_change, names="value")
        player.observe(on_player_change, names="value")
        widgets.link((speed, "value"), (player, "interval"))

        result = widgets.HBox(
            children=[player, speed, slider],
            layout=widgets.Layout(
                width="100%",
                flex_flow="row wrap"
            )
        )
        return result

    def color_map(self, l):
        """Build color map legend
        :return:
        """
        # create legend image
        img = os.path.join(l.temp_path, "legend.png")
        cmap = self.cmap[0]
        (v_min, v_max) = self.cmap[1]
        norm = mpl.colors.Normalize(vmin=v_min, vmax=v_max)
        fig, ax = plt.subplots(figsize=(5, 0.2))
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                     cax=ax, orientation="horizontal")
        plt.savefig(img, bbox_inches="tight", pad_inches=0.02)
        plt.close()

        # build legend widget
        result = widgets.Image(
            value=open(img, "rb").read(),
            format="png",
            layout=widgets.Layout(height="25px", width="200px")
        )
        os.remove(img)
        return result

    def get(self):
        return self.control
