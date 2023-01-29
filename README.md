# Model-Based Fault Identification
This Model-Based Fault Identification (MBFID) framework was designed by ARIA Systems Research as part of the AFRL STTR Research Contract. It utilizes **Bayesian Hypothesis Testing** by quantifying the uncertainty present in measurements observed by the system. The framework can identify known faults as well as detect _anomalous_ behavior (AKA unknown faults). 

Although it was initially designed to identify modeled satellite faults triggered during [Basilisk](https://hanspeterschaub.info/basilisk/) simulations the implementation is general enough to be used for any dynamical system one wishes to test. All that is required by the user is a well formatted simulation database as well as truth telemetry data. See [1-2] for more details on the inner workings of the framework.

## Requirements
The MBFID framework is built using **Python 3.9** with the following requirements:
- [Numpy](https://numpy.org/) version 1.23.5
- [Pandas](https://pandas.pydata.org/) version 1.5.2

You are welcome to install these libraries however you want. However, we provided some useful tools that will make this process very easy. 
**Note**: This framework **may** work with different versions. However, we have yet to test them and, thus, cannot claim to support them.

## Setup
### Installing Required Packages
You can install the [requirements](# Requirements) any way you'd like (e.g. `pip`). However, we have provided a simple way to manage this project using [Conda Environments](https://docs.conda.io/projects/conda/en/stable/). Conda is a language-agnostic virtual environment and package manager that replaces native `venv`. 
#### Installing Miniconda
If you have not done so already, install miniconda [here](https://docs.conda.io/en/latest/miniconda.html). Verify your installation succeeded by running 
```
conda --version
```
Once you have `conda` running on your machine, create a conda environment for this project by running the following. 
```
cd Model-Based-Fault-Identification/
conda env create -f environment.yml
```
This will create a virtual environment virtual environment with all the required dependencies installed. To activate the virtual environment, run 
`conda activate MBFID-Env`. Once you are done using it, enter `conda deactivate` to close the virtual environment. 
**Note**: You do not need to `create` the Conda enviroment every time. Only when when the `environment.yml` is updated.

### Running the Project
The MBFID tool requires two command line arguments to run properly. 
1. A path to a *directory* representing the simulation database for a particular example 
2. A path to *telemetry.csv* representing the truth telemetry data for a particular example
Instructions for providing these requirements can be found in the help module. 
```
python3 main.py --help
```

For fun, we included two test cases in the `tests/` directory. The tests can either be ran individually by calling `main.py` **or** run all at once by running
```
bash run_tests.sh
```

## References
[1] Andersson, S. B., Hristu-Varsakelis, D., & Lahijanian, M. (2008). Observers in language-based control.  
[2] Levy, B.C. (2008). Binary and Mary Hypothesis Testing. In: Principles of Signal Detection and Parameter Estimation. Springer, Boston, MA. https://doi.org/10.1007/978-0-387-76544-0_2
