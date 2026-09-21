"""Iterative SAA warm start followed by the full state-variable model."""

import argparse
import time
from pathlib import Path

from InstanceGet_SV2 import Instance
from PRAUWT2_SB import PRAUWT_SB
from PRAU2_SV2 import PRAU2_SV


def remaining(deadline):
    return max(0.0, deadline - time.monotonic())


def fix_first_stage(solver, solution):
    """Fix admission, room assignments, and transfer decisions to a SAA plan."""
    for (p, d), var in solver.alpha.items():
        value = int(d == solution[p]['Admission'])
        var.LB = var.UB = value
    for (p, r, i, d), var in solver.x.items():
        value = int(i == solution[p]['Admission'] and solution[p][d] == r)
        var.LB = var.UB = value
    for (p, d), var in solver.t.items():
        admission = solution[p]['Admission']
        value = int(admission < d < admission + solver.instance.L_p[p]
                    and solution[p][d - 1] != solution[p][d])
        var.LB = var.UB = value


def evaluate_with_sv(instance, solution, deadline):
    """Return the full SV objective with the SAA first-stage plan fixed."""
    solver = PRAU2_SV(instance)
    solver.CreateModel()
    fix_first_stage(solver, solution)
    limit = remaining(deadline)
    if limit <= 0:
        return None
    solver.model.setParam('OutputFlag', 0)
    solver.model.setParam('TimeLimit', limit)
    solver.model.optimize()
    if solver.model.SolCount == 0:
        return None
    return solver.model.ObjVal


def run(args):
    if args.time_limit <= 0 or args.scenarios <= 0 or args.max_iter <= 0:
        raise ValueError('time_limit, scenarios, and max_iter must be positive')

    dataset = f'overstay_{args.overstay_days}day' + ('s' if args.overstay_days == 2 else '')
    instance_dir = Path('example') / dataset / f'Uset{args.size}' / f'N{args.variant}' / args.type
    if not instance_dir.is_dir():
        raise FileNotFoundError(instance_dir)
    instance = Instance(str(instance_dir) + '/', in_OP=args.overflow_penalty)

    output_dir = Path('result') / dataset / f'Uset{args.size}' / f'N{args.variant}' / args.type
    log_dir = Path('log') / dataset / f'Uset{args.size}' / f'N{args.variant}' / args.type
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f'{args.size}_op{args.overflow_penalty}_ms{args.scenarios}'

    start = time.monotonic()
    saa_deadline = start + args.time_limit / 2
    final_deadline = start + args.time_limit
    best_plan = None
    best_cost = float('inf')
    previous_plan = None

    for iteration in range(1, args.max_iter + 1):
        stage_left = remaining(saa_deadline)
        if stage_left <= 0:
            break
        # Each solve may use all SAA time still available. An early finish
        # leaves that unused time for evaluation and another SAA round.
        saa_limit = stage_left
        saa = PRAUWT_SB(instance, args.scenarios)
        saa_log = log_dir / f'WSSAALog{stem}_iter{iteration}.txt'
        try:
            saa.Solve(time_limit=saa_limit, log_file=str(saa_log),
                      deadline=saa_deadline,
                      input_solution=best_plan or previous_plan)
        except TimeoutError:
            break
        if saa.model.SolCount == 0:
            print(f'SAA iteration {iteration}: no feasible solution')
            continue

        plan = saa.get_assignment()
        previous_plan = plan
        cost = evaluate_with_sv(instance, plan, saa_deadline)
        plan['SVFixedObjective'] = cost
        saa.output(plan, str(output_dir / f'WSSAAResult{stem}_iter{iteration}.txt'))
        print(f'SAA iteration {iteration}: fixed SV objective = {cost}')
        if cost is not None and cost < best_cost:
            best_cost = cost
            best_plan = plan

    if best_plan is None:
        best_plan = previous_plan
    if best_plan is None:
        raise RuntimeError('No feasible SAA solution was found')

    sv_limit = remaining(final_deadline)
    if sv_limit <= 0:
        raise RuntimeError('No time remains for the final SV solve')
    sv = PRAU2_SV(instance)
    sv_log = log_dir / f'WSSVLog{stem}.txt'
    sv.Solve(time_limit=sv_limit, log_file=str(sv_log),
             input_solution=best_plan, deadline=final_deadline)
    result = sv.get_assignment()
    result['BestSAAFixedObjective'] = None if best_cost == float('inf') else best_cost
    result['SAAMaxIter'] = args.max_iter
    result['SAAScenarios'] = args.scenarios
    result_path = output_dir / f'WSSVResult{stem}.txt'
    sv.output(result, str(result_path))
    print(f'SV result saved to {result_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('size', type=int)
    parser.add_argument('variant', type=int)
    parser.add_argument('type', help='Instance type, e.g. S1 or Sn')
    parser.add_argument('time_limit', type=float, help='Total time limit in seconds')
    parser.add_argument('overflow_penalty', type=int)
    parser.add_argument('scenarios', type=int, nargs='?', default=10)
    parser.add_argument('--max-iter', type=int, default=3)
    parser.add_argument('--overstay-days', type=int, choices=[1, 2], default=2)
    run(parser.parse_args())
