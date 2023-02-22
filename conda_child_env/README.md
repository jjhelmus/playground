
conda child enviroments
-----------------------
**Note that this is a proof of concept and may not always work correctly :)**

Child enviroments are conda environments which act as if they have all the
packages of a parent enviroment while allowing packages not in the parent
environment to be installed using conda or pip. 

Packages from the parent environment cannot be removed or changed in the child environment.

Installing packages in the child environment does not change the parent environment.

The manner in which the child environment is derived from the parent environment requires 
minimal disk usage. This differs from `conda create --clone` which create a "full"
environment. Typically this will require more disk space, although if the package cache
is on the same filesystem and very few files need prefix replacement, hard linking can
reduce the disk requirements greatly.


Quickstart
----------

While in the `base` environment, or an environment with conda, run:

```
conda create -p ./parent python=3.10 pip
./conda-child.py --parent-prefix ./parent -p ./child
```

This will create a parent environment with Python 3.10 and pip as well as a child environment.
Packages, such as imagesize, can be installed into the child environment using conda using:

```
conda install -p ./child imagesize
```

Or with pip:

```
conda run -p ./child python -m pip install imagesize 
```

Installing packages in the child environment makes no changes to the parent environment.