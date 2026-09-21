from PRAU2_SV2 import PRAU2_SV
from InstanceGet_SV2 import Instance
import argparse
import os

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('size', type=int)
    parser.add_argument('variant', type=int)
    parser.add_argument('type')
    parser.add_argument('time_limit', type=int)
    parser.add_argument('overflow_penalty', type=int)
    parser.add_argument('--overstay-days', type=int, choices=[1, 2], default=2)
    args = parser.parse_args()

    setnum = args.size
    nnum = args.variant
    ptype = args.type
    time_limit = args.time_limit
    OP_cost = args.overflow_penalty

    print('instance:', setnum)
    print('num:', nnum)
    print('ptype:', ptype)
    print('time limit:', time_limit)
    print('OP:', OP_cost)
    print('maximum overstay:', args.overstay_days)
    
    example_list = ['Uset'+str(setnum), 'N'+str(nnum), ptype]
    example_path = f'example/overstay_{args.overstay_days}day' + ('s/' if args.overstay_days == 2 else '/')
    for file in example_list:
        example_path += file + '/'
        if not os.path.exists(example_path):
            os.makedirs(example_path)
    
    log_list = ['log', f'overstay_{args.overstay_days}day' + ('s' if args.overstay_days == 2 else ''), 'Uset'+str(setnum), 'N'+str(nnum), ptype]
    log_path = ''
    for file in log_list:
        log_path += file + '/'
        if not os.path.exists(log_path):
            os.makedirs(log_path)
            
    result_list = ['result', f'overstay_{args.overstay_days}day' + ('s' if args.overstay_days == 2 else ''), 'Uset'+str(setnum), 'N'+str(nnum), ptype]
    result_path = ''
    for file in result_list:
        result_path += file + '/'
        if not os.path.exists(result_path):
            os.makedirs(result_path)
    
    log_file = log_path +'SVLog'+str(setnum) + '_op' + str(OP_cost)+ '.txt'
    result_file = result_path +'SVResult'+str(setnum) + '_op' + str(OP_cost)+'.txt'
    ins = Instance(example_path, in_OP = OP_cost)
    prau2_sv = PRAU2_SV(ins)
    prau2_sv.Solve(log_file=log_file, time_limit=time_limit)
    solution = prau2_sv.get_assignment()
    solution.update({'SimulateCost':solution['Objective']})
    prau2_sv.output(solution, result_file)
