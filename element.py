import h5py

class Element(object):
    """Entrance to class definitions for different data types

    With different data types as input, the output is an instance of one of the following class:
        - RadarPolarVolume
        - RadarScanIntegration

    Attributes:
        data_types: a list of supported data types, each leads to a subclass of Element
    """
    data_types = [
        "pvol",  # radar polar volume
        "esi",  # radar scan integration
    ]

    def __new__(cls, file_path, data_type):
        if data_type == cls.data_types[0]:
            return RadarPolarVolume(file_path)
        elif data_type == cls.data_types[1]:
            return RadarScanIntegration(file_path)


class RadarPolarVolume:
    """Radar scans as polar volumes

    Data are stored in HDF5 format based on the OPERA weather radar information model.
    """

    def __init__(self, file_path):
        self.file_path = file_path

        f = h5py.File(self.file_path, "r")
        print(f.keys())
        print(f["dataset1"].keys())
        print(f["dataset1"]["data1"].keys())



class RadarScanIntegration:
    """Integration of information across elevation scans of radar

    Data are integrated and projected in a two-dimensional spatial image of fine-scale radar reflectivity.
    Data are stored in HDF5 format.
    """

    def __init__(self, file_path):
        self.file_path = file_path
        print("ESI")


# Local Test
if __name__ == '__main__':
    fp = "/Users/ep/Workspace/meteo_vis/sample_data/ppi/BE/JAB/BEJAB_pvol_20161003T1425_06410.h5"
    e = Element(fp, "pvol")