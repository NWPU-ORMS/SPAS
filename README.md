# Stochastic Patient Admission Scheduling

This repository contains the implementation of the following paper:

> Haichao Liu, Yang Wang, Jin-Kao Hao, Abraham P. Punnen. Stochastic patient admission scheduling with an exponential number of scenarios. *IISE Transactions*, 2026, accept.

This repository contains two independent implementations and the instance data used in the paper:

- `static version/`: Static patient admission scheduling with SV and SAA-SV methods.
- `dynamic version/`: Rolling horizon planning for dynamic patient arrivals.
- `instance generator/`: Instance generation program and datasets.

Each solver version has its own source code, instances, README, logs, and results. Run commands from the corresponding version directory.

## Instance generator

Our instance generation program is based on the program of [Ceschia and Schaerf (2012)](https://bitbucket.org/satt/PASU/). The original program generates instances with a fixed overstay length for each patient. We modified the program to give a number of scenarios for each patient, where each scenario represents a possible realization of the overstay length for each patient.

- `instance generator/ins_gen.py`: Instance generation program.
- `instance generator/example/`: Randomly generated instances, grouped by maximum overstay (`1dayOverstay`, `2daysOverstay`), size combination (`S-S`, `S-M`, `S-L`, `M-S`, `M-M`), and occupancy (`DSR40` to `DSR70`).
- `instance generator/real-life instance/`: Real-life hospital instance.

## Requirements

The models were implemented and solved using Gurobi Optimizer 11.0.0 with its default parameter settings. 