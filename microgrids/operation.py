""" Microgrid operation modeling
"""
# Copyright (c) 2022, Evelise de G. Antunes, Nabil Sadou and Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.

from dataclasses import dataclass

import numpy as np

from .components import Microgrid

__all__ = ['TrajRecorder', 'sim_operation']


@dataclass
class OperationStats:
    """Aggregated statistics over the simulated Microgrid operation

    (simulation duration is assumed to be 1 year)
    """
    # Load statistics
    served_energy: float = 0.0
    "energy actually served to the load (kWh/y)"
    shed_energy: float = 0.0
    "shed energy, that is not served to the load (kWh/y)"
    shed_max: float = 0.0
    "maximum load shedding power (kW)"
    shed_hours: float = 0.0
    "cumulated duration of load shedding (h/y)"
    shed_duration_max: float = 0.0
    "maximum consecutive duration of load shedding (h)"
    shed_rate: float = 0.0
    "ratio of shed energy to the desired load (∈ [0,1])"

    # Dispatchable generator statistics
    gen_energy: float = 0.0
    "energy supplied by the dispatchable generator (kWh/y)"
    gen_hours: float = 0.0
    "cumulated operating hours of the dispatchable generator (h/y)"
    gen_fuel: float = 0.0
    "Diesel consumption in one year (L)"

    # Energy storage (e.g. battery) statistics
    storage_cycles: float = 0.0
    "cycling of the energy storage (cycles/y)"
    storage_char_energy: float = 0.0
    "energy charged into the energy storage (kWh/y)"
    storage_dis_energy: float = 0.0
    "energy discharged out of the energy storage (kWh/y)"
    storage_loss_energy: float = 0.0
    "energy lossed in the energy storage (kWh/y)"

    # Non-dispatchable (typ. renewables) sources statistics
    spilled_energy: float = 0.0
    "spilled energy (typ. from excess of renewables) (kWh/y)"
    spilled_max: float = 0.0
    "maximum spilled power (typ. from excess of renewables) (kW)"
    spilled_rate: float = 0.0
    "ratio of spilled energy to the energy potentially supplied by renewables (∈ [0,1])"
    renew_potential_energy: float = 0.0
    "energy potentially supplied by renewables in the absence spillage (kWh/y)"
    renew_energy: float = 0.0
    "energy actually supplied by renewables when substracting spillage (kWh/y)"
    renew_rate: float = 0.0
    "ratio of energy actually supplied by renewables (net of storage loss) to the energy served to the load (∈ [0,1])"


class TrajRecorder:
    """Recorder for trajectories of operational variables"""
    def init(self, **kwargs: dict[str,int]):
        """initialize arrays to record values of prescribed length

        Example: rec.init(var1=10, var2=11)
        """
        for name,length in kwargs.items():
            vector = np.zeros(length)
            self.__setattr__(name, vector)

    def rec(self, k:int, **kwargs: dict[str,int]):
        """record values at index `k`.

        `k` should be in [0, `length`−1], for the given `length` provided in `init`.

        Example: rec.rec(5, var1=0.8)
        """
        for name,value in kwargs.items():
            vector = self.__getattribute__(name)
            vector[k] = value


def dispatch(Pnl_req, Psto_cmax, Psto_dmax, Pgen_max) -> tuple[float, float, float, float]:
    """Energy dispatch decision for a "load-following-style" strategy.

    This simple rule-based energy dispatch assumes the Microgrid has
    one energy storage and one dispatchable generator.

    The load is implicitely fed for non-dispatchable sources first, so that
    the dispatch decision is only concerned by the net load request `Pnl_req`
    (desired load - non dispatchable potential).

    This net load is prioritarily fed by the energy storage and (when empty)
    by the dispatchable generator.

    Storage power uses a *generator convention*: positive when discharging
    and negative when charging.

    Parameters
    ----------
    Pnl_req: float
        Requested net load (desired load - non dispatchable potential) (kW).
    Psto_cmax: float
        Maximum storage charge power (kW, < 0).
    Psto_dmax:
        Maximum storage discharge power (kW).
    Pgen_max: float
        Rated power of the dispatchable generator (kW).

    Returns
    -------
    Pgen: float
        Power supplied by the dispatchable generator (kW).
    Psto: float
        Power supplied by the energy storage (kW).
    Pspill: float
        Spilled power, typically realized by curtailing renewables (kW).
    Pshed: float
        Shed power from the load (kW).
    """
    Pspill = 0.0
    Pshed = 0.0
    # Pnl_req >= 0 - load excess - after evaluating the production (Pnl = Pload - VRE generation)
    if Pnl_req >= 0.0:
        # storage discharging --> Psto positive
        if Pnl_req >= Psto_dmax:    # max(storage)
            Psto = Psto_dmax      # max(storage)
            if Pnl_req - Psto >= Pgen_max:  # max(generator)
                Pgen  = Pgen_max
                Pshed = Pnl_req - Psto - Pgen
            else:
                Pgen = Pnl_req - Psto
        else:
            Pgen  = 0.0
            Psto = Pnl_req

    # Pnl_req < 0 - VRE excess
    else: # Pnl_req < 0.0
        Pgen  = 0.0
        # storage charging --> Psto negative
        if Pnl_req >= Psto_cmax:    # min(storage)
            Psto = Pnl_req
        else:
            Psto = Psto_cmax      # min(storage)
            Pspill  = Psto - Pnl_req
    # end if Pnl_req >= 0.0

    return Pgen, Psto, Pspill, Pshed


def sim_operation(mg:Microgrid, recorder=None) -> OperationStats:
    """Simulate the operation of Microgrid project `mg`.

    Time series are recorded if `recorder` is a `Recorder`.

    Returns operational statistics.
    """
    # Remark: assuming all non-dispatchable sources are renewable!
    renew_productions = [nd.production() for nd in mg.nondispatchables.values()]
    renew_potential = sum(renew_productions)

    # Desired net load
    Pnl_request = mg.load - renew_potential

    # Fixed parameters and short aliases
    K = len(mg.load)
    dt = mg.project.timestep
    Psto_pmax =  mg.storage.discharge_rate_max * mg.storage.energy_rated
    Psto_pmin = -mg.storage.charge_rate_max * mg.storage.energy_rated
    Esto_max = mg.storage.energy_rated
    Esto_min = mg.storage.SoC_min * mg.storage.energy_rated
    sto_loss = mg.storage.loss_factor


    # Initialization of loop variables
    # Initial storage state
    Esto_ini = mg.storage.SoC_ini * mg.storage.energy_rated
    Esto = Esto_ini
    # Operation statistics counters initialiazed at zero
    op_st = OperationStats()
    shed_duration = 0.0 # duration of current load shedding event (h)

    if recorder:
        recorder.init(Prep=K, Pgen=K, Psto=K, Esto=K+1, Pspill=K, Pshed=K)


    ### Operation simulation loop
    for k in range(K):

        ### Decide energy dispatch

        # Storage energy and power limits (TODO: move to dispatch)
        Psto_emin = - (Esto_max - Esto) / ((1 - sto_loss) * dt)
        Psto_emax = (Esto - Esto_min) / ((1 + sto_loss) * dt)
        Psto_dmax = min(Psto_emax, Psto_pmax)
        Psto_cmax = max(Psto_emin, Psto_pmin)

        Pgen, Psto, Pspill, Pshed = dispatch(
            Pnl_request[k],
            Psto_cmax, Psto_dmax,
            mg.generator.power_rated)

        if recorder:
            recorder.rec(k,
                Prep=renew_potential[k],
                Pgen=Pgen, Psto=Psto, Esto=Esto,
                Pspill=Pspill, Pshed=Pshed)

        # Storage dynamics
        Esto = Esto - (Psto + sto_loss*abs(Psto))*dt

        ### Aggregate operation statistics

        # Load statistics
        op_st.shed_energy += Pshed*dt
        op_st.shed_max = max(op_st.shed_max, Pshed)
        if Pshed > 0.0:
            op_st.shed_hours += dt
            shed_duration += dt
            op_st.shed_duration_max = max(op_st.shed_duration_max, shed_duration)
        else:
            # reset duration of current load shedding event
            shed_duration = 0.0

        # Dispatchable generator statistics
        if Pgen > 0.0: # Generator ON
            op_st.gen_energy += Pgen*dt
            op_st.gen_hours += dt
            fuel_rate = mg.generator.fuel_intercept * mg.generator.power_rated +\
                          mg.generator.fuel_slope * Pgen # (l/h)
            op_st.gen_fuel += fuel_rate*dt

        # Energy storage (e.g. battery) statistics
        if Psto > 0.0: # discharge
            op_st.storage_dis_energy += Psto*dt
        else:
            op_st.storage_char_energy -= Psto*dt

        # Non-dispatchable (typ. renewables) sources statistics
        op_st.spilled_energy += Pspill*dt
        op_st.spilled_max = max(op_st.spilled_max, Pspill)
    # end for each instant k

    if recorder:
        recorder.rec(K-1, Esto=Esto)# Esto at last instant

    # Some more aggregated operation statistics
    load_energy = np.sum(mg.load)*dt
    op_st.served_energy = load_energy - op_st.shed_energy
    op_st.shed_rate = op_st.shed_energy / load_energy \
        if load_energy != 0.0 else np.inf

    op_st.storage_loss_energy = op_st.storage_char_energy \
        - op_st.storage_dis_energy - (Esto - Esto_ini)
    storage_throughput = op_st.storage_char_energy + op_st.storage_dis_energy
    op_st.storage_cycles = storage_throughput / (2*mg.storage.energy_rated) \
        if mg.storage.energy_rated != 0.0 else np.inf

    op_st.renew_potential_energy = np.sum(renew_potential)
    op_st.renew_energy = op_st.renew_potential_energy - op_st.spilled_energy
    op_st.renew_rate = 1 - op_st.gen_energy/op_st.served_energy \
        if op_st.served_energy != 0.0 else np.inf
    op_st.spilled_rate = op_st.spilled_energy / op_st.renew_potential_energy \
        if op_st.renew_potential_energy != 0.0 else np.inf
    return op_st
