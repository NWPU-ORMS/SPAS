# Dynamic Version

This folder contains the rolling horizon SAA-SV implementation for dynamic patient arrivals.

Each rolling day rebuilds a planning-window instance from the current patient states, then runs iterative SAA warm starts and a final state-variable (SV) solve.

## Main files

- `src/main_rpo_SAA_SV.py`: Entry point for rolling horizon SAA-SV.
- `src/RPO.py`: Rolling horizon procedure, patient-state updates, and the SAA-SV loop.
- `src/InstanceGet_SV3.py`: Loads dynamic instances and rolling state data.
- `src/PRAU3_SV2.py`: State variable model for a rolling planning window.
- `src/PRAUWT3_SB.py`: SAA model used by the rolling procedure.
- `src/Simulator3.py`: Evaluates the final rolling horizon solution.

## Folders

- `example/Uset624/N1/S1/`: Real-life instance, type `S1`.
- `example/Uset624/N1/Sn/`: Real-life instance, type `Sn`.
- `log/`: Solver logs created during execution.
- `result/`: Solution files created during execution.

## Run

The code requires NumPy, Gurobi, and a valid Gurobi license. Run commands from this directory:

```sh
python src/main_rpo_SAA_SV.py 624 1 Sn 60 30 100
```

The six positional arguments are:

1. Instance size (`Uset{size}`)
2. Instance number (`N{num}`)
3. Instance type (`S1` or `Sn`)
4. Time limit per rolling day, in seconds
5. Number of rolling days
6. Overflow penalty `W_op`

The command above reads `example/Uset624/N1/Sn/`. Rejection penalty `W_DE1` defaults to `10000` and transfer penalty `W_tr` defaults to `100`.

On each rolling day, `SAA_SV` uses the first half of the time limit for up to three SAA iterations (10 sampled scenarios by default). Each SAA plan is evaluated with the first-stage decisions fixed in the SV model. The best plan warm-starts the final SV solve in the remaining time.