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

class PRAU2_SV:
    
    def __init__(self, instance:Instance):
        self.instance = instance
        self.TimeToBuildModel = 0
    
    # 创建模型1
    def CreateModel(self):
        # 创建模型
        self.model = gp.Model("PRAU2_SV")
        
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
        
        # t_pd
        t_index = []
        for p in range(1, self.instance.patients+1):
            for d in range(self.instance.planning_horizon):
                if d > self.instance.DA_p[p][0] and d < self.instance.DA_p[p][1] + self.instance.L_p[p]:
                    t_index.append((p, d))
        self.t = self.model.addVars(t_index, vtype=GRB.BINARY, name=['t_'+str(p)+'_'+str(d) for p, d in t_index])
        
        y0_index = []
        for p in range(self.instance.patients+1):
            for d in range(self.instance.planning_horizon):
                if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                    for r in range(self.instance.rooms):
                        if self.instance.R_p[p][r] == 1:
                            for n in range(self.instance.N_pdr[p][d][r]+1):
                                y0_index.append((p,d,r,n))
        self.y0 = self.model.addVars(y0_index, vtype=GRB.CONTINUOUS, lb = 0, ub = 1, name=["y0_" + str(p) + "_" + str(d) + "_" + str(r) + "_" + str(n) for p,d,r,n in y0_index])
        
        y1_index = []
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for d in range(self.instance.planning_horizon):
                        if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and i <= d and self.instance.DU_p[pp1]['max_stay'] >= d-i + 1:
                                        for n in range(self.instance.N_pdr1[p][d][r]+1):
                                            y1_index.append((p,d,i,r,n))
        self.y1 = self.model.addVars(y1_index, vtype=GRB.CONTINUOUS, lb = 0, ub = 1, name=["y1_" + str(p) + "_" + str(d) + "_" + str(i) + "_" + str(r) + "_" + str(n) for p,d,i,r,n in y1_index])
        
        q0_index = []
        for p in range(self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1 and self.instance.RT_r[r] == 2:
                    for d in range(self.instance.planning_horizon):
                        if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                            for s in self.instance.S_pdr[p][d][r]:
                                q0_index.append((p,d,r,s))
        self.q0 = self.model.addVars(q0_index, vtype=GRB.CONTINUOUS, lb = 0, ub = 1, name=["q0_" + str(p) + "_" + str(d) + "_" + str(r) + "_" + str(s) for p,d,r,s in q0_index])
        
        q1_index = []
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1 and self.instance.RT_r[r] == 2:
                    for d in range(self.instance.planning_horizon):
                        if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and i <= d and self.instance.DU_p[pp1]['max_stay'] >= d-i + 1:
                                        for s in self.instance.S_pdr[p][d][r]:
                                            q1_index.append((p,d,i,r,s))
        self.q1 = self.model.addVars(q1_index, vtype=GRB.CONTINUOUS, lb = 0, ub = 1, name=["q1_" + str(p) + "_" + str(d) + "_" + str(i) + "_" + str(r) + "_" + str(s) for p,d,i,r,s in q1_index])
        
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

        # 与期望场景相关的费用
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for i in range(self.instance.planning_horizon):
                        if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                            for d in range(self.instance.planning_horizon):
                                if d >= i + self.instance.L_p[p] and d <= i + self.instance.DU_p[p]['max_stay'] - 1:
                                    dd1 = i + self.instance.L_p[p] - 1
                                    obj += self.instance.DU_p[p][d - i + 1] * self.instance.C_pr[p][r]* self.x[p, r, i, dd1] 
                                    # print(p, r, i, dd1)
        
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for d in range(self.instance.DU_p[p]['min_date'], self.instance.DU_p[p]['max_date']+1):
                        if d < self.instance.planning_horizon:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and i <= d and self.instance.DU_p[pp1]['max_stay'] >= d-i + 1:
                                        for n in range(self.instance.N_pdr1[p][d][r]+1):
                                            obj += self.instance.W_pdirn[p][d][i][r][n] * self.y1[p,d,i,r,n]
        
        
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1 and self.instance.RT_r[r] == 2:
                    for d in range(self.instance.DU_p[p]['min_date'], self.instance.DU_p[p]['max_date']+1):
                        if d < self.instance.planning_horizon:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and i <= d and self.instance.DU_p[pp1]['max_stay'] >= d-i + 1:
                                        for s in self.instance.S_pdr[p][d][r]:
                                            obj += self.instance.W_pdirs[p][d][i][r][s] * self.q1[p,d,i,r,s]
        
        self.model.setObjective(obj, GRB.MINIMIZE)


        # 构建约束
        linexp = gp.LinExpr()
        
        ## 约束1
        for p in range(1, self.instance.patients+1):
        # for p in range(2, 3):
            linexp = 0
            for d in range(self.instance.planning_horizon):
                if d >= self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                    linexp += self.alpha[p, d]
            self.model.addConstr(linexp == 1, name='C1_'+str(p))
            
        ## 约束2
        for p in range(1, self.instance.patients+1):
        # for p in range(2, 3):
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
                                self.model.addConstr(linexp >= 0, name='C3_'+str(p)+'_'+str(r)+'_'+str(d))
                            
        ## 约束4
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for d in range(self.instance.DU_p[p]['min_date'], self.instance.DU_p[p]['max_date']+1):
                        if d < self.instance.planning_horizon:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i  and d <= self.instance.DU_p[pp1]['max_stay'] + i -1 :
                                        linexp = 0
                                        for n in range(self.instance.N_pdr1[p][d][r]+1):
                                            linexp += self.y1[p,d,i,r,n]
                                        if d < i + self.instance.L_p[pp1]:
                                            linexp -= self.x[pp1, r, i, d]
                                        elif d >= i + self.instance.L_p[pp1]:
                                            dd1 = i + self.instance.L_p[pp1] - 1
                                            linexp -= self.x[pp1, r, i, dd1]
                                        self.model.addConstr(linexp == 0, name='C4_'+str(p)+'_'+str(d)+'_'+str(i)+'_'+str(r)) 
        
        ## 约束5
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for d in range(self.instance.planning_horizon):
                        if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                linexp = 0
                                for n in range(self.instance.N_pdr[p][d][r]+1):
                                    linexp += self.y0[p,d,r,n]
                                linexp -= 1
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i and d <= self.instance.DU_p[pp1]['max_stay'] + i -1:
                                        if d < i + self.instance.L_p[pp1]:
                                            linexp -= - self.x[pp1, r, i, d]
                                        elif d >= i + self.instance.L_p[pp1]:
                                            dd1 = i + self.instance.L_p[pp1] - 1
                                            linexp -= - self.x[pp1, r, i, dd1]
                                self.model.addConstr(linexp == 0, name='C5_'+str(p)+'_'+str(d)+'_'+str(r))
        
        ## 约束6
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1 and self.instance.RT_r[r] == 2:
                    for d in range(self.instance.DU_p[p]['min_date'], self.instance.DU_p[p]['max_date']+1):
                        if d < self.instance.planning_horizon:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i  and d <= self.instance.DU_p[pp1]['max_stay'] + i -1 :
                                        linexp = 0
                                        for s in self.instance.S_pdr[p][d][r]:
                                            linexp += self.q1[p,d,i,r,s]
                                        if d < i + self.instance.L_p[pp1]:
                                            linexp -= self.x[pp1, r, i, d]
                                        elif d >= i + self.instance.L_p[pp1]:
                                            dd1 = i + self.instance.L_p[pp1] - 1
                                            linexp -= self.x[pp1, r, i, dd1]
                                        self.model.addConstr(linexp == 0, name='C6_'+str(p)+'_'+str(d)+'_'+str(i)+'_'+str(r)) 
        
        ## 约束7
        for p in range(self.instance.patients):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1 and self.instance.RT_r[r] == 2:
                    for d in range(self.instance.planning_horizon):
                        if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                            num_d = self.instance.total_number_of_day[d][r] # 当日的病人数
                            p_num = self.instance.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                            if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                pp1 = self.instance.P_dr[d][r][p_num+1]['p']
                                linexp = 0
                                for s in self.instance.S_pdr[p][d][r]:
                                    linexp += self.q0[p,d,r,s]
                                linexp -= 1
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i and d <= self.instance.DU_p[pp1]['max_stay'] + i -1:
                                        if d < i + self.instance.L_p[pp1]:
                                            linexp -= - self.x[pp1, r, i, d]
                                        elif d >= i + self.instance.L_p[pp1]:
                                            dd1 = i + self.instance.L_p[pp1] - 1
                                            linexp -= - self.x[pp1, r, i, dd1]
                                self.model.addConstr(linexp == 0, name='C7_'+str(p)+'_'+str(d)+'_'+str(r))
        
        ## 约束8 状态转移约束1
        for p in range(1, self.instance.patients+1):
            for r in range(self.instance.rooms):
                if self.instance.R_p[p][r] == 1:
                    for d in range(self.instance.planning_horizon):
                        if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                            for n in range(self.instance.N_pdr[p][d][r]+1):
                                linexp = 0
                                linexp += self.y0[p,d,r,n]
                                p_num = self.instance.B_pdr[p][d][r]                      # 病人p在第d天的决策次序
                                if p_num < self.instance.total_number_of_day[d][r]-1:    # 如果病人p不是当日最后一个需要决策的病人
                                    if n <= self.instance.N_pdr1[p][d][r]:
                                        pp1 = self.instance.P_dr[d][r][p_num+1]['p'] # 病人p的下一个决策病人
                                        for i in range(self.instance.planning_horizon):
                                            if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i and d <= self.instance.DU_p[pp1]['max_stay'] + i -1:
                                                linexp += self.y1[p,d,i,r,n]
                                former_p = self.instance.P_dr[d][r][p_num-1]['p'] # 前一个病人
                                if n <= self.instance.N_pdr[former_p][d][r]:
                                    linexp -= self.y0[former_p,d,r,n]
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1] and d >= i and d <= self.instance.DU_p[p]['max_stay'] + i -1:
                                        ## 当前患者当日不出现
                                        if 1-self.instance.DU_p[p][d - i + 1] > 0:
                                            if n <= self.instance.N_pdr1[former_p][d][r]:
                                                linexp -= self.y1[former_p,d,i,r,n]*(1-self.instance.DU_p[p][d - i + 1])
                                        ## 当前患者当日出现
                                        if self.instance.DU_p[p][d - i + 1] > 0 and n > 0:
                                            linexp -= self.y1[former_p,d,i,r,n-1]*self.instance.DU_p[p][d - i + 1]
                                self.model.addConstr(linexp == 0, name='C8_'+str(p)+'_'+str(d)+'_'+str(r)+'_'+str(n))
                        
        ## 约束9 状态转移约束2
        for p in range(1, self.instance.patients+1):
            for d in range(self.instance.planning_horizon): #self.instance.planning_horizon
                if d >= self.instance.DU_p[p]['min_date'] and d <= self.instance.DU_p[p]['max_date']:
                    for r in range(self.instance.rooms):
                        if self.instance.RT_r[r] == 2 and self.instance.R_p[p][r] == 1:
                            for s in self.instance.S_pdr[p][d][r]:#self.instance.S_pd[p][d]
                                linexp = 0
                                linexp += self.q0[p,d,r,s]
                                p_num = self.instance.B_pdr[p][d][r]
                                if p_num < self.instance.total_number_of_day[d][r]-1:    # 如果病人p不是当日最后一个需要决策的病人
                                    pp1 = self.instance.P_dr[d][r][p_num+1]['p'] # 病人p的下一个决策病人
                                    for i in range(self.instance.planning_horizon):
                                        if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i and d <= self.instance.DU_p[pp1]['max_stay'] + i -1:
                                            linexp += self.q1[p,d,i,r,s]
                                            
                                former_p = self.instance.P_dr[d][r][p_num-1]['p'] # 前一个病人
                                
                                if s in self.instance.S_pdr[former_p][d][r]:
                                    linexp -= self.q0[former_p,d,r,s]
                                
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1] and d >= i and d <= self.instance.DU_p[p]['max_stay'] + i -1:
                                        ## 当前患者当日不出现
                                        if 1-self.instance.DU_p[p][d - i + 1] > 0:
                                            if s in self.instance.S_pdr[former_p][d][r]:
                                                linexp -= self.q1[former_p,d,i,r,s]*(1-self.instance.DU_p[p][d - i + 1])
                                                
                                        ## 当前患者当日出现
                                        if self.instance.DU_p[p][d - i + 1] > 0 and s > 0: # 当前状态不能是空的状态
                                            if s == 1: # 若当前状态是1-M，则前一个状态只能是0-空
                                                s1 = 0 # 状态0是所有患者都有的状态
                                                if self.instance.PG_pg[p][1]: # 若病人p是男
                                                    linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                                s1 = 1
                                                if self.instance.PG_pg[p][1] and s1 in self.instance.S_pdr[former_p][d][r]: # 若病人p是男
                                                    linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                            elif s == 2:
                                                s1 = 0
                                                if self.instance.PG_pg[p][0]:
                                                    linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                                s1 = 2
                                                if self.instance.PG_pg[p][0] and s1 in self.instance.S_pdr[former_p][d][r]: # 若病人p是女
                                                    linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                            elif s == 3:
                                                if self.instance.PG_pg[p][1]: # 若病人p是男，则前一个状态只能是2-女
                                                    s1 = 2
                                                    if s1 in self.instance.S_pdr[former_p][d][r]:
                                                        linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                                elif self.instance.PG_pg[p][0]: # 若病人p是女，则前一个状态只能是1-男
                                                    s1 = 1
                                                    if s1 in self.instance.S_pdr[former_p][d][r]:
                                                        linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                            elif s == 4:
                                                s1 = 4
                                                if s1 in self.instance.S_pdr[former_p][d][r]:
                                                    linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                                s1 =3
                                                if s1 in self.instance.S_pdr[former_p][d][r]:
                                                    linexp -= self.q1[former_p,d,i, r, s1]*self.instance.DU_p[p][d - i + 1]
                                self.model.addConstr(linexp == 0, name='C9_'+str(p)+'_'+str(d)+'_'+str(r)+'_'+str(s))
                                
    
    def Solve(self, time_limit = 0, log_file = '', input_solution = None, deadline = None):
        time_start = time.time()
        self.CreateModel()
        self.TimeToBuildModel = time.time() - time_start
        if deadline is not None:
            time_limit = max(0, deadline - time.monotonic())
        if time_limit > 0:
            self.model.setParam('TimeLimit', time_limit)
        if log_file != '':
            self.model.setParam('LogFile',log_file)
        # self.model.write('sv_model.mps')
        self.model.setParam('Method', 3)
        self.model.setParam('MIPGap', 0.000001)
        
        ## 读取初始解
        if input_solution != None:
            for p in range(1, self.instance.patients+1):
                Ad = input_solution[p]['Admission']
                for d in range(self.instance.planning_horizon):
                    if d >= self.instance.DA_p[p][0] and d <= self.instance.DA_p[p][1]:
                        if d == Ad:
                            self.alpha[p, d].Start = 1
                        else:
                            self.alpha[p, d].Start = 0
            
            for p in range(1, self.instance.patients+1):
                if self.instance.L_p[p] >= 2:
                    i = input_solution[p]['Admission']
                    for d in range(self.instance.planning_horizon):
                        if d > i and d < i + self.instance.L_p[p]:
                            r1 = input_solution[p][d-1]
                            r2 = input_solution[p][d]
                            if r1 != r2:
                                self.t[p, d].Start = 1
                            else:
                                self.t[p, d].Start = 0
                                
            for p in range(1, self.instance.patients+1):
                i1 = input_solution[p]['Admission']
                for i in range(self.instance.planning_horizon):
                    if i >= self.instance.DA_p[p][0] and i <= self.instance.DA_p[p][1]:
                        for d in range(self.instance.planning_horizon):
                            if d >= i and d < i + self.instance.L_p[p]:
                                for r in range(self.instance.rooms):
                                    if self.instance.R_p[p][r] == 1:
                                        self.x[p, r, i, d].Start = int(i1 == i and input_solution[p][d] == r)
                    
        
        if deadline is not None:
            time_limit = deadline - time.monotonic()
            if time_limit <= 0:
                raise TimeoutError('SV time budget expired during model construction')
            self.model.setParam('TimeLimit', time_limit)
        self.model.optimize(RecordTimeToBest)
    
    def output(self, solution, result_file):
        # 保存结果
        with open(result_file, 'w') as file:
            json.dump(solution, file)
    
    def get_assignment(self):
        global TimeToBest
        solution = {}
        if self.model.getAttr('Status') != 3 and self.model.getAttr('SolCount') > 0:
            # 目标值
            solution.update({'Objective':self.model.getObjective().getValue()})
            # 到达最佳目标值的时间
            solution.update({'TimeToBest':TimeToBest})
            # 运行时间
            solution.update({'TimeToEnd':self.model.getAttr('Runtime')})
            # 下界
            solution.update({'LowerBound':self.model.getAttr('ObjBound')})
            # 分枝树的节点数
            solution.update({'NodeCount':self.model.getAttr('NodeCount')})
        else:
            solution.update({'Objective':'-'})
            solution.update({'TimeToBest':'-'})
            solution.update({'TimeToEnd':'-'})
            solution.update({'LowerBound':'-'})
            solution.update({'NodeCount':'-'})
        # 建模时间
        solution.update({'TimeToBuildModel':self.TimeToBuildModel})
        # 获取模型的变量数量
        solution.update({'NumVars':self.model.getAttr('NumVars')})
        # 获取模型的约束数量
        solution.update({'NumConstrs':self.model.getAttr('NumConstrs')})
        
        if self.model.getAttr('Status') != 3 and self.model.getAttr('SolCount') > 0:
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
