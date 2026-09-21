import gurobipy as gp
from gurobipy import GRB
from InstanceGet_SV2 import Instance
import json
import time

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
        
class PRAU2_SB:
    
    def __init__(self, instance:Instance):
        self.instance = instance
        
    # 生成模型
    def CreateModel(self):
        # 创建模型
        self.model = gp.Model("PRAU2_SB")
        
        # 创建变量
        ## alpha_pd
        alpha_index = []
        for p in range(1, self.instance.patients+1):
            for d in range(self.instance.planning_horizon):
                if d >= self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                    alpha_index.append((p, d))
        self.alpha = self.model.addVars(alpha_index, vtype=GRB.BINARY, name=['alpha_'+str(p)+'_'+str(d) for p, d in alpha_index])
        
        ## x_prid
        x_index = []
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            for d in range(self.instance.planning_horizon):
                                if d >= i and d < i + self.instance.L_p[p]:
                                    x_index.append((p, r, i, d))
        self.x = self.model.addVars(x_index, vtype=GRB.BINARY, name=['x_'+str(p)+'_'+str(r)+'_'+str(i)+'_'+str(d) for p, r, i, d in x_index])
        
        # b_rdw
        b_index = []
        for d in range(self.instance.planning_horizon):
            for r in range(self.instance.rooms):
                if self.instance.RT_r[r] == 2:
                    for w in range(self.instance.scenario):
                        b_index.append((r, d, w))
        self.b = self.model.addVars(b_index, vtype=GRB.BINARY, name=['b_'+str(r)+'_'+str(d)+'_'+str(w) for r, d, w in b_index])
        self.u = self.model.addVars(b_index, vtype=GRB.BINARY, name=['u_'+str(r)+'_'+str(d)+'_'+str(w) for r, d, w in b_index])
        
        # z_rdw
        z_index = []
        ub = []
        for d in range(self.instance.planning_horizon):
            for r in range(self.instance.rooms):
                for w in range(self.instance.scenario):
                    z_index.append((r, d, w))
                    ub.append(self.instance.Q_r[r])
        self.z = self.model.addVars(z_index, vtype=GRB.INTEGER, lb = 0, ub = ub, name=['z_'+str(r)+'_'+str(d)+'_'+str(w) for r, d, w in z_index])
                    
        # t_pd
        t_index = []
        for p in range(1, self.instance.patients+1):
            if self.instance.L_p[p] >= 2:
                for d in range(self.instance.planning_horizon):
                    if d > self.instance.DA_p[p][0] and d < self.instance.DA_p[p][1] + self.instance.L_p[p]:
                        t_index.append((p, d))
        self.t = self.model.addVars(t_index, vtype=GRB.BINARY, name=['t_'+str(p)+'_'+str(d) for p, d in t_index])
        
        # 创建目标函数
        obj = gp.LinExpr()
        obj = 0
        
        for p in range(1, self.instance.patients+1):
            for d in range(self.instance.planning_horizon):
                if d >= self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                    obj += self.instance.W_DE * (d - self.instance.DA_p[p][0]) * self.alpha[p, d]
                    
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            for d in range(self.instance.planning_horizon):
                                if d >= i and d < i + self.instance.L_p[p]:
                                    obj += self.instance.C_pr[p][r] * self.x[p, r, i, d]
        
        for p in range(1, self.instance.patients+1):
            if self.instance.L_p[p] >= 2:
                for d in range(self.instance.planning_horizon):
                    if d > self.instance.DA_p[p][0] and d < self.instance.DA_p[p][1] + self.instance.L_p[p]:
                        obj += self.instance.W_tr * self.t[p, d]
        
        
        for w in range(self.instance.scenario): #self.instance.scenario
            for p in range(1, self.instance.patients+1):
                for r in range(self.instance.rooms):
                    if self.instance.R_p[p][r] == 1:
                        for i in range(self.instance.planning_horizon):
                            if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                for d in range(self.instance.planning_horizon):
                                    if d >= i + self.instance.L_p[p] and d < i + self.instance.L_p[p] + self.instance.L_ps[p][w]:
                                        dd1 = i + self.instance.L_p[p] - 1
                                        obj += self.instance.C_pr[p][r] * self.x[p, r, i, dd1] * 1/self.instance.scenario
                                        # print(p, r, i, d, dd1, w, self.instance.C_pr[p][r]* 1/self.instance.scenario )
                                    
        
        for w in range(self.instance.scenario):
            for r in range(self.instance.rooms):
                if self.instance.RT_r[r] == 2:
                    for d in range(self.instance.planning_horizon):
                        obj += self.instance.W_RG * self.b[r, d, w] * 1/self.instance.scenario
        
        for w in range(self.instance.scenario):
            for r in range(self.instance.rooms):
                for d in range(self.instance.planning_horizon):
                    obj += self.instance.W_op * self.z[r, d, w] * 1/self.instance.scenario
        
        self.model.setObjective(obj, GRB.MINIMIZE)
        
        # 构建约束
        linexp = gp.LinExpr()
        
        ## 约束1
        for p in range(1, self.instance.patients+1):
            linexp = 0
            for d in range(self.instance.planning_horizon):
                if d >= self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                    linexp += self.alpha[p, d]
            self.model.addConstr(linexp == 1, name='C1_'+str(p))
            
        ## 约束2
        for p in range(1, self.instance.patients+1):
            for i in range(self.instance.planning_horizon):
                if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                    for d in range(self.instance.planning_horizon):
                        if d >= i and d < i + self.instance.L_p[p]:
                            linexp = 0
                            for r in range(self.instance.rooms):
                                if self.instance.R_p[p][r] == 1:
                                    linexp += self.x[p, r, i, d]
                            linexp -= self.alpha[p, i]
                            self.model.addConstr(linexp == 0, name='C2_'+str(p)+'_'+str(i)+'_'+str(d))
                            
        ## 约束2-1
        for r in range(self.instance.rooms):
            for d in range(self.instance.planning_horizon):
                for w in range(self.instance.scenario):
                    linexp = 0
                    linexp += self.instance.Q_r[r]
                    num = 0
                    for p in range(1, self.instance.patients+1):
                        if self.instance.R_p[p][r] == 1:
                            for i in range(self.instance.planning_horizon):
                                if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                    if d >= i and d < i + self.instance.L_p[p]:
                                        num += 1
                                        linexp -= self.x[p, r, i, d]
                    if num > 0:
                        self.model.addConstr(linexp >= 0, name='C2-1_'+str(r)+'_'+str(d)+'_'+str(w))
        
        ## 约束3
        for r in range(self.instance.rooms):
            for d in range(self.instance.planning_horizon):
                for w in range(self.instance.scenario):
                    linexp = 0
                    linexp += self.z[r, d, w] + self.instance.Q_r[r]
                    num = 0
                    for p in range(1, self.instance.patients+1):
                        if self.instance.R_p[p][r] == 1:
                            for i in range(self.instance.planning_horizon):
                                if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                    if d >= i and d < i + self.instance.L_p[p]:
                                        num += 1
                                        linexp -= self.x[p, r, i, d]
                                    elif d >= i + self.instance.L_p[p] and d < i + self.instance.L_p[p] + self.instance.L_ps[p][w]:
                                        num += 1
                                        linexp -= self.x[p, r, i, i + self.instance.L_p[p]-1]
                    if num > 0:
                        self.model.addConstr(linexp >= 0, name='C3_'+str(r)+'_'+str(d)+'_'+str(w))

        ## 约束4
        for r in range(self.instance.rooms):
            if self.instance.RT_r[r] == 2:
                for d in range(self.instance.planning_horizon):
                    for w in range(self.instance.scenario):
                        linexp = 0
                        num = 0
                        linexp += 2*self.instance.Q_r[r] * (self.u[r, d, w] + self.b[r, d, w])
                        for p in range(1, self.instance.patients+1):
                            if self.instance.R_p[p][r] == 1:
                                if self.instance.PG_pg[p][0] == 1:
                                    for i in range(self.instance.planning_horizon):
                                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                            if d >= i and d < i + self.instance.L_p[p]:
                                                num += 1
                                                linexp -= self.x[p, r, i, d]
                                            elif d >= i + self.instance.L_p[p] and d < i + self.instance.L_p[p] + self.instance.L_ps[p][w]:
                                                num += 1
                                                linexp -= self.x[p, r, i, i + self.instance.L_p[p]-1]
                        if num > 0:
                            self.model.addConstr(linexp >= 0, name='C4_'+str(r)+'_'+str(d)+'_'+str(w))
                            
        ## 约束5
        for r in range(self.instance.rooms):
            if self.instance.RT_r[r] == 2:
                for d in range(self.instance.planning_horizon):
                    for w in range(self.instance.scenario):
                        linexp = 0
                        num = 0
                        linexp += 2*self.instance.Q_r[r] * (1 - self.u[r, d, w] + self.b[r, d, w])
                        for p in range(1, self.instance.patients+1):
                            if self.instance.R_p[p][r] == 1:
                                if self.instance.PG_pg[p][1] == 1:
                                    for i in range(self.instance.planning_horizon):
                                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                            if d >= i and d < i + self.instance.L_p[p]:
                                                num += 1
                                                linexp -= self.x[p, r, i, d]
                                            elif d >= i + self.instance.L_p[p] and d < i + self.instance.L_p[p] + self.instance.L_ps[p][w]:
                                                num += 1
                                                linexp -= self.x[p, r, i, i + self.instance.L_p[p]-1]
                        if num > 0:
                            self.model.addConstr(linexp >= 0, name='C5_'+str(r)+'_'+str(d)+'_'+str(w))
        
        ## 约束6
        for p in range(1, self.instance.patients+1):
            if self.instance.L_p[p] >= 2:
                for r in range(self.instance.rooms):
                    if self.instance.R_p[p][r] == 1:
                        for d in range(self.instance.planning_horizon):
                            if d > self.instance.DA_p[p][0] and d < self.instance.DA_p[p][1] + self.instance.L_p[p]:
                                linexp = 0
                                linexp += self.t[p, d]
                                if d > self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                                    linexp += self.alpha[p, d]
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                                        if d > i and d < i + self.instance.L_p[p]:
                                            linexp -= self.x[p, r, i, d] 
                                            linexp -= - self.x[p, r, i, d - 1]
                                self.model.addConstr(linexp >= 0, name='C6_'+str(p)+'_'+str(r)+'_'+str(d))
                                    
    def Solve(self, time_limit = 0, log_file = '', result_file = ''):
        time_start = time.time()
        self.CreateModel()
        self.TimeToBuildModel = time.time() - time_start
        if time_limit > 0:
            self.model.setParam('TimeLimit', time_limit)
        if log_file != '':
            self.model.setParam('LogFile',log_file)
        self.model.setParam('Method',3)
        self.model.optimize(RecordTimeToBest)
        
        # 保存结果
        if result_file != '':
            solution = self.get_assignment()
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
            for d in range(self.instance.planning_horizon):
                if d >= self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                    if abs(self.alpha[p, d].x - 1) < 1e-3:
                        solution[p].update({'Admission':d})
                        break
        
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            for d in range(self.instance.planning_horizon):
                                if d >= i and d < i + self.instance.L_p[p]:
                                    if abs(self.x[p, r, i, d].x - 1) < 1e-3:
                                        solution[p].update({d:r})
        
        return solution
                            