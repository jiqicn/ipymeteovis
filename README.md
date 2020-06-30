# Meteovis

A Jupyter-based tool for visualizing meteorological data

<!--#### Backgound-->

<!--There are two motivations of this project and the further development: first, to introduce high performance computation (HPC) to our data exploration tests, due to the increasing cost of memory and computation; and second, to explore a new way of rapid data exploration and implement a set of toolkits based on that. -->

<!--Depending on the problem scale and concrete requirements from users, HPC can play roles in different steps of meteorological data exploration, e.g. data preprocessing, rendering. Considering the implementation of Bart’s visualization as an example, both preparing and plotting the bird density data requires considerable usage of memory and computation, and we assume to have more and more tasks like this, due to the increasing volume of meteorological data we will have and the potential application of machine learning technologies.  -->

<!--Meanwhile, general challenges remain for the exploration or visualization of meteorological data. First, existing tools are typically designed for specific tasks (data source, visualization, analysis, etc.), and can be too heavy and inflexible for tasks of rapid exploration of meteorological data. Second, although script-based tools are preferred in many cases for customization, realize the visualization usually requires considerable knowledge of, e.g. programming in special language, setting parallel computing environment, display design. -->

<!--This project is a preliminary case study that tries to address the above challenges. The aim of this project is to implement a prototype framework that supports rapid exploration of meteorological data through a browser-based interface (sketch as Figure 1 below), and realize Bart’s visualization of bird density over basemap as a showcase. HPC is driven by the Lisa cluster and the HPC cloud virtual machine for data preparation and rendering. A prototype of a python-based visualization toolkit for meteorological data will be developed. This toolkit is inspired by vega-lite (https://vega.github.io/vega-lite/), which is a high-grammar of interactive graphics for ease the way of generating customized visualization with interaction. -->

<!--#### Objectives-->

<!--- To implement a prototype version of the visualization toolkit -->
<!--    - Script-based toolkit as a Python library -->
<!--    - Input: raster data in HDF5 format (only HDF5 supported in this project, will be extended), and a key-value style description of the output visualization -->
<!--    - Output: density map, both static and animated, projected on a base-map (only density map supported in this project, will be extended) -->
<!--    - Support of rendering in parallel -->
<!--- To develop a data preparation program -->
<!--    - Calculate bird density data based on the polar volume data -->
<!--    - Input: a set of pVol data in HDF5 format and related VP data for a pre-defined period of time and a number of radar stations -->
<!--    - Output: raster data of bird density, also in HDF5 format, with necessary metadata for plotting. -->
<!--    - Support of job submission to the Lisa cluster system -->

<!--#### Scope -->

<!--The end result of this project is to realize Bart’s visualization (static and animated visualization of bird density data for a number of radars in a period of time, <mark>say from 2016-10-03 14:00 to 2016-10-04 09:00 and for radar NL/DHL, NL/HRW, BE/JAB, and BE/WID</mark>) by using the above tool and program as a show showcase, and demonstrate it through a Jupyter Notebook built on a remote machine. The demonstration has the following content: -->

<!--- Both static and animated plots -->
<!--- Basic interaction with the plots (zooming, panning, etc.) -->

<!--The expected result: -->

<!--![Fig.1 Expected view on Jupyter Notebook.](Images/expectation.png)-->

#### Installation

Firstly, it’s recommended to install the latest version of conda and create environment for running your code. You can refer to https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html for installation of conda. Commands for basic use can also be found there.

Then, you may navigate to the directory of the cloned repository, and create an environment with the following command:

    conda create -n <yourenvname> --file spec-file.txt
    
An extra dependency is not supported by conda and need to be installed via pip using the following command:

    pip install ipydatetime
    
Creating environment and installing dependencies may take a considerable period of time. To enable widgets on Jupyter notebook 5.2 or earlier, you may also need to run the following command:

    jupyter nbextension enable --py --sys-prefix ipytree
    jupyter nbextension enable --py --sys-prefix ipydatetime
    jupyter nbextension enable --py --sys-prefix ipyleaflet

After that, you can start creating you own Jupyter notebook by running the following command:

    jupyter notebook