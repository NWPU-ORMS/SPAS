import subprocess
from PRAU2_SV2 import PRAU2_SV
from InstanceGet_SV2 import Instance
from Simulator2 import Simulator
import os
import sys
import json

## 转换json文件中的键为整数
def convert_keys(data):
    new_data = {}
    for key, value in data.items():
        new_key = int(key) if key.isdigit() else key  # 将数字字符串的键转换为整数
        if isinstance(value, dict):  # 如果值是字典，递归调用
            new_data[new_key] = convert_keys(value)
        else:
            new_data[new_key] = value
    return new_data

## 读取实例和解决方案，返回解决方案的字典
def obtain_result(instance, solution_path, mode = 0):
    
    with open(solution_path, 'r') as f:
        solution = json.load(f)
    solution = convert_keys(solution)
    
    if mode == 1:
        sim = Simulator(instance, solution)
        sim.runLargeScaleApproximate() # 运行大规模近似算法评估结果
        solution.update({"SimulateCost":sim.expected_cost})
    else:
        solution.update({"SimulateCost":solution['Objective']})
    
    return solution

if __name__ == '__main__':
    
    setnum = int(sys.argv[1])
    nnum = int(sys.argv[2])
    ptype = sys.argv[3]
    time_limit = int(sys.argv[4])
    OP_cost = int(sys.argv[5])
    
    ## run C++ code
    process = subprocess.Popen(['bin/PRAU2_cpp', sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # 循环读取输出
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line.strip())
        
    # 等待子进程结束
    process.wait()
    
    # 检查子进程的退出状态
    if process.returncode == 0:
        print("Program executed successfully")
    else:
        print("Program terminated with an error")
    
    ## 运行仿真评估
    example_path = 'example/' + 'Uset'+str(setnum) + '/N'+str(nnum) + '/' + ptype + '/'
    ins = Instance(example_path, in_OP = OP_cost)
    result_path = 'result/' + 'Uset'+str(setnum) + '/N'+str(nnum) + '/' + ptype + '/SBResult'+str(setnum) + '_op' + str(OP_cost)+'.txt'
    solution = obtain_result(ins, result_path, mode = 1)
    print("SimulateCost:", solution['SimulateCost'])
    ## 保存仿真后的结果
    with open(result_path, 'w') as file:
        json.dump(solution, file)
        
