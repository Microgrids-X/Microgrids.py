# Draft tests for components

import microgrids as mgs
import numpy as np
from pytest import approx

def test_wind_capacity_factor():
    # Wind turbine parameters fitted to an EWT 900 kW DW52
    S_D52 = np.pi * (52/2)**2 # rotor swept area m²
    TSP_D52 = 900e3/S_D52 # W/m²
    v_out = 25.0 # cut-out speed m/s
    Cp_D52, α_D52 = 0.521, 3.1 # fitted from actual power curve

    wind_speed = np.array([0., 2., 3.,    5.,    7.,    10.,   15., 25., 25.1]) # m/s
    cf_exp =     np.array([0., 0., 0.005, 0.075, 0.227, 0.630, 0.997, 1.0, 0.])

    cf = mgs.WindPower.capacity_from_wind(wind_speed, TSP_D52, Cp_D52, v_out, α_D52)
    assert(cf == approx(cf_exp, abs=1e-3))