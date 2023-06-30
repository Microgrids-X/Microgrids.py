# Draft tests for components

import microgrids as mgs

def test_wind_capacity_factor():
    v = [0, 1, 5, 10, 15, 20, 26]
    Pw = mgs.WindPower.capacity_from_wind(v, 200, 0.45, 25, 3)
    assert(Pw == [0.0, 0.0, 0.2, 0.8, 1.0, 1.0, 0.0])