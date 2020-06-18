"""Make, get and remove temp sets
"""

import os

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


def get(*args):
    """Get list of temporary set
    :return:
    """
    g = Get_GUI()
    g.show()


def remove():
    """Remove existing temporary set
    :return:
    """
    pass


class Temp:
    """Class definition of a temporary set.

    This is for instantiating temporary sets for creating views.
    """

    def __init__(self, temp_path):
        self.temp_path = temp_path
        self.profile = None

        # get profile information
        with open(temp_path + "/profile.txt", "r") as f:
            self.profile = eval(f.read())
        print(self.profile)

    def get_profile(self):
        """Return the profile information of this temporary set.
        :return:
        """
        desc = "name: " + self.profile["task"]["name"]
        desc += ", task: " + self.profile["task"]["task"]
        for o in self.profile["task"]["options"]:
            desc += ", " + o + ": " + self.profile["task"]["options"][o]
        w = widgets.HTML(
            value=desc
        )
        return w

    def remove(self):
        """Remove this temporary set.
        :return:
        """
        pass


class Make_GUI:
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


class Get_GUI:
    """GUI regarding the get method of temporary set
    """

    def __init__(self):
        # get temp list
        t_list = os.listdir(TEMP_SET_PATH)
        t_list = [TEMP_SET_PATH + "/" + d for d in t_list if
                       not d.startswith('.')]
        t_list = [d for d in t_list if os.path.isdir(d)]
        t_list = [Temp(d) for d in t_list]

        # add temp sets as widgets to the GUI
        title = widgets.HTML(
            value="<b style='font-size: medium'>"
                  "Get Temporary Set</b>"
        )
        temps = widgets.VBox(
            layout=widgets.Layout(
                width="100%"
            )
        )
        for t in t_list:
            temps.children += (t.get_profile(), )

        self.container = widgets.VBox([
            title, temps
        ])

    def show(self):
        display(self.container)


class Remove_GUI:
    def __init__(self):
        pass
