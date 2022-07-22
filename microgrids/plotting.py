"""Plotting functions for microgrid simulation data
"""
# Copyright (c) 2022, Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .components import Microgrid
from .operation import OperationStats, TrajRecorder

__all__ = ['plot_oper_traj', 'plot_energy_mix']

def plot_oper_traj(microgrid:Microgrid, oper_traj:TrajRecorder) -> Figure:
    """plot trajectories of operational microgrid variables"""
    td = np.arange(24*365)/24 # time in days

    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(5,6))

    c = dict(
        load='tab:blue',
        shed='tab:pink',
        gen='tab:red',
        renew='tab:orange',
        spill='tab:orange',
        sto_ch='tab:green',
        sto_dis='tab:green',
        sto_ener='tab:green',
    )

    def pos(x):
        """positive part"""
        return x if x > 0.0 else 0.0

    def neg(x):
        """negative part"""
        return -x if x < 0.0 else 0.0

    pos = np.vectorize(pos)
    neg = np.vectorize(neg)

    # Load, generator and battery discharge
    ax[0].plot(td, microgrid.load, label='load req',
               color=c['load'], lw=1)
    actual_load = microgrid.load - oper_traj.Pshed
    ax[0].plot(td, actual_load, label='load',
               color=c['load'], lw=5, alpha=0.5)
    ax[0].fill_between(td, actual_load, microgrid.load, #where=oper_traj.Pshed>0.0,
                    label='shed', lw=0, color=c['shed'], alpha=0.6)
    ax[0].plot(td, oper_traj.Pgen, label='gen',
               color=c['gen'])
    ax[0].plot(td, pos(oper_traj.Psto), label='sto dis',
               color=c['sto_dis'])

    ax[0].set(
        title = 'Load, generator and battery discharge',
        ylabel = 'kW'
    )

    # Renewable production and battery charging
    actual_renew = oper_traj.Prep - oper_traj.Pspill
    ax[1].plot(td, oper_traj.Prep, label='renew pot',
              lw=0.5, color=c['renew'])
    ax[1].plot(td, actual_renew, label='renew',
               color=c['renew'])
    ax[1].fill_between(td, actual_renew, oper_traj.Prep, #where=oper_traj.Pspill>0.0,
                    label='spill', lw=0, color=c['spill'], alpha=0.3)
    ax[1].plot(td, neg(oper_traj.Psto), label='sto char',
               color=c['sto_ch'])

    ax[1].set(
        title = 'Renewable production and battery charging',
        ylabel = 'kW'
    )

    # Energy storage state
    ax[2].plot(td, oper_traj.Esto[:-1], label='sto ener',
              color=c['sto_ener'])
    Esto_max = microgrid.storage.energy_rated
    Esto_min = microgrid.storage.SoC_min * microgrid.storage.energy_rated
    ax[2].axhline(Esto_min, label='min, max',
                  color='k', ls='--')
    ax[2].axhline(Esto_max,
                  color='k', ls='--')
    ax[2].set(
        title = 'Energy storage state',
        ylabel = 'kWh'
    )

    for axi in ax:
        axi.grid()
        axi.legend(loc='upper right', ncol=2)

    fig.tight_layout()

    return fig

def plot_energy_mix(microgrid:Microgrid, oper_stats:OperationStats, eu='MWh'):
    """plot the microgrid energy mix

    `eu` is the energy unit ('kWh', 'MWh', 'GWh', 'TWh')
    """
    fig, ax = plt.subplots(1,1, figsize=(5,2.5))

    # energy scaling: kWh → k/M/G/TWh
    if eu == 'kWh':
        es = 1.0
    elif eu == 'MWh':
        es = 1e-3
    elif eu == 'GWh':
        es = 1e-6
    elif eu == 'TWh':
        es = 1e-9
    else:
        raise ValueError(f"Energy unit `eu` should be 'kWh', 'MWh', 'GWh' or 'TWh', but got {eu} instead")

    data = np.array([
        oper_stats.served_energy + oper_stats.shed_energy,
        oper_stats.renew_energy,
        oper_stats.gen_energy,
        oper_stats.storage_loss_energy,
    ])*es

    ylabels = [
        'Load',
        'Renewables',
        'Generator',
        'Storage loss',
    ]

    y = np.arange(len(data))

    ax.barh(-1, oper_stats.renew_potential_energy*es, label='renew potential',
            color = 'tab:blue', alpha=0.3)
    ax.barh(-y, data,
            color = 'tab:blue')

    if oper_stats.shed_energy > 0.0:
        ax.barh(0, oper_stats.shed_energy*es, label='shedding',
                color = 'tab:red')

    ax.set(
        title = 'Microgrid energy mix (shedding: {:.3g})'.format(oper_stats.shed_rate),
        yticks = -y,
        yticklabels = ylabels,
        xlabel = f'{eu}/y'
    )
    ax.grid()
    ax.legend(loc='lower right')

    fig.tight_layout()
