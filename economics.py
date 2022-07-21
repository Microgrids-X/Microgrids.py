#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Pierre Haessig, Evelise Antunes — 2022
""" Microgrid economics modeling (based on operation statistics)
"""

from dataclasses import dataclass

import numpy as np

from components import Project

@dataclass
class ComponentCosts:
    """Cost factors of a Microgrid component, expressed as Net Present Values over the Microgrid project lifetime"""
    total: float = 0.0
    "total cost (initial + replacement + O&M + fuel + salvage)"
    investment: float = 0.0
    "initial investment cost"
    replacement: float = 0.0
    "replacement cost"
    om: float = 0.0
    "operation & maintenance cost"
    fuel: float = 0.0
    "Fuel cost"
    salvage: float = 0.0
    "salvage cost (negative)"


def component_costs(mg_project: Project, quantity: float, lifetime: float,
                    investment_price: float, replacement_price: float,
                    salvage_price: float, om_price: float,
                    fuel_consumption: float = 0.0, fuel_price: float = 0.0
                   ) -> ComponentCosts:
    """Net Present Cost for a component over the lifecycle of the `mg_project`.

    Componenent is bought in given `quantity`, which multiplies
    the respective unit prices for investment, replacement, salvage and O&M.

    Component's `lifetime` sets its replacements schedule over `mg_project`
    lifetime.

    If `fuel_consumption` (per year) is non zero, it is priced at `fuel_price`.

    Returns the component cost factors.
    """
    # discount factor for each year of the project
    discount_factors = [1/((1 + mg_project.discount_rate)**i)
                        for i in range(1, mg_project.lifetime+1)]
    sum_discounts = sum(discount_factors)

    # number of replacements
    replacements_number = int(np.ceil(mg_project.lifetime/lifetime)) - 1
    # years that the replacements happen
    replacement_years = [i*lifetime for i in range(1, replacements_number+1)]
    # discount factors for the replacements years
    replacement_factors = [1/(1 + mg_project.discount_rate)**i for i in replacement_years]

    # component remaining life at the project end
    remaining_life = lifetime*(1+replacements_number) - mg_project.lifetime
    # proportional unitary salvage cost given remaining life
    salvage_price_effective = salvage_price * remaining_life / lifetime

    # investment cost
    investment_cost = investment_price * quantity
    # operation and maintenance cost
    om_cost = om_price * quantity * sum_discounts
    # replacement cost
    if replacements_number == 0:
        replacement_cost = 0.0
    else:
        replacement_cost = replacement_price * quantity * sum(replacement_factors)
    # salvage cost (<0)
    salvage_cost = -salvage_price_effective * quantity * discount_factors[mg_project.lifetime-1]
    # fuel cost
    fuel_cost = fuel_price * fuel_consumption * sum_discounts

    total_cost = investment_cost + replacement_cost + om_cost + fuel_cost + salvage_cost

    return ComponentCosts(total_cost, investment_cost, replacement_cost, om_cost, fuel_cost, salvage_cost)
