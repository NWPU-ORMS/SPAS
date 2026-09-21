# Patient Admission Scheduling

This folder contains Python and C++ code for scheduling patient admissions and assigning hospital rooms under uncertain lengths of stay.

## Main files

- `src/main_PRAU_SV.py`: Runs the Python state variable model.
- `src/main_PRAU2_cpp.py`: Runs the C++ model and evaluates its solution.
- `src/SAA-SV.py`: Runs up to three SAA iterations and uses the best solution to warm start the SV model.
- `src/InstanceGet_SV2.py`: Loads and prepares instance data.
- `src/PRAU2_SV2.py`: Python state variable model.
- `src/PRAU2_SB.py`: Python scenario based model.
- `src/PRAUWT2_SB.py`: SAA model used by the SAA-SV algorithm.
- `src/Simulator2.py`: Simulates and evaluates solutions.

## Folders

- `src/cpp/`: C++ source files and CMake configuration.
- `bin/`: Prebuilt C++ executable.
- `example/overstay_1day/`: Instances with a maximum overstay of one day.
- `example/overstay_2days/`: Instances with a maximum overstay of two days.
- `log/`: Solver logs from previous experiments.

The code uses Gurobi. Run the entry point scripts from this folder with an instance size, variant, type, time limit, and overflow penalty. For example:

```sh
python src/main_PRAU_SV.py 50 1 S1 3600 100
python src/SAA-SV.py 50 1 S1 3600 100 10
python src/SAA-SV.py 50 1 S1 3600 100 10 --overstay-days 1
```

The last argument of `SAA-SV.py` is the number of sampled scenarios. It defaults to `10` if omitted.
Both commands use the two-day dataset by default. Add `--overstay-days 1` to use the one-day dataset.
