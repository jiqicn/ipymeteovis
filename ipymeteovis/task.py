"""Class definitions of various tasks and the central control

The control class is for communicating with the front-end GUI, and to
organize the task into parallel.
Different tasks are defined by different classes. The "task" class is a unique
entrance that leads to different task instance based on the input task.
Each task class defines a process and a create temp method as the two major
steps of the background computation. Content will be different.
"""

import os
import time
from functools import partial
import multiprocessing as mp
import copy

import h5py
import wradlib as wrl
import numpy as np
from dateutil import parser
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm

TEMP_SET_PATH = "./temp_sets"


class Control(object):
    """Central control of data processing before visualization.

    """

    def __init__(self, data_path):
        self.data_path = data_path
        self.tasks = []
        self.file_list = []

        # get file list
        for r, d, fs in os.walk(data_path):
            fs = [r + "/" + f for f in fs if not f.startswith('.')]
            self.file_list += fs

    def choose_task(self, task):
        """First hand-shake between the GUI and the task controller.

        By specifying the task and dataset, a list of option will be returned
        to the GUI for users to choose and generate the config.
        :param data_path:
        :param task:
        :return:
        """
        sample_file = self.file_list[0]
        t = Task(file_path=sample_file, task=task)
        o_list = t.get_options()
        return o_list

    def submit(self, config):
        """Second hand-shake between GUI and the task controller.

        Submit task and make selection as the result. Task will be separated
        by files and processed in parallel. A selection is generated as a
        result. Physically, a selection is a directory including a profile
        file and a sub-directory of temporal files.
        :param config:
        :return:
        """
        if config["task"] is None:
            print("[ERROR] Please choose your task")
            return

        # create temp set directory
        id = str(time.time_ns())
        t_dir = TEMP_SET_PATH + "/" + id
        temp_path = t_dir + "/temp"
        os.mkdir(t_dir)  # temp directory
        os.mkdir(temp_path)  # temp file directory

        # create task list
        print("[STEP] Initialize task......", end="")
        job = partial(
            Task,
            task=config["task"]
        )
        args = self.file_list
        self.tasks = self.parallel(job, args)
        print("Done!")

        # process tasks
        print("[STEP] Process task......", end="")
        job = partial(
            self.process,
            config=config
        )
        args = self.tasks
        self.tasks = self.parallel(job, args)
        print("Done!")

        # create temporary files
        print("[STEP] Create temp files......", end="")
        job = partial(
            self.create_temp,
            temp_path=temp_path
        )
        args = self.tasks
        self.parallel(job, args)
        print("Done!")

        # create profile
        t_profile = {
            "source": self.data_path,
            "temp_path": temp_path,
            "task": self.tasks[0].get_profile(config)
        }
        with open(t_dir + "/profile.txt", 'w') as f:
            print(t_profile, file=f)
        print("[STEP] Task completed!")

    @staticmethod
    def process(task, config):
        task.process(config=config)
        return task

    @staticmethod
    def create_temp(task, temp_path):
        task.create_temp(temp_path=temp_path)

    @staticmethod
    def parallel(job, args):
        """Map job on args in parallel
        :param job:
        :param args:
        :return:
        """
        with mp.Pool(processes=mp.cpu_count()) as pool:
            result = pool.map_async(job, args).get()
        return result


class Task(object):
    """Entrance to class definitions for different tasks

    Different tasks results in different class to handle
    Attributes:
        data_types: a list of supported data types, each leads to a
        subclass of Element
    """
    tasks = [
        "Radar polar volume (2D)",  # radar polar volume
        "Radar scan integration (2D)",  # radar scan integration
    ]

    def __new__(cls, file_path, task):
        if task == cls.tasks[0]:
            return PolarVol2D(file_path)
        elif task == cls.tasks[1]:
            return ScanIntg2D(file_path)


class PolarVol2D:
    """Radar scans as polar volumes

    Data are stored in HDF5 format based on the OPERA weather radar
    information model. Config should include the following information:
    scan, quantity (qty), elangle, nbins, nrarys, rscale, a1gate, gain,
    offset, nodate, undetect
    """

    def __init__(self, file_path):
        """

        :param file_path:
        """
        self.file_path = file_path
        self.data = None
        self.grid = None
        self.bounds = None
        self.v_min = None
        self.v_max = None
        self.dt = None

    def get_options(self):
        o_list = []

        # Scan
        scan_list = []
        with h5py.File(self.file_path, "r") as f:
            keys = [s for s in f.keys() if "dataset" in s]
            for i in range(len(keys)):
                k = keys[i]
                elangle = f[k]["where"].attrs["elangle"]
                t = ("Scan " + str(i) + " (Elev. = " + str(elangle) + ")", k)
                scan_list.append(t)
            # scan_list = sorted(scan_list, key=lambda x: x[0], reverse=True)
        o_list.append({
            "key": "scan",
            "type": "dropdown",
            "options": scan_list,
            "description": "Scan"
        })

        # Quantity
        qty_list = []
        with h5py.File(self.file_path, "r") as f:
            keys = [s for s in f["dataset1"].keys() if "data" in s]
            for i in range(len(keys)):
                k = keys[i]
                qty = f["dataset1"][k]["what"].attrs["quantity"].decode("utf-8")
                t = (qty, k)
                qty_list.append(t)
        o_list.append({
            "key": "qty",
            "type": "dropdown",
            "options": qty_list,
            "description": "Quantity"
        })

        # Appearance
        o_list.append({
            "key": "appearance",
            "type": "dropdown",
            "options": ["dynamic", "static"],
            "description": "Appearance"
        })

        return o_list

    def get_profile(self, config):
        """Return the profile string
        :return:
        """
        c = copy.deepcopy(config)
        scan = c["options"]["scan"]
        qty = c["options"]["qty"]
        app = c["options"]["appearance"]
        with h5py.File(self.file_path, "r") as f:
            scan = "Elev. = " + str(f[scan]["where"].attrs["elangle"])
            qty = f["dataset1"][qty]["what"].attrs["quantity"].decode("utf-8")
        c["options"] = {
            "Scan": scan,
            "Quantity": qty,
            "Appearance": app,
            "Colormap": ("jet", (self.v_min, self.v_max), "linear"),
            "Bounds": self.bounds
        }
        return c

    def process(self, config):
        """
        Get all the attributes and transform coordinate system from
        spherical to geographical. Config of PolarVol2D should include
        information of scan and qty.
        :return:
        """
        # Read the data and all the necessary attributes
        scan = config["options"]["scan"]
        qty = config["options"]["qty"]
        with h5py.File(self.file_path, "r") as f:
            self.data = f[scan][qty]["data"][...]

            # prepare attributes
            elangle = f[scan]["where"].attrs["elangle"]
            if isinstance(elangle, np.ndarray): elangle = elangle[0]
            elangle = float(elangle)

            rscale = f[scan]["where"].attrs["rscale"]
            if isinstance(rscale, np.ndarray): rscale = rscale[0]
            rscale = float(rscale)

            nbins = f[scan]["where"].attrs["nbins"]
            if isinstance(nbins, np.ndarray): nbins = nbins[0]
            nbins = int(nbins)

            nrays = f[scan]["where"].attrs["nrays"]
            if isinstance(nrays, np.ndarray): nrays = nrays[0]
            nrays = int(nrays)

            gain = f[scan][qty]["what"].attrs["gain"]
            if isinstance(gain, np.ndarray): gain = gain[0]
            gain = float(gain)

            offset = f[scan][qty]["what"].attrs["offset"]
            if isinstance(offset, np.ndarray): offset = offset[0]
            offset = float(offset)

            nodata = f[scan][qty]["what"].attrs["nodata"]
            if isinstance(nodata, np.ndarray): nodata = nodata[0]
            nodata = float(nodata)

            undetect = f[scan][qty]["what"].attrs["undetect"]
            if isinstance(undetect, np.ndarray): undetect = undetect[0]
            undetect = float(undetect)

            lon = f["where"].attrs["lon"]
            if isinstance(lon, np.ndarray): lon = lon[0]
            lon = float(lon)

            lat = f["where"].attrs["lat"]
            if isinstance(lat, np.ndarray): lat = lat[0]
            lat = float(lat)

            height = f["where"].attrs["height"]
            if isinstance(height, np.ndarray): height = height[0]
            height = float(height)

            date = f["what"].attrs["date"]
            if isinstance(date, np.ndarray): date = date[0]
            date = date.decode("utf-8")

            tp = f["what"].attrs["time"]
            if isinstance(tp, np.ndarray): tp = tp[0]
            tp = tp.decode("utf-8")

        # Datetime stamp
        self.dt = parser.parse(date + " " + tp)
        self.dt = self.dt.replace(second=0, microsecond=0)  # ignore second
        self.dt = self.dt.strftime("%Y%m%d %H%M")  # transfer back to str

        # Mask nodata and undetect value and compute unit values
        self.data = np.ma.masked_values(self.data, undetect)
        self.data = np.ma.masked_values(self.data, nodata)
        self.data = self.data * gain + offset

        # Compute v_min and v_max for choosing the boundaries of colormap
        self.v_min = self.data.min()
        self.v_max = self.data.max()
        if self.v_min >= 0 and self.v_max <= 1:
            self.v_min = 0.2
            self.v_max = 0.8
        elif self.v_min >= 0 and self.v_max <= 10:
            self.v_min = 1
            self.v_max = 8
        elif self.v_min >= -50 and self.v_max <= 100:
            self.v_min = -10
            self.v_max = 80
        else:
            self.v_min = 0
            self.v_max = 350

        # Compute the grid
        self.grid = np.empty((nrays, nbins, 3))  # azimuth, range, height
        self.grid = wrl.georef.sweep_centroids(nrays=nrays, rscale=rscale,
                                               nbins=nbins, elangle=elangle)
        self.grid = np.insert(self.grid, 0, 0, axis=1)
        self.grid = np.insert(self.grid, nrays, self.grid[0, :, :], axis=0)
        self.grid = wrl.georef.polar.spherical_to_proj(
            self.grid[..., 0], self.grid[..., 1], self.grid[..., 2],
            (lon, lat, height)  # site coordinates
        )
        np.set_printoptions(linewidth=np.inf)

        # Compute the bounds
        lons = self.grid[..., 0].flatten()
        lats = self.grid[..., 1].flatten()
        self.bounds = [
            [min(lats), min(lons)],
            [max(lats), max(lons)]
        ]

    def create_temp(self, temp_path):
        """
        Create temp file that is the raster image.
        :return:
        """
        temp_img = temp_path + "/" + self.dt + ".png"
        fig, ax = plt.subplots()
        x_range = [self.bounds[0][1], self.bounds[1][1]]
        y_range = [self.bounds[0][0], self.bounds[1][0]]
        plt.xlim(x_range)
        plt.ylim(y_range)
        cmap = cm.get_cmap("jet")
        # cmap.set_bad("grey")  # give color to bad values masked
        plt.pcolormesh(self.grid[..., 0], self.grid[..., 1], self.data,
                       cmap=cmap, vmin=self.v_min, vmax=self.v_max,
                       snap=True)
        ax.axis("off")
        plt.savefig(temp_img, transparent=True, bbox_inches="tight",
                    pad_inches=0, dpi=300)
        plt.close()


class ScanIntg2D:
    """Integration of information across elevation scans of radar

    Data are integrated and projected in a two-dimensional spatial image
    of fine-scale radar reflectivity. Data are stored in HDF5 format.
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.grid = None
        self.bounds = None
        self.v_min = 1
        self.v_max = 10000
        self.dt = None

    def get_options(self):
        o_list = []

        # Quantity
        qty_list = []
        with h5py.File(self.file_path, "r") as f:
            keys = [s for s in f["dataset1"].keys() if "data" in s]
            for i in range(len(keys)):
                k = keys[i]
                qty = f["dataset1"][k]["what"].attrs["quantity"]
                qty = qty[0].decode("utf-8")  # was array of b string
                t = (qty, k)
                qty_list.append(t)
        o_list.append({
            "key": "qty",
            "type": "dropdown",
            "options": qty_list,
            "description": "Quantity"
        })

        # Appearance
        o_list.append({
            "key": "appearance",
            "type": "dropdown",
            "options": ["dynamic", "static"],
            "description": "Appearance"
        })

        return o_list

    def get_profile(self, config):
        """Return the profile string
                :return:
                """
        c = copy.deepcopy(config)
        qty = c["options"]["qty"]
        app = c["options"]["appearance"]
        with h5py.File(self.file_path, "r") as f:
            qty = f["dataset1"][qty]["what"].attrs["quantity"]
            if isinstance(qty, np.ndarray): qty = qty[0]
            qty = qty.decode("utf-8")
        c["options"] = {
            "Quantity": qty,
            "Appearance": app,
            "Colormap": ("jet", (self.v_min, self.v_max), "log"),
            "Bounds": self.bounds
        }
        return c

    def process(self, config):
        qty = config["options"]["qty"]
        with h5py.File(self.file_path, "r") as f:
            self.data = f["dataset1"][qty]["data"][...]

            # prepare attributes
            lon_min = f["dataset1"]["how"].attrs["lon_min"]
            if isinstance(lon_min, np.ndarray): lon_min = lon_min[0]
            lon_min = float(lon_min)

            lon_max = f["dataset1"]["how"].attrs["lon_max"]
            if isinstance(lon_min, np.ndarray): lon_max = lon_max[0]
            lon_max = float(lon_max)

            lat_min = f["dataset1"]["how"].attrs["lat_min"]
            if isinstance(lat_min, np.ndarray): lat_min = lat_min[0]
            lat_min = float(lat_min)

            lat_max = f["dataset1"]["how"].attrs["lat_max"]
            if isinstance(lat_max, np.ndarray): lat_max = lat_max[0]
            lat_max = float(lat_max)

            nrows = f["dataset1"]["how"].attrs["nrows"]
            if isinstance(nrows, np.ndarray): nrows = nrows[0]
            nrows = int(nrows)

            ncols = f["dataset1"]["how"].attrs["ncols"]
            if isinstance(ncols, np.ndarray): ncols = ncols[0]
            ncols = int(ncols)

            tp = f["dataset1"]["how"].attrs["time"]
            if isinstance(tp, np.ndarray): tp = tp[0]
            tp = tp.decode("utf-8")

        # datatime stamp
        self.dt = parser.parse(tp)
        self.dt = self.dt.replace(second=0, microsecond=0)  # ignore second
        self.dt = self.dt.strftime("%Y%m%d %H%M")  # transfer back to str

        # Mask 0 values
        self.data = np.ma.masked_values(self.data, 0)

        # compute the grid
        self.bounds = [[lat_min, lon_min], [lat_max, lon_max]]
        lon_range = np.linspace(self.bounds[0][1], self.bounds[1][1], ncols + 1)
        lat_range = np.linspace(self.bounds[0][0], self.bounds[1][0], nrows + 1)
        lon_matrix = np.tile(lon_range, (ncols + 1, 1))
        lat_matrix = np.tile(lat_range, (nrows + 1, 1)).T
        self.grid = np.dstack((lon_matrix, lat_matrix))

    def create_temp(self, temp_path):
        """
        Create temp file that is the raster image.
        :return:
        """
        temp_img = temp_path + "/" + self.dt + ".png"
        fig, ax = plt.subplots()
        x_range = [self.bounds[0][1], self.bounds[1][1]]
        y_range = [self.bounds[0][0], self.bounds[1][0]]
        plt.xlim(x_range)
        plt.ylim(y_range)
        norm = colors.LogNorm(vmin=self.v_min, vmax=self.v_max)
        cmap = cm.get_cmap("jet")
        # cmap.set_bad("grey")  # give color to bad values masked
        plt.pcolormesh(self.grid[..., 0], self.grid[..., 1], self.data,
                       cmap=cmap, norm=norm,
                       snap=True)
        ax.axis("off")
        plt.savefig(temp_img, transparent=True, bbox_inches="tight",
                    pad_inches=0, dpi=300)
        plt.close()


# Local Test
if __name__ == '__main__':
    # Class test: Task
    fp = "/Users/ep/Workspace/meteo_vis/sample_data/" \
         "ppi/BE/JAB/BEJAB_pvol_20161003T1425_06410.h5"
    config = {
        "task": "Radar polar volume (2D)",
        "scan": "dataset9",
        "qty": "data1",
        "appearance": "static"
    }
    e = Task(fp, config)
    e.process(config)
    e.create_temp()

    # Class test: Control
    c = Control("/Users/ep/Workspace/meteo_vis/sample_data/ppi/NL/HRW")
    config = {
        'name': 'DEFAULT_NAME',
        'desc': 'DEFAULT_DESC',
        'task': 'Radar polar volume (2D)',
        'options': {
            'scan': 'dataset15',
            'qty': 'data1',
            'appearance': 'dynamic'
        }
    }
    c.submit(config)
