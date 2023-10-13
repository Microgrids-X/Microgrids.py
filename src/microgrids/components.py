""" Component classes for describing microgrid projects

also include `production` methods for non-dispatchable sources
"""
# Copyright (c) 2022, Evelise de G. Antunes, Nabil Sadou and Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

__all__ = ['Microgrid', 'Project',
    'DispatchableGenerator', 'Battery',
    'Photovoltaic', 'WindPower']


@dataclass
class Microgrid:
    """Microgrid system description"""
    project: 'Project'
    "microgrid project information"
    load: npt.ArrayLike
    "desired load time series (kW)"
    generator: 'DispatchableGenerator'
    "dispatchable generator"
    storage: 'Battery'
    "energy storage (e.g. battery)"
    nondispatchables: dict[str, 'NonDispatchableSource']
    "non-dispatchable sources (e.g. renewables like wind and solar)"


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
    # Main technical parameters
    power_rated: float
    "rated power (kW)"
    fuel_intercept: float
    "fuel consumption curve intercept (L/h/kW_max)"
    fuel_slope: float
    "fuel consumption curve slope (L/h/kW)"

    # Main economics parameters
    fuel_price: float
    "fuel price ($/L)"
    investment_price: float
    "initial investment price ($/kW)"
    om_price_hours: float
    "operation & maintenance price ($/kW/h of operation)"
    lifetime_hours: float
    "generator lifetime (h of operation)"

    # Secondary technical parameters, with default values
    load_ratio_min: float = 0.0
    "minimum load ratio ∈ [0,1]"

    # Secondary economics parameters, with default values
    replacement_price_ratio: float = 1.0
    "replacement price, relative to initial investment"
    salvage_price_ratio: float = 1.0
    "salvage price, relative to initial investment"
    fuel_unit: str = "L"
    "fuel quantity unit (used in fuel price and consumption curve parameters)"

    def lifetime(self, oper_hours : float) -> float:
        """effective lifetime (y), based on yearly operation hours `oper_hours` (h/y)
        """
        return self.lifetime_hours / oper_hours # h / (h/y) → y


@dataclass
class Battery:
    """Battery energy storage (including AC/DC converter)

    Battery dynamics is E(k+1) = E(k) − (P(k) + α|P(k)|).Δt
    where α is a linear loss factor (`loss_factor` parameter).
    It relates approximately to the roundtrip efficiency η as η = 1−2α.
    """
    # Main technical parameters
    energy_rated: float
    "rated energy capacity (kWh)"

    # Main economics parameters
    investment_price: float
    "initial investment price ($/kWh)"
    om_price: float
    "operation and maintenance price ($/kWh/y)"
    lifetime_calendar: float
    "calendar lifetime (y)"
    lifetime_cycles: float
    "maximum number of cycles over life"

    # Secondary technical parameters, with default values
    charge_rate: float = 1.0
    "max charge power for 1 kWh (kW/kWh = h^-1)"
    discharge_rate: float = 1.0
    "max discharge power for 1 kWh (kW/kWh = h^-1)"
    loss_factor: float = 0.05
    "linear loss factor α (round-trip efficiency is about 1 − 2α) ∈ [0,1]"
    SoC_min: float = 0.0
    "minimum State of Charge ∈ [0,1]"
    SoC_ini: float = 0.0
    "initial State of Charge ∈ [0,1]"

    # Secondary economics parameters, with default values
    replacement_price_ratio: float = 1.0
    "replacement price, relative to initial investment"
    salvage_price_ratio: float = 1.0
    "salvage price, relative to initial investment"

    def lifetime(self, cycles : float) -> float:
        """effective lifetime (y), based on yearly operation `cycles`
        """
        if self.energy_rated == 0.0:
            return self.lifetime_calendar
        elif cycles > 0.0:
            lifetime_cycling = self.lifetime_cycles / cycles # cycles / (cycles/y) → y
            return min(self.lifetime_calendar, lifetime_cycling)
        else:
            return self.lifetime_calendar


# Non-dispatchable sources (e.g. renewables like wind and solar)

class NonDispatchableSource(ABC):
    """Base class for non-dispatchable sources (e.g. renewables like wind and solar)"""

    @abstractmethod
    def production(self) -> np.ndarray:
        "production time series"
        pass

@dataclass
class Photovoltaic(NonDispatchableSource):
    """Solar photovoltaic generator (including AC/DC converter)"""
    # Main technical parameters
    power_rated: float
    "rated power (kW)"
    irradiance: npt.ArrayLike
    "global solar irradiance incident on the PV array time series (kW/m²)"

    # Main economics parameters
    investment_price: float
    "initial investment price ($/kW)"
    om_price: float
    "operation and maintenance price ($/kW)"
    lifetime: float
    "lifetime (y)"

    # Secondary technical parameters, with default values
    derating_factor: float = 0.9
    "derating factor (or performance ratio) ∈ [0,1]"

    # Secondary economics parameters, with default values
    replacement_price_ratio: float = 1.0
    "replacement price, relative to initial investment"
    salvage_price_ratio: float = 1.0
    "salvage price, relative to initial investment"

    def production(self):
        "PV production time series"
        power_output = self.derating_factor * self.power_rated * self.irradiance
        return power_output

@dataclass
class WindPower(NonDispatchableSource):
    """Wind power generator (simple model using a given capacity factor time series)"""
    # Main technical parameters
    power_rated: float
    "rated power (kW)"
    capacity_factor: npt.ArrayLike
    "capacity factor (normalized power) time series ∈ [0,1]"

    # Main economics parameters
    investment_price: float
    "initial investment price ($/kW)"
    om_price: float
    "operation and maintenance price ($/kW)"
    lifetime: float
    "lifetime (y)"

    # Secondary economics parameters, with default values
    replacement_price_ratio: float = 1.0
    "replacement price, relative to initial investment"
    salvage_price_ratio: float = 1.0
    "salvage price, relative to initial investment"

    def production(self):
        "Wind power production time series"
        power_output = self.power_rated * self.capacity_factor
        return power_output

    @staticmethod
    def capacity_from_wind(v: npt.ArrayLike,
                           TSP: float, Cp=0.50, v_out=25.0,
                           α=3.0) -> npt.ArrayLike:
        """Compute capacity factor (normalized power) of a wind turbine,
        using a generic parametrized power curve P(v),
        for a given a wind speed time series `v` (m/s).

        Model parameters are:
        Turbine Specific Power `TSP`, in W/m², typically 200 – 400.
        Maximum power coefficient `Cp` (used before saturation)
        should be smaller than Betz' limit of 16/27.
        Cut-out wind speed is `v_out` (m/s).

        A fixed Cp model is used, with a soft saturation when reaching maximum power.
        This soft saturation, based on LogSumExp, is tuned with `α`
        (default: 3.0, higher yields sharper transition).

        Air is assumed to have fixed density ρ=1.225 kg/m³.
        """
        ρ = 1.225 # kg/m³ at 15°C
        # Normalized power from the wind, without saturation:
        cf = 0.5*Cp*ρ/TSP * v**3
        # saturation using a smooth min based on LogSumExp
        cf = -np.log(np.exp(-α) + np.exp(-α*cf)) / α
        # saturate negative values (due to the smooth min)
        cf = np.where(cf>=0,    cf, 0)
        # Cut-out wind speed:
        cf = np.where(v<=v_out, cf, 0)
        return cf