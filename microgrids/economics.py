""" Microgrid economics modeling (based on operation statistics)
"""
# Copyright (c) 2022, Evelise de G. Antunes, Nabil Sadou and Pierre Haessig
# Distributed under the terms of the MIT License.
# The full license is in the file LICENSE.txt, distributed with this software.

from dataclasses import dataclass

import numpy as np

from .components import Microgrid, Project
from .operation import OperationStats

__all__ = ['sim_economics']


@dataclass
class CostFactors:
    """Cost factors of a component or a set of components"""
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

    @classmethod
    def from_prices(cls, mg_project: Project,
                        quantity: float, lifetime: float,
                        investment_price: float, replacement_price: float,
                        salvage_price: float, om_price: float,
                        fuel_consumption: float = 0.0, fuel_price: float = 0.0
                    ) -> 'CostFactors':
        """Cost factors for a single component given its `quantity` and price factors.

        Costs are computed as Net Present Values over the lifecycle of the
        Microgrid projet `mg_project` which the component belongs to.

        Component is bought in given `quantity`, which multiplies
        the respective unit prices for investment, replacement, salvage and O&M.
        Component's `lifetime` sets its replacements schedule over `mg_project`
        lifetime.
        If `fuel_consumption` (per year) is non zero, it is priced at `fuel_price`.

        Returns the cost factors of the component.
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

        return cls(total_cost, investment_cost, replacement_cost, om_cost, fuel_cost, salvage_cost)

    def __add__(self, other : 'CostFactors'):
        """sum of two `CostFactors` is the sum of their factors"""
        if type(other) == CostFactors:
            return CostFactors(
                self.total + other.total,
                self.investment + other.investment,
                self.replacement + other.replacement,
                self.om + other.om,
                self.fuel + other.fuel,
                self.salvage + other.salvage
            )
        else:
            raise NotImplementedError
# end CostFactors class


@dataclass
class MicrogridCosts:
    """Cost factors of each component of a Microgrid

    also includes `system` cost (all components) and two key economic data:
    `npc` and `lcoe`.
    """
    lcoe : float
    'levelised cost of electricity'
    npc : float
    'net present cost of the microgrid'
    system: CostFactors
    'costs of all components'
    generator: CostFactors
    'costs of generator'
    storage: CostFactors
    'costs of energy storage'
    nondispatchables: dict[str, CostFactors]
    'list costs of each non-dispatchable source'

    def costs_table(self):
        """Microgrid costs as a numpy 2D array"""
        # Rows
        cmat_rows = ['Generator', 'Storage'] + \
            [nd_name for nd_name in self.nondispatchables] + \
            ['All components']
        nr = len(cmat_rows)
        # Columns
        cmat_cols = ["Investment", "Replacement", "O&M", "Fuel", "Salvage", "Total by component"]
        nc = len(cmat_cols)
        cmat = np.zeros((nr,nc))

        def costs_to_vec(c: CostFactors):
            """cost factors to Numpy vector"""
            return np.array((
                c.investment,
                c.replacement,
                c.om,
                c.fuel,
                c.salvage,
                c.total
            ))

        # Fill in the cost table, one row for each component
        cmat[0,:] = costs_to_vec(self.generator)
        cmat[1,:] = costs_to_vec(self.storage)
        for i, ndc in enumerate(self.nondispatchables.values()):
            cmat[2+i,:] = costs_to_vec(ndc)
        cmat[nr-1,:] = costs_to_vec(self.system)

        return cmat, cmat_rows, cmat_cols
# end MicrogridCosts


def sim_economics(mg: Microgrid, oper_stats: OperationStats) -> MicrogridCosts:
    """evaluate economic performance of Microgrid `mg`,
    based on its operation statistics `oper_stats`.
    """
    # Dispatchable generator
    gen = mg.generator
    quantity = gen.power_rated
    lifetime = gen.lifetime(oper_stats.gen_hours)
    replacement_price = gen.investment_price * gen.replacement_price_ratio
    salvage_price = gen.investment_price * gen.salvage_price_ratio
    om_price = gen.om_price_hours * oper_stats.gen_hours # $/h × h/y → $/y

    gen_costs = CostFactors.from_prices(
        mg.project, quantity, lifetime,
        gen.investment_price, replacement_price, salvage_price, om_price,
        oper_stats.gen_fuel, gen.fuel_price
    )

    # Energy storage
    sto = mg.storage
    quantity = sto.energy_rated
    lifetime = sto.lifetime(oper_stats.storage_cycles)
    replacement_price = sto.investment_price * sto.replacement_price_ratio
    salvage_price = sto.investment_price * sto.salvage_price_ratio

    sto_costs = CostFactors.from_prices(
        mg.project, quantity, lifetime,
        sto.investment_price, replacement_price,
        salvage_price, sto.om_price
    )

    # Non-dispatchable sources (e.g. renewables like wind and solar)
    nd_costs: dict[str, CostFactors] = {}
    for name, nd in mg.nondispatchables.items():
        quantity = nd.power_rated
        replacement_price = nd.investment_price * nd.replacement_price_ratio
        salvage_price = nd.investment_price * nd.salvage_price_ratio

        nd_costs[name] = CostFactors.from_prices(
            mg.project, quantity, nd.lifetime,
            nd.investment_price, replacement_price,
            salvage_price, nd.om_price,
        )

    # Capital recovery factor (CRF)
    discount_factors = [1/((1 + mg.project.discount_rate)**i)
                        for i in range(1, mg.project.lifetime+1)]
    crf = 1/sum(discount_factors)
    # Cost of all components and NPC of the project
    system_costs = gen_costs + sto_costs + sum(nd_costs.values(), start=CostFactors())
    npc = system_costs.total
    # levelized cost of energy
    annualized_cost = npc*crf # $/y
    lcoe = annualized_cost / oper_stats.served_energy # ($/y) / (kWh/y) → $/kWh

    mg_costs = MicrogridCosts(lcoe, npc,
        system_costs, gen_costs, sto_costs, nd_costs
    )

    return mg_costs