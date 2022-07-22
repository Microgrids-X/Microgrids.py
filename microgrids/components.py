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
    'DispatchableGenerator', 'Battery', 'Photovoltaic']


@dataclass
class Microgrid:
    """Microgrid system description"""
    project: 'Project'
    "microgrid project information"
    load: npt.ArrayLike
    "desired load (kW)"
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
    om_price_hours: float
    "operation & maintenance price ($/kW/h of operation)"
    lifetime_hours: float
    "generator operation lifetime (h of operation)"

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

    def lifetime(self, oper_hours : float) -> float:
        """effective lifetime (y), based on yearly operation hours `oper_hours` (h/y)
        """
        return self.lifetime_hours / oper_hours # h / (h/y) → y


@dataclass
class Battery:
    """Battery energy storage (including AC/DC converter)

    Battery dynamics is E(k+1) = E(k) − (P(k) + α|P(k)|).Δt
    """
    # Technical parameters
    energy_rated: float
    "rated energy capacity (kWh)"

    # economics
    investment_price: float
    "initial investiment price ($/kWh)"
    om_price: float
    "operation and maintenance price ($/kWh/y)"
    lifetime_calendar: float
    "calendar lifetime (y)"
    lifetime_cycles: float
    "maximum number of cycles over life (1)"

    # Technical parameters with default values
    charge_rate_max: float = 1.0
    "max charge power for 1 kWh (kW/kWh = h^-1)"
    discharge_rate_max: float = 1.0
    "max discharge power for 1 kWh (kW/kWh = h^-1)"
    loss_factor: float = 0.05
    "linear loss factor α (round-trip efficiency is about 1 − 2α) ∈ [0,1]"
    SoC_min: float = 0.0
    "minimum State of Charge ∈ [0,1]"
    SoC_ini: float = 0.0
    "initial State of Charge ∈ [0,1]"

    # Economics with default values
    replacement_price_ratio: float = 1.0
    "replacement price, as a fraction of initial investment price"
    salvage_price_ratio: float = 1.0
    "salvage price, as a fraction of initial investment price"

    def lifetime(self, cycles : float) -> float:
        """effective lifetime (y), based on yearly operation `cycles`
        """
        if cycles > 0.0:
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
    power_rated: float
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

    def production(self):
        "PV production time series"
        power_output = self.derating_factor * self.power_rated * self.irradiance
        return power_output