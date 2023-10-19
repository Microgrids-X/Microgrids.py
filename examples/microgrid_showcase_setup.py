""" Setup code for the Microgrid showcase notebook

"""
# Pierre Haessig — July 2022

from functools import lru_cache

import numpy as np
import scipy.optimize as opt
from matplotlib import pyplot as plt

from ipywidgets import interactive, fixed

import microgrids as mgs

from Microgrid_Wind_Solar_data import *

project = mgs.Project(lifetime, discount_rate, timestep)

def interactive_mg(power_rated_gen, energy_rated_sto, power_rated_pv, power_rated_wind):
    """Create `Microgrid` project description with generator, battery,
    and renewables (solar and wind) with given ratings"""
    generator = mgs.DispatchableGenerator(power_rated_gen,
        fuel_intercept, fuel_slope, fuel_price,
        investment_price_gen, om_price_gen,
        lifetime_gen
    )

    battery = mgs.Battery(energy_rated_sto,
        investment_price_sto, om_price_sto,
        lifetime_sto, lifetime_cycles,
        charge_rate, discharge_rate,
        loss_factor_sto)

    photovoltaic = mgs.Photovoltaic(power_rated_pv, irradiance,
        investment_price_pv, om_price_pv,
        lifetime_pv, derating_factor_pv)

    windgen = mgs.WindPower(power_rated_wind, cf_wind,
        investment_price_wind, om_price_wind,
        lifetime_wind)

    microgrid = mgs.Microgrid(project, Pload,
        generator, battery, {
        'Solar PV': photovoltaic,
        'Wind': windgen
        }
    )
    return microgrid


@lru_cache(maxsize=1000)
def simulate_microgrid(power_rated_gen, energy_rated_sto, power_rated_pv, power_rated_wind):
    """Microgrid performance simulator, with calculation caching"""
    microgrid = interactive_mg(power_rated_gen, energy_rated_sto, power_rated_pv, power_rated_wind)
    # Launch simulation:
    oper_stats, mg_costs = microgrid.simulate()
    return oper_stats, mg_costs


def interactive_energy_mix(Solar=0., Wind=0., Battery=0.):
    """display energy mix with given ratings"""
    # Translate variable names:
    # power_rated_gen # taken as global variable
    energy_rated_sto = Battery # kWh
    power_rated_pv = Solar # kW
    power_rated_wind = Wind # kW

    # Create Microgrid project description
    microgrid = interactive_mg(power_rated_gen, energy_rated_sto, power_rated_pv, power_rated_wind)
    # Simulate (with cache)
    oper_stats, mg_costs = simulate_microgrid(power_rated_gen, energy_rated_sto, power_rated_pv, power_rated_wind)
    # Show some performance stats:
    print(f'Load shedding: {oper_stats.shed_rate:.1%}')
    print(f'Renewable: {oper_stats.renew_rate:.1%}')
    print(f'(Spilled renewable: {oper_stats.spilled_rate:.1%})')
    print(f'Levelized Cost of Electricity: {mg_costs.lcoe:.3f} $/kWh')

    # Display energy mix
    fig, (ax1, ax2) = plt.subplots(2,1, num=1, figsize=(6,6),
                                  gridspec_kw=dict(height_ratios=(2,1)))
    mgs.plotting.plot_ratings(microgrid, xlim=(-3.5,2.5), ylim=(-2.5,2.5), ax=ax1)
    mgs.plotting.plot_energy_mix(microgrid, oper_stats, ax=ax2)
    fig.tight_layout()
    plt.show()

### For sizing optimization

def obj_multi(x):
    "Multi-objective criterion for microgrid performance: lcoe, shedding rate"
    # Split decision variables (converted MW → kW):
    power_rated_gen = x[0]*1000
    energy_rated_sto = x[1]*1000
    power_rated_pv = x[2]*1000
    power_rated_wind = x[3]*1000
    stats, costs = simulate_microgrid(power_rated_gen, energy_rated_sto, power_rated_pv, power_rated_wind)
    # Extract KPIs of interest
    lcoe = costs.lcoe # $/kWh
    shed_rate = stats.shed_rate # in [0,1]
    return lcoe, shed_rate


def obj(x, shed_max, w_shed_max=1e5):
    """Mono-objective criterion: LCOE + penalty if shedding rate > `shed_max`

    load shedding penalty threshold `shed_max` should be in [0,1[
    """
    lcoe, shed_rate = obj_multi(x)
    over_shed = shed_rate - shed_max
    if over_shed > 0.0:
        penalty = w_shed_max*over_shed
    else:
        penalty = 0.0
    return lcoe + penalty

Pload_max = np.max(Pload)
xmin = np.array([0., 0., 1e-3, 0.]) # 1e-3 instead of 0.0, because LCOE is NaN if ther is exactly zero generation
xmax = np.array([1.2, 10.0, 10.0, 5.0]) * (Pload_max/1000)

def optim_mg(shed_max, algo='DIRECT', maxeval=300, xtol_rel=1e-4, srand=1):
    """Optimize sizing of microgrid based on the `obj` function

    Parameters:
    - `x0`: initial sizing (for the algorithms which need them)
    - `shed_max`: load shedding penalty threshold (same as in `obj`)
    - `algo` could be one of 'DIRECT'...
    - `maxeval`: maximum allowed number of calls to the objective function,
      that is to the microgrid simulation
    - `xtol_rel`: termination condition based on relative change of sizing, see NLopt doc.
    - `srand`: random number generation seed (for algorithms which use some stochastic search)

    Problem bounds are taken as the global variables `xmin`, `xmax`,
    but could be added to the parameters as well.
    """
    x0 = np.array([1.0, 3.0, 3.0, 2.0]) * (Pload_max/1000)
    bounds = opt.Bounds(xmin, xmax)
    if algo=='DIRECT':
        res = opt.direct(obj, bounds, args=(shed_max,), maxfun=maxeval)
    else:
        raise ValueError(f'Unsupported optimization algorithm {algo}')

    xopt = res.x
    return xopt, res, res.nfev

def print_xopt(x):
    # Split decision variables (converted MW → kW):
    power_rated_gen = x[0]*1000
    energy_rated_sto = x[1]*1000
    power_rated_pv = x[2]*1000
    power_rated_wind = x[3]*1000
    print(f'- Generator power:  {power_rated_gen:.0f} kW')
    print(f'- Storage capacity: {energy_rated_sto:.0f} kWh')
    print(f'- Solar power:      {power_rated_pv:.0f} kW')
    print(f'- Wind power:       {power_rated_wind:.0f} kW')

print('Showcase setup complete.')
