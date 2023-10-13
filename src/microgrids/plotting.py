"""Plotting functions for microgrid simulation data
"""
# Copyright (c) 2022, Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.

import numpy as np
import numpy.typing as npt
from typing import Any, Union

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import FancyBboxPatch, Circle, Arrow


from .components import Microgrid
from .operation import OperationStats, TrajRecorder

AxesArrayOpt = Union[npt.NDArray[Any], None] # NDArray[Axes] is not acceptable
AxesOpt = Union[Axes, None]

__all__ = ['plot_ratings', 'plot_oper_traj', 'plot_energy_mix']


def _add_component(ax:Axes, xy_A, anchor:str, width:float, height:float,
                    label='', color='C0'):
    """Add box showing microgrid component to the Axes `ax`,
    at position `xy_A` corresponding to `anchor` side of the box.
    """
    # Compute left-bottom origin of Rectangle
    if anchor=='N':
        xy_rect = (xy_A[0]-width/2, xy_A[1]-height)
    elif anchor=='NE':
        xy_rect = (xy_A[0]-width, xy_A[1]-height)
    elif anchor=='E':
        xy_rect = (xy_A[0]-width, xy_A[1]-height/2)
    elif anchor=='SE':
        xy_rect = (xy_A[0]-width, xy_A[1])
    elif anchor=='S':
        xy_rect = (xy_A[0]-width/2, xy_A[1])
    elif anchor=='SW': # easiest case
        xy_rect = (xy_A[0], xy_A[1])
    elif anchor=='W':
        xy_rect = (xy_A[0], xy_A[1]-height/2)
    elif anchor=='NW':
        xy_rect = (xy_A[0], xy_A[1]-height)

    # C is center of rectangle
    xC = xy_rect[0]+width/2
    yC = xy_rect[1]+height/2
    # M is midpoint of link from origin to A
    xM = xy_A[0]/2
    yM = xy_A[1]/2

    # Rectangle which depicts the component, anchored at A
    rect = FancyBboxPatch(xy_rect, width, height,
                          facecolor=color, alpha=1,
                          lw=1, edgecolor='black',
                          boxstyle='Round, pad=0.1')
    # Link to the orgin
    ax.add_patch(Arrow(0, 0, xC, yC, width=0.5, color='k'))
    #if flow == 'load' or flow == 'both':
    # power flow arrow doesn't look right.
    #    ax.add_patch(Arrow(0, 0, xM+xy_A[0]/4, yM+xy_A[1]/4, color='k'))

    ax.add_patch(rect)
    ax.text(xC, yC, label,
        size='large', ha='center', va='center')
# end _add_component


def plot_ratings(microgrid:Microgrid, unit='MW',
                 xlim=(-3.,3.), ylim=(-2.,2.),
                 ax : AxesOpt = None,) -> Figure:
    """Box and lines diagram of the `microgrid`, annotated with the ratings

    Ratings are shown in `unit` ('kW', 'MW', 'GW', 'TW').
    """
    if ax is None:
        fig, ax = plt.subplots(1,1, figsize=(6,4))
        standalone = True
    else:
        fig = ax.get_figure()
        standalone = False

    # Power ratings scaling: kW → k/M/G/TW
    if unit == 'kW':
        scaling = 1.0
    elif unit == 'MW':
        scaling = 1e-3
    elif unit == 'GW':
        scaling = 1e-6
    elif unit == 'TW':
        scaling = 1e-9
    else:
        raise ValueError(f"Ratings `unit` should be 'kW', 'MW', 'GW' or 'TW', but got {unit} instead")

    # Size normalization constant:
    P0 = np.max(microgrid.load) # kW

    ax.set(
        title='Microgrid ratings',
        aspect='equal',
        xlim=xlim,
        ylim=ylim
    )
    ax.set_axis_off()

    ### Add components
    # Load
    _add_component(ax, (1,-0.5), 'NW', width=1, height=2/3,
              label='Load', color='#d4efff')

    # Generator
    Pgen = microgrid.generator.power_rated
    width = np.sqrt(Pgen/P0)
    height = width*2/3
    label = f'Generator\n{Pgen*scaling:.3g} {unit}'
    _add_component(ax, (1,0.5), 'SW', width, height,
                   label=label, color='#ffa3a0')

    # Storage
    Esto = microgrid.storage.energy_rated
    width = np.sqrt(Esto/P0)
    height = width*2/3
    label=f'Storage\n{Esto*scaling:.3g} {unit}h'
    _add_component(ax, (-1,-0.5), 'NE', width, height,
                   label, color='#acffc9')

    # Non dispatchables: sum of all rated powers
    if microgrid.nondispatchables:
        names = microgrid.nondispatchables.keys()
        name_joined = '\n+ '.join(names)
        Pnd_tot = sum(nd.power_rated for nd in microgrid.nondispatchables.values())
        width = np.sqrt(Pnd_tot/P0)
        height = width*2/3
        label=f'{name_joined}\n{Pnd_tot*scaling:.3g} {unit}'
        _add_component(ax, (-1,0.5), 'SE', width, height,
                    label, color='#ffe3a0')

    # Disc at the convergence of lines:
    ax.add_patch(Circle((0,0), radius=0.15, color='k'))

    if standalone:
        fig.tight_layout()

    return fig


def plot_oper_traj(microgrid:Microgrid, oper_traj:TrajRecorder,
                   ax : AxesArrayOpt = None) -> Figure:
    """plot trajectories of operational microgrid variables"""
    td = np.arange(24*365)/24 # time in days

    if ax is None:
        fig, ax = plt.subplots(3, 1, sharex=True, figsize=(6,6))
        standalone = True
    else:
        fig = ax[0].get_figure()
        standalone = False

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

    if standalone:
        fig.tight_layout()

    return fig

def plot_energy_mix(microgrid:Microgrid, oper_stats:OperationStats, unit='MWh',
                    ax : AxesOpt = None) -> Figure:
    """plot the microgrid energy mix

    `unit` is the energy unit ('kWh', 'MWh', 'GWh', 'TWh')
    """
    if ax is None:
        fig, ax = plt.subplots(1,1, figsize=(5,2.5))
        standalone = True
    else:
        fig = ax.get_figure()
        standalone = False

    # energy scaling: kWh → k/M/G/TWh
    if unit == 'kWh':
        scaling = 1.0
    elif unit == 'MWh':
        scaling = 1e-3
    elif unit == 'GWh':
        scaling = 1e-6
    elif unit == 'TWh':
        scaling = 1e-9
    else:
        raise ValueError(f"Energy `unit` should be 'kWh', 'MWh', 'GWh' or 'TWh', but got {unit} instead")

    data = np.array([
        oper_stats.served_energy + oper_stats.shed_energy,
        oper_stats.renew_energy,
        oper_stats.gen_energy,
        oper_stats.storage_loss_energy,
    ]) * scaling

    ylabels = [
        'Load',
        'Renewables',
        'Generator',
        'Storage loss',
    ]

    y = np.arange(len(data))

    ax.barh(-1, oper_stats.renew_potential_energy*scaling, label='renew potential',
            color = 'tab:blue', alpha=0.3)
    ax.barh(-y, data,
            color = 'tab:blue')

    if oper_stats.shed_energy > 0.0:
        ax.barh(0, oper_stats.shed_energy*scaling, label='shedding',
                color = 'tab:red')

    ax.set(
        title = 'Microgrid energy mix (shedding: {:.3g})'.format(oper_stats.shed_rate),
        yticks = -y,
        yticklabels = ylabels,
        xlabel = f'{unit}/y'
    )
    ax.grid()
    ax.legend(loc='lower right')

    if standalone:
        fig.tight_layout()

    return fig
