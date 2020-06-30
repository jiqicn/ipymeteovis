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
    def __init__(self, *args, view="single", height=400, col=1):
        self.maps = []
        self.layers = []
        self.cont = None
        self.ctrl = None
        self.height = str(height) + "px"  # height of basemap
        self.col = col  # number of columns of content

        if len(args) == 1:
            self.unit_view(args[0])  # unit
        else:
            v_list = [View(i, height=height) for i in args]
            if view == "single":
                self.single_view(v_list)  # single
            elif view == "multiple":
                self.multiple_view(v_list)  # multiple
            else:
                print("[ERROR] View should be either 'single' or 'multiple'.")

    def unit_view(self, arg):
        if isinstance(arg, int):
            # init basemap
            t = Temp(arg)
            b = t.profile["task"]["options"]["Bounds"]
            center = [
                (b[0][0] + b[1][0]) * 0.5,
                (b[0][1] + b[1][1]) * 0.5,
            ]
            self.maps.append(self.Map(center, self.height))

            # init layer
            p = t.profile
            self.layers.append(self.Layer(p))

            # init content
            self.cont = self.Content(self.col)

            # init control
            self.ctrl = self.Control()

            # add layer to basemap
            self.maps[0].add_layer(self.layers[0])

            # add control to layer
            self.ctrl.add_control(self.layers[0])

            # add basemap to content
            self.cont.add_content(self.maps[0])
        elif isinstance(arg, View):
            # wrap the input view instance
            self.maps = arg.maps
            self.layers = arg.layers
            self.cont = arg.cont
            self.ctrl = arg.ctrl
            self.height = arg.height
            self.col = arg.col

    def single_view(self, v_list):
        # init maps
        centers = [v.maps[0].center for v in v_list]
        center = [
            sum([c[0] for c in centers]) / len(centers),
            sum([c[1] for c in centers]) / len(centers)
        ]
        self.maps.append((self.Map(center, self.height)))

        # init layers
        for v in v_list:
            self.layers = self.layers + v.layers

        # init content
        self.cont = self.Content(self.col)

        # init control
        self.ctrl = self.Control()

        # add layers to basemap
        for l in self.layers:
            self.maps[0].add_layer(l)

        # add map to content
        self.cont.add_content(self.maps[0])

        # add control to views
        self.ctrl.add_control(v_list)

    def multiple_view(self, v_list):
        # init maps
        for v in v_list:
            self.maps = self.maps + v.maps

        # init layers
        for v in v_list:
            self.layers = self.layers + v.layers

        # init content
        self.cont = self.Content(self.col)

        # init control
        self.ctrl = self.Control()

        # add maps to content
        for m in self.maps:
            self.cont.add_content(m)

        # add control to views
        self.ctrl.add_control(v_list)

    def show(self):
        result = widgets.VBox(
            children=[self.cont.get(), self.ctrl.get()]
        )
        display(result)

    class Map(object):
        """class definition of basemap

        One basemap contains one or more layers.
        """

        def __init__(self, center, height):
            self.center = center
            self.map = ill.Map(
                basemap=ill.basemaps.CartoDB.Positron,
                center=self.center,
                scroll_wheel_zoom=True,
                zoom=7,
                layout=widgets.Layout(height=height)
            )
            self.legend_list = []

        def get(self):
            return self.map

        def add_layer(self, l):
            layer, legend, profile = l.get()

            # add layer to map
            self.map.add_layer(layer)

            # add legend to map if necessary
            if "Colormap" in profile["task"]["options"]:
                t = profile["task"]["options"]["Colormap"]
                if t not in self.legend_list and legend is not None:
                    legend_ctrl = ill.WidgetControl(
                        widget=legend,
                        position="topright"
                    )
                    self.map.add_control(legend_ctrl)
                    self.legend_list.append(t)

    class Layer(object):
        """class definition of layer

        A layer corresponds to a temp set
        """

        def __init__(self, p):
            self.p = p
            self.temp_path = p["temp_path"]
            self.file_list = []
            for f in os.listdir(self.temp_path):
                fp = os.path.join(self.temp_path, f)
                if os.path.isfile(fp) and not f.startswith("."):
                    self.file_list.append(f)
            self.file_list.sort()
            self.layer = None
            self.legend = None

            # different branches by task
            task = p["task"]["task"]
            task_list = Task.tasks
            if task == task_list[0] or task == task_list[1]:
                app = p["task"]["options"]["Appearance"]
                if app == "static":
                    self.layer = self.raster_static()
                else:
                    self.layer = self.raster_dynamic()
                self.legend = self.color_map()

        def raster_static(self):
            """Single image or ghost view of multiple images
            :return:
            """
            temp_path = self.p["temp_path"]
            bounds = self.p["task"]["options"]["Bounds"]
            layer = ill.ImageOverlay(
                url="",
                bounds=bounds
            )

            plt.subplot()
            n = len(self.file_list)
            offset = 0.1 / n
            for i in range(n):
                f = self.file_list[i]
                fp = os.path.join(temp_path, f)
                img = mpimg.imread(fp)
                alpha = offset * (i + 1)
                if i == n - 1:
                    alpha = 1
                plt.imshow(img, alpha=alpha)
                plt.axis("off")
            target_path = os.path.join(temp_path, "ghost.png")
            plt.savefig(target_path, transparent=True,
                        bbox_inches="tight", pad_inches=0, dpi=300)
            plt.close()
            layer.url = self.read_image(target_path)
            os.remove(target_path)
            return layer

        def raster_dynamic(self):
            """Animation of images, initialize layer with the first image in temp
            :return:
            """
            temp_path = self.p["temp_path"]
            bounds = self.p["task"]["options"]["Bounds"]
            layer = ill.ImageOverlay(
                url="",
                bounds=bounds
            )

            first_img = os.path.join(temp_path, self.file_list[0])
            layer.url = self.read_image(first_img)

            return layer

        def color_map(self):
            temp_path = self.p["temp_path"]
            cmap = self.p["task"]["options"]["Colormap"]
            img = os.path.join(temp_path, "legend.png")
            (v_min, v_max) = cmap[1]
            norm = mpl.colors.Normalize(vmin=v_min, vmax=v_max)
            fig, ax = plt.subplots(figsize=(5, 0.2))
            fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap[0]),
                         cax=ax, orientation="horizontal")
            plt.savefig(img, bbox_inches="tight", pad_inches=0.02)
            plt.close()

            # build legend widget
            legend = widgets.Image(
                value=open(img, "rb").read(),
                format="png",
                layout=widgets.Layout(height="25px", width="250px")
            )
            os.remove(img)

            return legend

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
            return self.layer, self.legend, self.p

    class Content(object):
        """class definition of content

        One content contains one or more basemaps
        """

        def __init__(self, col):
            width = round(100.0 / col, 2)
            template = ""
            for i in range(col):
                template += str(width) + "% "
            self.grid = widgets.GridBox(
                children=[],
                layout=widgets.Layout(
                    grid_template_columns=template
                )
            )

        def add_content(self, m):
            self.grid.children += (m.get(),)

        def get(self):
            return self.grid

    class Control(object):
        """class definition of control

        Area that contains all the widgets for controlling the view.
        """

        def __init__(self):
            self.container = widgets.VBox(
                children=[]
            )
            self.widgets = {
                "player": None
            }

        def add_control(self, arg):
            # add player widget
            self.widgets["player"] = self.Player(arg)
            if self.widgets["player"].get() is not None:
                self.container.children += (self.widgets["player"].get(),)

        def get(self):
            return self.container

        class Player(object):
            """class definition of animation player widget
            """

            def __init__(self, arg):
                self.arg = arg
                self.timeline = None
                self.player = None
                self.slider = None
                self.speed = None

                # Build new player or merge existing players
                if isinstance(arg, View.Layer):
                    self.unit_player()
                elif isinstance(arg, list):
                    self.joint_player()

            def unit_player(self):
                layer, legend, profile = self.arg.get()
                temp_path = self.arg.temp_path
                file_list = self.arg.file_list
                if "Appearance" in profile["task"]["options"]:
                    app = profile["task"]["options"]["Appearance"]
                    if app == "static":
                        return

                # compute timeline
                timeline = [t.split(".")[0] for t in self.arg.file_list]
                timeline = [parser.parse(t) for t in timeline]
                self.timeline = timeline

                # init widgets
                self.player = widgets.Play(value=0, min=0,
                                           max=len(timeline) - 1,
                                           interval=150)
                self.slider = widgets.SelectionSlider(value=timeline[0],
                                                      options=timeline)
                self.speed = widgets.Dropdown(
                    options=[("1", 250), ("2", 200), ("3", 150), ("4", 100),
                             ("5", 50)],
                    value=150,
                    description="Speed:",
                    layout=widgets.Layout(
                        width="100px"
                    ),
                    style={
                        "description_width": "45px"
                    }
                )

                # slider change event
                def on_slider_change(change):
                    i = self.timeline.index(change.new)
                    self.player.value = i  # regarding change on player
                    img = os.path.join(temp_path, file_list[i])
                    layer.url = View.Layer.read_image(img)

                self.slider.observe(on_slider_change, names="value")

                # player change event
                def on_player_change(change):
                    t = self.timeline[change.new]
                    self.slider.value = t  # regarding change on slider
                    img = os.path.join(temp_path, file_list[change.new])
                    layer.url = View.Layer.read_image(img)

                self.player.observe(on_player_change, names="value")

                # speed change event
                widgets.link((self.speed, "value"), (self.player, "interval"))

            def joint_player(self):
                # compute timeline
                timeline = []
                for v in self.arg:
                    p = v.ctrl.widgets["player"]
                    if p.timeline is not None:
                        timeline = timeline + p.timeline
                    timeline = list(set(timeline))
                    timeline.sort()
                self.timeline = timeline

                # init widgets
                self.player = widgets.Play(value=0, min=0,
                                           max=len(timeline) - 1,
                                           interval=150)
                self.slider = widgets.SelectionSlider(value=timeline[0],
                                                      options=timeline)
                self.speed = widgets.Dropdown(
                    options=[("1", 250), ("2", 200), ("3", 150), ("4", 100),
                             ("5", 50)],
                    value=150,
                    description="Speed:",
                    layout=widgets.Layout(
                        width="100px"
                    ),
                    style={
                        "description_width": "45px"
                    }
                )

                def on_slider_change(change):
                    t = change.new
                    self.player.value = self.timeline.index(t)
                    for v in self.arg:
                        p = v.ctrl.widgets["player"]
                        if p is not None and t in p.slider.options:
                            p.slider.value = t
                self.slider.observe(on_slider_change, names="value")

                def on_player_change(change):
                    t = self.timeline[change.new]
                    self.slider.value = t
                    for v in self.arg:
                        p = v.ctrl.widgets["player"]
                        if p is not None and t in p.slider.options:
                            p.slider.value = t
                self.player.observe(on_player_change, names="value")

                widgets.link((self.speed, "value"), (self.player, "interval"))

            def get(self):
                if self.player is None:
                    return None

                result = widgets.HBox(
                    children=[self.player, self.speed, self.slider],
                    layout=widgets.Layout(
                        width="100%",
                        flex_flow="row wrap"
                    )
                )
                return result
