import h5py
import numpy as np

from ipymeteovis.tools import Colors


class Task(object):
    """Entrance to class definitions for different data types

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
        self.min = None
        self.max = None

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
            scan_list = sorted(scan_list, key=lambda x: x[0], reverse=True)
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
                qty = f["dataset1"][k]["what"].attrs["quantity"].decode(
                    "utf-8")
                t = (qty, k)
                qty_list.append(t)
        o_list.append({
            "key": "qty",
            "type": "dropdown",
            "options": qty_list,
            "description": "Quantity"
        })

        return o_list

    def process(self, config):
        """
        Get all the attributes and transform coordinate system from
        spherical to geographical. Config of PolarVol2D should include
        information of scan and qty.
        :return:
        """
        # Read the data and all the necessary attributes
        scan = config["scan"]
        qty = config["qty"]
        with h5py.File(self.file_path, "r") as f:
            self.data = f[scan][qty]["data"][...]
            elangle = float(f[scan]["where"].attrs["elangle"])
            rscale = float(f[scan]["where"].attrs["rscale"])
            nbins = int(f[scan]["where"].attrs["nbins"])
            nrays = int(f[scan]["where"].attrs["nrays"])
            a1gate = int(f[scan]["where"].attrs["a1gate"])
            gain = float(f[scan][qty]["what"].attrs["gain"])
            offset = float(f[scan][qty]["what"].attrs["offset"])
            nodata = float(f[scan][qty]["what"].attrs["nodata"])
            undetect = float(f[scan][qty]["what"].attrs["undetect"])

        # Mask nodata and undetect value and compute unit values
        # Compute min and max value
        # correct rays order by a1gate
        self.data = np.ma.masked_values(self.data, undetect)
        self.data = np.ma.masked_values(self.data, nodata)
        self.data = self.data * gain + offset
        self.min = self.data.min()
        self.max = self.data.max()

    def create_temp(self):
        """
        Create temp file that is the raster image.
        :return:
        """
        pass

    @staticmethod
    def plot_static():
        pass


class ScanIntg2D:
    """Integration of information across elevation scans of radar

    Data are integrated and projected in a two-dimensional spatial image
    of fine-scale radar reflectivity. Data are stored in HDF5 format.
    """

    def __init__(self, file_path):
        self.file_path = file_path

    def get_options(self):
        pass

    def process(self):
        pass

    def create_temp(self):
        pass

    @staticmethod
    def plot_static():
        pass


# Local Test
if __name__ == '__main__':
    fp = "/Users/ep/Workspace/meteo_vis/sample_data/" \
         "ppi/BE/JAB/BEJAB_pvol_20161003T1425_06410.h5"
    config = {
        "scan": "dataset1",
        "qty": "data1"
    }
    e = Task(fp, "Radar polar volume (2D)")
    e.process(config)