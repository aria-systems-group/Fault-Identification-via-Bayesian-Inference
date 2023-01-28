# Model-Based Fault Identification
This Model-Based Fault Identification (MBFID) framework was designed by ARIA Systems Research as part of the AFRL STTR Research Contract. It utilizes **Bayesian Hypothesis Testing** by quantifing the uncertainty present in measurements observed by the system. The framework is capable of identifing known faults as well as detecting _anomalous_ behaviour (AKA unknown faults). 

Although it was initially designed to identify modeled satellite faults triggered during [Basilisk](https://hanspeterschaub.info/basilisk/) simulations the implementation is general enough to be used for any dynamical system one wishes to test. All that is required by the user is a well formatted simulation database as well as truth telemetry data. See [1-2] for more details on the inner workings of the framework.

## Requirements
The MBFID framework is built using **Python 3.9** with the following requirements:
- [Numpy](https://numpy.org/) version 1.23.5
- [Pandas](https://pandas.pydata.org/) version 1.5.2

You are welcome to install these libraries however you want. However, we provded some useful tools that will make this process very easy. 
**Note**: This framework **may** work with different versions. However, we have yet to test them and, thus, cannot claim to support them.  

## Setup
**This is a to-do item**

## References
[1] Andersson, S. B., Hristu-Varsakelis, D., & Lahijanian, M. (2008). Observers in language-based control.  
[2] Levy, B.C. (2008). Binary and Mary Hypothesis Testing. In: Principles of Signal Detection and Parameter Estimation. Springer, Boston, MA. https://doi.org/10.1007/978-0-387-76544-0_2
