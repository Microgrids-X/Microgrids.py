"""Example of a simple Microgrid with PV generation, battery and a Diesel generator.

Uses real load data from Ouessant island and solar data from PVGIS.
"""
# Copyright (c) 2022, Evelise de G. Antunes, Nabil Sadou and Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.
# (Copyright for Ouessant data is described in the file SOURCES.md.)

from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

import microgrids as mgs


# Load time series data
print(__file__)
folder = Path(__file__).parent
datapath = folder / 'data' / 'Ouessant_data_2016.csv'
data = np.loadtxt(datapath,
                  delimiter=',', skiprows=2, usecols=(1,2))

# Split load and solar data:
Pload = data[:,0] # kW
Ppv1k =  data[:,1] / 1000; # convert to kW/kWp


## Create Microgrid project and its components

# Project
lifetime = 25 # yr
discount_rate = 0.05
timestep = 1 # h

project = mgs.Project(lifetime, discount_rate, timestep)

# Diesel generator
power_rated_gen = 1800.  # /2 to see some load shedding
fuel_intercept = 0.0 # fuel curve intercept (l/h/kW_max)
fuel_slope = 0.240 # fuel curve slope (l/h/kW)
fuel_price = 1. # fuel price ($/l)
investment_price_gen = 400. # initial investiment price ($/kW)
om_price_gen = 0.02 # operation & maintenance price ($/kW/h of operation)
lifetime_gen = 15000. # generator lifetime (h)

generator = mgs.DispatchableGenerator(power_rated_gen,
    fuel_intercept, fuel_slope, fuel_price,
    investment_price_gen, om_price_gen,
    lifetime_gen
)

# Battery energy storage
energy_rated_sto = 9000. # rated energy capacity (kWh)
investment_price_sto = 350. # initial investiment price ($/kWh)
om_price_sto = 10. # operation and maintenance price ($/kWh/y)
lifetime_sto = 15. # calendar lifetime (y)
lifetime_cycles = 3000 # maximum number of cycles over life (1)
# Parameters with default values
charge_rate_max = 1.0 # max charge power for 1 kWh (kW/kWh = h^-1)
discharge_rate_max = 1.0 # max discharge power for 1 kWh (kW/kWh = h^-1)
loss_factor_sto = 0.05 # linear loss factor α (round-trip efficiency is about 1 − 2α) ∈ [0,1]

battery = mgs.Battery(energy_rated_sto,
    investment_price_sto, om_price_sto,
    lifetime_sto, lifetime_cycles,
    charge_rate_max, discharge_rate_max,
    loss_factor_sto)

# Photovoltaic generation
power_rated_pv = 6000. # rated power (kW)
irradiance = Ppv1k # global solar irradiance incident on the PV array (kW/m²)
investment_price_pv = 1200. # initial investiment price ($/kW)
om_price_pv = 20.# operation and maintenance price ($/kW)
lifetime_pv = 25. # lifetime (y)
# Parameters with default values
derating_factor_pv = 1.0 # derating factor (or performance ratio) ∈ [0,1]"

photovoltaic = mgs.Photovoltaic(power_rated_pv, irradiance,
    investment_price_pv, om_price_pv,
    lifetime_pv, derating_factor_pv)

microgrid = mgs.Microgrid(project, Pload,
    generator, battery,
    {'Solar PV': photovoltaic}
)

# Display the microgrid
mgs.plotting.plot_ratings(microgrid, xlim=(-3.5,2.5), ylim=(-2.5,2.5))

oper_traj = mgs.TrajRecorder()

oper_stats = mgs.sim_operation(microgrid, oper_traj)

# timing of `sim_operation`:
# - 25.3 ms without trajectory recording.
# - 43.2 ms with recording

# mgs.plotting.plot_oper_traj(microgrid, oper_traj)
mgs.plotting.plot_energy_mix(microgrid, oper_stats, 'GWh')

mgc = mgs.sim_economics(microgrid, oper_stats)
print(f'Microgrid NPC: {mgc.npc/1e6:.3f} M$')

cmat, cmat_rows, cmat_cols = mgc.costs_table()
print(f'Cost matrix. columns: {cmat_cols}')
print(f'  rows: {cmat_rows}')
print(np.round(cmat/1e6, 3)) # in M$

def simulate(microgrid):
    oper_stats = mgs.sim_operation(microgrid)
    mgc = mgs.sim_economics(microgrid, oper_stats)
    return mgc, oper_stats

plt.show()
