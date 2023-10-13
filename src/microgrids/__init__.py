"""Operational & economic simulation of Microgrid projects
"""
# Copyright (c) 2022, Evelise de G. Antunes, Nabil Sadou and Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.

#__all__ = ['components', 'economics', 'operation', 'plotting']

__version__ = '0.3.0'

from . import components
from . import operation
from . import economics
from . import plotting

from .components import *
from .operation import *
from .economics import *

# Top-level Microgrid simulation function.
def simulate(mg: Microgrid, recorder: TrajRecorder | None = None) -> tuple[
    operation.OperationStats, economics.MicrogridCosts]:
    """Simulate the technical and economic performance of the Microgrid `mg`.

    Operation time series are optionnaly recorded if `recorder` is a `TrajRecorder` instance.

    Returns:
    - Operational statistics from `sim_operation`
    - Microgrid project costs from `sim_economics`
    """
    oper_stats = sim_operation(mg, recorder)
    mg_costs = sim_economics(mg, oper_stats)
    return oper_stats, mg_costs

# add as Microgrid's method for convenience
setattr(Microgrid, 'simulate', simulate)