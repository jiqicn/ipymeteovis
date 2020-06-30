"""Make, get and remove temp sets
"""

import os
import shutil

import ipywidgets as widgets
from IPython.display import display

from .task import Task, Control, TEMP_SET_PATH


def make(data_path):
    """Make temporary set
    :param data_path:
    :return:
    """
    g = Make_GUI(data_path)
    g.show()


def list():
    """Get list of temporary set
    :return:
    """
    g = List_GUI()
    g.show()


class Temp(object):
    """Class definition of a temporary set.

    This is for instantiating temporary sets for creating views.
    """

    def __init__(self, id):
        self.id = id
        self.is_chosen = False

        # get temp path
        t_list = self.get_temp_list()
        self.temp_path = t_list[id]

        # read profile information
        with open(self.temp_path + "/profile.txt", "r") as f:
            self.profile = eval(f.read())

    def get_profile(self):
        """Return the profile information of this temporary set.
        :return:
        """
        # description of temp set
        p_str = "<b>ID</b>: " + str(self.id) + "<br>"
        p_str += "<b>Name</b>: " + self.profile["task"]["name"] + "<br>"
        p_str += "<b>Task</b>: " + self.profile["task"]["task"] + "<br>"
        desc = self.profile["task"]["desc"]
        if len(desc) > 50:
            desc = desc[:50] + "..."
        p_str += "<b>Description</b>: " + desc + "<br>"
        p_str += "<b>Details</b>: <br>"
        for o in self.profile["task"]["options"]:
            p_str += "|-- <b>" + o + "</b>: " + \
                     str(self.profile["task"]["options"][o]) + "<br>"
        p_str += "<b>Example:</b>"
        p_str = "<p style='line-height: 1.3em'>" + p_str + "</p>"
        desc = widgets.HTML(
            value=p_str,
        )

        # example image
        img_path = self.temp_path + "/temp"
        for r, d, fs in os.walk(img_path):
            for f in fs:
                img_path = img_path + "/" + f
                break
            break
        img = widgets.Image(
            value=open(img_path, "rb").read(),
            width="80%",
        )

        # remove button of the temp set
        def remove_choose(change):
            self.is_chosen = change["new"]

        remove = widgets.ToggleButton(
            value=self.is_chosen,
            description="Choose",
            icon="check"
        )
        remove.observe(remove_choose, names="value")

        return widgets.VBox([desc, img, remove])

    def remove(self):
        """Remove this temporary set.
        :return:
        """
        shutil.rmtree(self.temp_path)

    @staticmethod
    def get_temp_list():
        """Get the path list of existing temp sets
        :return:
        """
        t_list = os.listdir(TEMP_SET_PATH)
        t_list = [TEMP_SET_PATH + "/" + d for d in t_list if
                  not d.startswith('.')]
        t_list = [d for d in t_list if os.path.isdir(d)]
        t_list.sort()  # sort increasingly
        return t_list


class Make_GUI(object):
    """GUI regarding the "make" method of temporary sets.
    """

    def __init__(self, data_path):
        self.data_path = data_path
        self.control = Control(data_path)
        self.config = {
            "name": "DEFAULT_NAME",
            "desc": "DEFAULT_DESC",
            "task": None,
            "options": None,
        }

        # Initialize the GUI
        title = widgets.HTML(
            value="<b style='font-size: medium'>"
                  "Make Temporary Set</b>"
                  "<p style='color: #D84141'>Please confirm before operating "
                  "that all the files in the above directory follows the "
                  "same schema.</p>"
        )
        name = widgets.Text(
            placeholder="Name of the temporary set...",
            description="Name"
        )
        desc = widgets.Textarea(
            placeholder="Description of the temporary set...",
            description="Description"
        )
        task = widgets.Dropdown(
            options=Task.tasks,
            description="Task",
            value=None
        )
        self.options = widgets.VBox()
        submit = widgets.Button(
            description="Submit Task",
            icon="check",
        )
        output = widgets.Output()
        self.container = widgets.VBox([
            title, name, desc, task, self.options, submit, output
        ])

        # Change event of task
        def task_change(change):
            """Reaction to task change

            Get the new task, send it back to the control.
            compute the option list based on the input dataset and the task.
            Update the option list based on the above computation.
            """
            t = change["new"]
            o_list = self.control.choose_task(t)
            self.update_options(o_list)

        task.observe(task_change, names="value")

        # Click event of submit
        def submit_click(b):
            output.clear_output()
            with output:
                self.control.submit(self.config)

        submit.on_click(submit_click)

        # Other events
        def config_change(change):
            id = change["owner"].description
            if id == "Name":
                self.config["name"] = change["new"]
            elif id == "Description":
                self.config["desc"] = change["new"]
            elif id == "Task":
                self.config["task"] = change["new"]

        name.observe(config_change, names="value")
        desc.observe(config_change, names="value")
        task.observe(config_change, names="value")

    def show(self):
        """Present the GUI.
        :return:
        """
        display(self.container)

    def update_options(self, o_list):
        """Update the option list due to different tasks.
        :param o_list:
        :return:
        """
        self.config["options"] = {}
        self.options.children = ()

        # React event
        def value_change(change):
            id = change["owner"].description
            for o in o_list:
                if id == o["description"]:
                    k = o["key"]
                    self.config["options"][k] = change["new"]
                    break

        # Realize options in the list
        if o_list is None:
            return
        for o in o_list:
            k = o["key"]
            self.config["options"][k] = None

            # Build option
            if o["type"] == "dropdown":
                w = widgets.Dropdown(
                    options=o["options"],
                    description=o["description"]
                )
            self.options.children += (w,)
            self.config["options"][k] = w.value
            w.observe(value_change, names="value")


class List_GUI(object):
    """GUI regarding the get method of temporary set
    """

    def __init__(self):
        self.t_list = []  # list of temp

        # add temp sets as widgets to the GUI
        title = widgets.HTML(
            value="<b style='font-size: medium'>List of Temporary Set</b>"
        )

        # container of temp sets
        self.temps = widgets.GridBox(
            layout=widgets.Layout(
                grid_template_columns='33.3% 33.3% 33.3%',
            )
        )

        # remove button
        def remove_click(b):
            self.remove_temps()

        remove = widgets.Button(
            description="Remove",
            icon="trash"
        )
        remove.on_click(remove_click)

        # container of the whole UI
        self.container = widgets.VBox([
            title, self.temps, remove
        ])

    def update_temps(self):
        """Update the temp list based on the existing temp sets.
        :return:
        """
        self.temps.children = []

        # initialize temp list
        self.t_list = Temp.get_temp_list()
        self.t_list = [Temp(id) for id in range(len(self.t_list))]

        for t in self.t_list:
            self.temps.children += (t.get_profile(),)

    def remove_temps(self):
        """Remove temps based on the choosing status
        :return:
        """
        for t in self.t_list:
            if t.is_chosen:
                t.remove()
        self.update_temps()

    def show(self):
        self.update_temps()
        display(self.container)
