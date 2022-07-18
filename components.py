#!/usr/bin/python3
# -*- coding: utf-8 -*-
""" Component classes for Microgrid projects

Pierre Haessig, Evelise Antunes — 2022
"""

from dataclasses import dataclass
import numpy.typing as npt


@dataclass
class Project:
    """Microgrid project information
    
    - lifetime (y)
    - discount rate ∈ [0,1]
    - time step (h)
    - currency
    """
    lifetime: int = 25
    "project lifetime (y)"
    discount_rate: float = 0.05
    "discount rate ∈ [0,1]"
    timestep: float = 1.0
    "time step (h)"
    currency: str = "$"
    "currency used in price parameters and computed costs"


@dataclass
class DispatchableGenerator:
    """Dispatchable power source (e.g. Diesel generator, Gas turbine, Fuel cell)"""
    # Technical parameters
    power_rated: float
    "rated power (kW)"
    fuel_intercept: float
    "fuel curve intercept (fu/h/kW_max)"
    fuel_slope: float
    "fuel curve slope (fu/h/kW)"

    # Economics parameters
    fuel_price: float 
    "fuel price ($/fu)"
    investment_price: float
    "initial investiment price ($/kW)"
    om_price: float
    "operation & Maintenance price ($/kW/h of operation)"
    lifetime: float
    "generator lifetime (h)"

    # Technical parameters with default values
    load_ratio_min: float = 0.0
    "minimum load ratio ∈ [0,1]"

    # Economics with default values
    replacement_price_ratio: float = 1.0
    "replacement price, as a fraction of initial investment price"
    salvage_price_ratio: float = 1.0
    "salvage price, as a fraction of initial investment price"
    fuel_unit: str = "l"
    "fuel counting unit (i.e. 'fu' used in price and fuel curve parameters)"


@dataclass
class Battery:
    """Battery energy storage (including AC/DC converter)"""
    # Technical parameters
    energy_rated: float
    "rated energy capacity (kWh)"

    # economics
    investment_price: float
    "initial investiment price ($/kWh)"
    om_price: float
    "operation and maintenance price ($/kWh/y)"
    lifetime: float
    "calendar lifetime (y)"
    lifetime_cycles: float
    "Maximum number of cycles over life (1)"

    # Technical parameters with default values
    charge_rate_max: float = 1.0
    "max charge power for 1 kWh (kW/kWh = h^-1)"
    discharge_rate_max: float = 1.0
    "max discharge power for 1 kWh (kW/kWh = h^-1)"
    efficiency: float = 0.9487
    "Charge/discharge efficiency ∈ [0,1]. Remark: round-trip efficiency is efficiency²"
    SoC_min: float = 0.0
    "Minimum State of Charge ∈ [0,1]"
    energy_initial: float = 0.0
    "Initial energy (kWh)"

    # Economics with default values
    replacement_price_ratio: float = 1.0
    "replacement price, as a fraction of initial investment price"
    salvage_price_ratio: float = 1.0
    "salvage price, as a fraction of initial investment price"


@dataclass
class Photovoltaic:
    """Solar photovoltaic generator (including AC/DC converter)"""
    power_rated: float   # decision variable
    "rated power (kW)"
    irradiance: npt.ArrayLike
    "global solar irradiance incident on the PV array (kW/m²)"

    # Economics
    investment_price: float
    "initial investiment price ($/kW)"
    om_price: float
    "operation and maintenance price ($/kW)"
    lifetime: float
    "lifetime (y)"

    # Technical parameters with default values
    derating_factor: float = 0.9
    "derating factor (or performance ratio) ∈ [0,1]"

    # Economics with default values
    replacement_price_ratio: float = 1.0
    "replacement price, as a fraction of initial investment price"
    salvage_price_ratio: float = 1.0
    "salvage price, as a fraction of initial investment price"