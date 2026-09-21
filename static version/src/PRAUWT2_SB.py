import gurobipy as gp
from gurobipy import GRB
from InstanceGet_SV2 import Instance
import random as rd
import json
import time
import random

TimeToBest = 0
BestSol = 1E10

def RecordTimeToBest(model, where):
    if where == GRB.Callback.MIPSOL:
        global TimeToBest, BestSol
        obj = model.cbGet(GRB.Callback.MIPSOL_OBJ)
        if BestSol - obj> 1e-5:
            BestSol = obj
            TimeToBest = model.cbGet(GRB.Callback.RUNTIME)
        # print(BestSol - obj, TimeToBest)

class PRAUWT_SB:
    
    def __init__(self, instance:Instance, modified_scenario:int):
        self.instance = instance
        self.modified_scenario = modified_scenario
    
    def EVP(self):
        self.modified_L_pu = self.instance.L_ps

    def ScenarioCreate(self):
        """Generate overstay scenarios for any supported maximum overstay."""
        self.modified_L_pu = [
            [0 for _ in range(self.modified_scenario)]
            for _ in range(self.instance.patients + 1)
        ]

        for scenario in range(self.modified_scenario):
            for p in range(1, self.instance.patients + 1):
                ratio = 0.5 if scenario == 0 else rd.random()
                fixed_los = self.instance.L_p[p]
                max_stay = self.instance.DU_p[p]['max_stay']
                max_overstay = max_stay - fixed_los
                overstay = 0

                for extra_day in range(1, max_overstay + 1):
                    stay_day = fixed_los + extra_day
                    if stay_day not in self.instance.DU_p[p]:
                        raise ValueError(
                            f'Missing LOS probability: patient={p}, day={stay_day}'
                        )
                    if ratio <= self.instance.DU_p[p][stay_day]:
                        overstay = extra_day
                    else:
                        break

                self.modified_L_pu[p][scenario] = overstay
    
    def EliteScenarioCreate3(self):
        self.modified_L_pu = [[0 for o in range(self.modified_scenario)] for p in range(self.instance.patients+1)]
        ## 生成第一个场景，采用均值
        for o in range(self.modified_scenario):
            if o == 0:
                ratio = 0.5
            else:
                ratio = rd.random()
            ## 生成初始场景采用30%的概率，其他场景，采用随机数
            for p in range(1, self.instance.patients+1):
                d = self.instance.DU_p[p]['max_stay']
                
                if ratio <= self.instance.DU_p[p][d] :
                    dd1 = 1
                else:
                    dd1 = 0

                self.modified_L_pu[p][o] = dd1
                # print(dd1)
                # print(p, self.instance.DU_p[p][d], dd1, self.instance.L_ps[p][o])
    
    def EliteScenarioCreate2(self):
        self.modified_L_pu = [[0 for o in range(self.modified_scenario)] for p in range(self.instance.patients+1)]
        ## 生成第一个场景，采用均值
        for o in range(self.modified_scenario):
            ## 生成初始场景采用30%的概率，其他场景，采用随机数
            for p in range(1, self.instance.patients+1):
                for j in [1, 2]:
                    if o == 0:
                        ratio = 0.5
                    else:
                        ratio = rd.random()
                    l = self.instance.L_p[p]
                    # print(p, l+j, self.instance.DU_p[p], ratio)
                    if ratio <= self.instance.DU_p[p][l + j]:
                        dd1 = j
                    else:
                        dd1 = j - 1
                        break

                self.modified_L_pu[p][o] = dd1
                # print(p, self.instance.DU_p[p], dd1, self.instance.L_ps[p][o])
    
    def EliteScenarioCreate(self):
        self.modified_L_pu = [[0 for o in range(self.modified_scenario)] for p in range(self.instance.patients+1)]
        ## 生成第一个场景，采用均值
        for o in range(self.modified_scenario):
            for p in range(1, self.instance.patients+1):
                dd1 = 0
                ## 生成初始场景采用50%的概率，其他场景，采用随机数
                if o == 0:
                    ratio = 0.5
                else:
                    ratio = rd.random()
                for d in range(self.instance.planning_horizon):
                    if d >= self.instance.L_p[p] and d <= self.instance.DU_p[p]['max_stay']:
                        if self.instance.DU_p[p][d] < ratio:
                            dd1 = d
                            break
                    elif d > self.instance.DU_p[p]['max_stay']:
                        dd1 = self.instance.DU_p[p]['max_stay']
                        break
            
                if dd1 == 0:
                    dd1 = self.instance.DU_p[p]['max_stay']
                self.modified_L_pu[p][o] = dd1
    
    def CreateModel(self):
        # 创建模型
        self.model = gp.Model("PRAUWT_SB")
        
        # 创建变量
        ## x_pri
        x_index = []
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            x_index.append((p, r, i))
        self.x = self.model.addVars(x_index, vtype=GRB.BINARY, name=['x_'+str(p)+'_'+str(r)+'_'+str(i) for p, r, i in x_index])
        
        # b_rdw
        b_index = []
        for d in range(self.instance.planning_horizon):
            for r in range(self.instance.rooms):
                if self.instance.RT_r[r] == 2:
                    for w in range(self.modified_scenario):
                        b_index.append((r, d, w))
        self.b = self.model.addVars(b_index, vtype=GRB.BINARY, name=['b_'+str(r)+'_'+str(d)+'_'+str(w) for r, d, w in b_index])
        self.u = self.model.addVars(b_index, vtype=GRB.BINARY, name=['u_'+str(r)+'_'+str(d)+'_'+str(w) for r, d, w in b_index])
        
        # z_rdw
        z_index = []
        ub = []
        for d in range(self.instance.planning_horizon):
            for r in range(self.instance.rooms):
                for w in range(self.modified_scenario):
                    z_index.append((r, d, w))
                    ub.append(self.instance.Q_r[r])
        self.z = self.model.addVars(z_index, vtype=GRB.INTEGER, lb = 0, ub = ub, name=['z_'+str(r)+'_'+str(d)+'_'+str(w) for r, d, w in z_index])
        
        # 创建目标函数
        obj = gp.LinExpr()
        obj = 0
        
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            obj += self.instance.W_DE * (i - self.instance.DA_p[p][0]) * self.x[p, r, i]

        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            for d in range(self.instance.planning_horizon):
                                if d >= i and d < i + self.instance.L_p[p]:
                                    obj += self.instance.C_pr[p][r] * self.x[p, r, i]
        
        for w in range(self.modified_scenario):
            for p in range(1, self.instance.patients+1):
                for r in range(self.instance.rooms):
                    if self.instance.R_p[p][r] == 1:
                        for i in range(self.instance.planning_horizon):
                            if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                for d in range(self.instance.planning_horizon):
                                    if d >= i + self.instance.L_p[p] and d < i + self.instance.L_p[p] + self.modified_L_pu[p][w]:
                                        obj += self.instance.C_pr[p][r] * self.x[p, r, i] * 1/self.modified_scenario

        for w in range(self.modified_scenario):
            for r in range(self.instance.rooms):
                if self.instance.RT_r[r] == 2:
                    for d in range(self.instance.planning_horizon):
                        obj += self.instance.W_RG * self.b[r, d, w] * 1/self.modified_scenario
        
        for w in range(self.modified_scenario):
            for r in range(self.instance.rooms):
                for d in range(self.instance.planning_horizon):
                    obj += self.instance.W_op * self.z[r, d, w] * 1/self.modified_scenario
                    
        self.model.setObjective(obj, GRB.MINIMIZE)
        
        # 构建约束
        linexp = gp.LinExpr()
        
        ## 约束1
        for p in range(1, self.instance.patients+1):
            linexp = 0
            for i in range(self.instance.planning_horizon):
                if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                    for r in range(self.instance.rooms):
                        if self.instance.R_p[p][r] == 1:
                            linexp += self.x[p, r, i]
            self.model.addConstr(linexp == 1, name='C1_'+str(p))
            
        # 约束2
        for r in range(self.instance.rooms):
            for d in range(self.instance.planning_horizon):
                for w in range(self.modified_scenario):
                    linexp = 0
                    linexp += self.z[r, d, w] + self.instance.Q_r[r]
                    num = 0
                    for p in range(1, self.instance.patients+1):
                        if self.instance.R_p[p][r] == 1:
                            for i in range(self.instance.planning_horizon):
                                if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                    if d >= i and d < i + self.instance.L_p[p] + self.modified_L_pu[p][w]:
                                        linexp -= self.x[p, r, i]
                                        num += 1
                    if num > 0:
                        self.model.addConstr(linexp >= 0, name='C2_'+str(r)+'_'+str(d)+'_'+str(w))

        for r in range(self.instance.rooms):
            for d in range(self.instance.planning_horizon):
                for w in range(self.modified_scenario):
                    linexp = 0
                    linexp += self.instance.Q_r[r]
                    num = 0
                    for p in range(1, self.instance.patients+1):
                        if self.instance.R_p[p][r] == 1:
                            for i in range(self.instance.planning_horizon):
                                if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                    if d >= i and d < i + self.instance.L_p[p]:
                                        linexp -= self.x[p, r, i]
                                        num += 1
                    if num > 0:
                        self.model.addConstr(linexp >= 0, name='C2-1_'+str(r)+'_'+str(d)+'_'+str(w))
        
        ## 约束3
        for r in range(self.instance.rooms):
            if self.instance.RT_r[r] == 2:
                for d in range(self.instance.planning_horizon):
                    for w in range(self.modified_scenario):
                        linexp = 0
                        num = 0
                        linexp += 2 * self.instance.Q_r[r]  * (self.u[r, d, w] + self.b[r, d, w])
                        for p in range(1, self.instance.patients+1):
                            if self.instance.R_p[p][r] == 1 and self.instance.PG_pg[p][0] == 1:
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                        if d >= i and d < i + self.instance.L_p[p] + self.modified_L_pu[p][w]:
                                            num += 1
                                            linexp -= self.x[p, r, i]
                        if num > 0:
                            self.model.addConstr(linexp >= 0, name='C3_'+str(r)+'_'+str(d)+'_'+str(w))
        
        ## 约束4
        for r in range(self.instance.rooms):
            if self.instance.RT_r[r] == 2:
                for d in range(self.instance.planning_horizon):
                    for w in range(self.modified_scenario):
                        linexp = 0
                        num = 0
                        linexp += 2 * self.instance.Q_r[r] * (1 - self.u[r, d, w] + self.b[r, d, w])
                        for p in range(1, self.instance.patients+1):
                            if self.instance.R_p[p][r] == 1 and self.instance.PG_pg[p][1] == 1:
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                        if d >= i and d < i + self.instance.L_p[p] + self.modified_L_pu[p][w]:
                                            num += 1
                                            linexp -= self.x[p, r, i]
                        if num > 0:
                            self.model.addConstr(linexp >= 0, name='C5_'+str(r)+'_'+str(d)+'_'+str(w))
                            
    def Solve(self, time_limit = 0, log_file = '', input_solution = None, deadline = None):
        self.ScenarioCreate()
        # self.EVP()
        time_start = time.time()
        self.CreateModel()
        self.TimeToBuildModel = time.time() - time_start
        if deadline is not None:
            time_limit = max(0, deadline - time.monotonic())
        if time_limit > 0:
            self.model.setParam('TimeLimit', time_limit)
        if log_file != '':
            self.model.setParam('LogFile',log_file)
        if input_solution is not None:
            for (p, r, i), variable in self.x.items():
                selected = input_solution[p]['Admission'] == i and input_solution[p][i] == r
                variable.Start = int(selected)
        if deadline is not None:
            time_limit = deadline - time.monotonic()
            if time_limit <= 0:
                raise TimeoutError('SAA time budget expired during model construction')
            self.model.setParam('TimeLimit', time_limit)
        self.model.optimize(RecordTimeToBest)
    
    def output(self, solution, result_file):
        # 保存结果
        with open(result_file, 'w') as file:
            json.dump(solution, file)

    def get_assignment(self):
        
        global TimeToBest
        solution = {}
        # 目标值
        solution.update({'Objective':self.model.getObjective().getValue()})
        # 到达最佳目标值的时间
        solution.update({'TimeToBest':TimeToBest})
        # 运行时间
        solution.update({'TimeToEnd':self.model.getAttr('Runtime')})
        # 建模时间
        solution.update({'TimeToBuildModel':self.TimeToBuildModel})
        # 下界
        solution.update({'LowerBound':self.model.getAttr('ObjBound')})
        # 分枝树的节点数
        solution.update({'NodeCount':self.model.getAttr('NodeCount')})
        # 获取模型的变量数量
        solution.update({'NumVars':self.model.getAttr('NumVars')})
        # 获取模型的约束数量
        solution.update({'NumConstrs':self.model.getAttr('NumConstrs')})
        
        for p in range(1, self.instance.patients+1):
            if p not in solution.keys():
                    solution.update({p:{}})
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            if abs(self.x[p, r, i].x - 1) < 1e-3:
                                solution[p].update({'Admission':i})
                                for d in range(self.instance.planning_horizon):
                                    if d >= i and d < i + self.instance.L_p[p]:
                                        solution[p].update({d:r})
                                break
        
        return solution
