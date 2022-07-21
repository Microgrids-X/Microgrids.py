# Sources for Ouessant load, PV, wind, temperature data

Ouessant data 2016 (trimmed at 365 days), by Pierre Haessig, April 2021

## Load data

Load data from EDF https://opendata-iles-ponant.edf.fr/,
collected and cleaned by Benjamin Bonvalet & Mohamed Chtiba,
in 2nd year Supélec student project 2018-2019.

Unit: kW

File `Ouessant_load_2016_filled_365j.csv` created by P. Haessig for HOMER ETS demo, 2019
in `~/Travail/46 Séminaires/Efficient Tools Seminar/ETS HOMER/Conso Ouessant`

## PV, wind, temperature data

PV (W/kWp, 40° slope, 0° azimuth), Wind speed (m/s at 10 m)
and temperature (°C at 2 m) from PVGIS (c) European Communities, 2001-2021.

File PVGIS_Ouessant_40deg_2013_2016.csv.xz created by P. Haessig, 2021,
in `~/Travail/11 Solar data/PVGIS/Ouessant hourly`

## Merge

Done by Python script `merge_PVGIS_load_data.py`.
