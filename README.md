# ![Microgrids.py](https://github.com/Microgrids-X/Microgrids-artwork/raw/main/svg/Microgrids-py.svg)

The Microgrids.py package allows simulating the energetic operation of an isolated microgrid,
returning economic and operation indicators.

Installation with `pip`:

```
pip install -U microgrids
```

## Documentation

See the [Microgrid_py_PV_BT_DG.ipynb](examples/Microgrid_py_PV_BT_DG.ipynb)
notebook example which walks through:
1. the main data structure to describe a Microgrid project
2. the main function to simulate it and display the results

You can have a live demo of this notebook right in your browser:
[Microgrid_py_PV_BT_DG.ipynb web demo](https://microgrids-x.github.io/Microgrids.web/lab?path=Microgrid_py_PV_BT_DG.ipynb)
(from [Microgrids.web](https://github.com/Microgrids-X/Microgrids.web/) repository).


## Acknowledgements

The development of Microgrids.jl (sibling package in Julia) was first led by
Evelise de Godoy Antunes. She was financed in part by
the Coordenação de Aperfeiçoamento de Pessoal de Nı́vel Superior - Brasil (CAPES) – Finance Code 001,
by Conselho Nacional de Desenvolvimento Cientı́fico e Tecnológico - Brasil (CNPq)
and by the grant “Accélérer le dimensionnement des systèmes énergétiques avec
la différentiation automatique” from [GdR SEEDS (CNRS, France)](https://seeds.cnrs.fr/).


## Other microgrids-related packages in Python

Found by searching for ["microgrid"](https://pypi.org/search/?q=microgrid) on PyPI or from personal knowledge:

- [PyEPLAN](https://pypi.org/project/pyeplan/): a free software toolbox for designing resilient mini-grids in developing countries. From Leeds, CUT, ICL.
- [pymgrid](https://github.com/Total-RD/pymgrid) (PYthon MicroGRID): a python library to generate and simulate a large number of microgrids.
- [OpenModelica Microgrid Gym](https://pypi.org/project/openmodelica-microgrid-gym/) (OMG):
  a software toolbox for the simulation and control optimization of microgrids
  based on energy conversion by power electronic converters.
    - “The main characteristics of the toolbox are the plug-and-play grid design and simulation in OpenModelica as well as the ready-to-go approach of intuitive reinforcement learning (RL) approaches through a Python interface.”
    - “The OMG toolbox is built upon the OpenAI Gym environment definition framework. Therefore, the toolbox is specifically designed for running reinforcement learning algorithms to train agents controlling power electronic converters in microgrids. Nevertheless, also arbritary classical control approaches can be combined and tested using the OMG interface.”
- [CVXMG](https://pypi.org/project/cvxmg/): Planning of Microgrids considering Demand Side Management Strategies using Disciplined Convex Deterministic and Stochastic Programming
