from InstanceGet_SV3 import Instance
import os
import sys
from RPO import RPO
from Simulator3 import Simulator as TSim

if __name__ == '__main__':

    print('instance:', int(sys.argv[1]))
    print('num:', sys.argv[2])
    print('ptype:', sys.argv[3])
    print('time limit:', int(sys.argv[4]))
    print('total_rolling_day:', int(sys.argv[5]))
    print('OP:', int(sys.argv[6]))
    
    setnum = int(sys.argv[1])
    nnum = int(sys.argv[2])
    ptype = sys.argv[3]
    time_limit = int(sys.argv[4])
    total_rolling_day = int(sys.argv[5])
    OP_cost = int(sys.argv[6])
    
    example_list = ['Uset'+str(setnum), 'N'+str(nnum), ptype]
    example_path = 'example/'
    for file in example_list:
        example_path += file + '/'
    ins = Instance(example_path, in_OP = OP_cost)

    result_path = os.path.join('result', str(setnum), str(nnum), ptype)
    log_path = os.path.join('log', str(setnum), str(nnum), ptype)
    os.makedirs(result_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)

    rpo = RPO(ins, time_limit, result_path=result_path, log_path=log_path)
    rpo.SAA_SV_solve(total_rolling_day)