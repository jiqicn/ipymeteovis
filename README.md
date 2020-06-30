# ipymeteovis

A Jupyter-based toolkit for visualizing meteorological and ecological data used at TCE UvA group.

## Installation

**1. Install anaconda**

It’s highly recommended to work with ipymeteovis in anaconda environments. To install the latest version of anaconda, refer to

https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html 

where you can also find tutoiral of using anaconda.

**2. Download ipymeteovis**

Clone the repository to your local machine:

    git clone https://gitlab.com/BerendWijers/meteo_vis.git
    
You may need your gitlab account and password for doing this. 

**3. Prepare anaconda environment**

Go to the folder you just cloned, create a new anaconda environment:

    conda create -n <yourenvname> --file spec-file.txt
    
Replace \<yourenvname\> with the name of your own environment. After finished, activate the environment you just created:

    conda activate <yourenvname>

You also need to enable *ipyleaflet* in your environment:

    jupyter nbextension enable --py --sys-prefix ipyleaflet
    
**4. Start working**
    
Now, you can run Jupyter and create your own notebook:

    jupyter notebook
