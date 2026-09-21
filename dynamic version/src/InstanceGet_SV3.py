import numpy as np
import os
import json

def find_combinations(num_patients, current_combination, all_combinations, index):
    # 递归基案例：如果已处理所有病人，将当前组合添加到所有组合中
    if index == num_patients:
        all_combinations.append(current_combination.copy())
        return
    
    # 决策1: 当前病人出现 (将对应位置设为1)
    current_combination[index] = 1
    find_combinations(num_patients, current_combination, all_combinations,  index + 1)

    # 决策2: 当前病人不出现 (将对应位置设为0)
    current_combination[index] = 0
    find_combinations(num_patients, current_combination, all_combinations, index + 1)

class Instance:
    
    def __init__(self, path, in_DE1 = 10000, in_Tr = 100, in_OP = 1000):
        # 读取 profile.txt 文件内容
        with open(path+'profile.txt', 'r') as f:
            lines = f.readlines()

        # 初始化变量
        self.rooms = 0
        self.patients = 0
        self.planning_horizon = 0
        self.scenario = 0
        if in_OP >0:
            self.W_op = in_OP
        else:
            self.W_op = 0
        self.W_RG = 50
        self.W_tr = in_Tr
        self.W_DE = 2
        self.max_Over = 1
        self.path = path
        self.W_SP = 20
        self.W_PE = 20
        self.W_RC = 10
        self.W_DE1 = in_DE1
        

        # 解析每一行
        for line in lines:
            if 'Rooms:' in line:
                self.rooms = int(line.split(":")[1].strip())
            elif 'Patients:' in line:
                self.patients = int(line.split(":")[1].strip())
            elif 'Planning horizon:' in line:
                self.planning_horizon = int(line.split(":")[1].strip())
            elif 'Scenario size' in line:
                self.scenario = int(line.split(":")[1].strip())
        
        if os.path.exists(path + 'Patients_dict.txt'):
            with open(path+'Patients_dict.txt', 'r') as file:
                self.Patients_dict = json.load(file)
            with open(path+'Rooms_dict.txt', 'r') as file:
                self.Rooms_dict = json.load(file)
            with open(path+'Departments_dict.txt', 'r') as file:
                self.Departments_dict = json.load(file)
        
        # # B_r
        # self.B_r = []
        # with open(path+'B_r.txt', 'r') as f:
        #     for line in f:
        #         row = line.strip().split("\t")
        #         row = list(map(int, row))
        #         self.B_r.append(row)
        
        # C_pr
        self.C_pr = np.zeros((self.patients+1, self.rooms))
        with open(path+'C_pr.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    # row = list(map(int, row))
                    p = int(row[0])
                    r = int(row[1])
                    c_pr = float(row[2])
                    self.C_pr[p][r-1] = c_pr
        
        # D_p
        self.L_p = [0]
        with open(path + 'L_p.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    row = list(map(int, row))
                    self.L_p.append(row[1])
                
        # RG_rg
        self.RG_rg = []
        with open(path + 'RG_rg.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    row = list(map(int, row))
                    self.RG_rg.append(row[1:])
        
        # PG_pg
        self.PG_pg = [[0, 0]]
        with open(path + 'PG_pg.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    row = list(map(int, row))
                    self.PG_pg.append(row[1:])
        
        # R_p
        self.R_p = [[0 for r in range(self.rooms)] for p in range(self.patients+1)]
        with open(path + 'R_p.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    p = int(row[0])
                    r = int(row[1])
                    value = int(row[2])
                    # print(p, r, value)
                    self.R_p[p][r-1] = value
        
        for r in range(self.rooms): # 虚拟病人可以去任何一个房间
            self.R_p[0][r] = 1
        
        # RT 1-depentent, 2-indepentent
        self.RT_r = []
        with open(path + 'RT_r.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    row = list(map(int, row))
                    self.RT_r.append(row[1])
                
        # Q_r
        self.Q_r = []
        with open(path + 'Q_r.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    row = list(map(int, row))
                    self.Q_r.append(row[1])
                
        
        # 不同场景下患者离院时间
        self.L_ps = [[]]
        with open(path + 'L_pu.txt', 'r') as f:
            for line in f:
                row = line.strip().split("\t")
                row = list(map(int, row))
                self.L_ps.append(row)
        
        # DA_p 患者入院时间
        self.DA_p = [[]]
        with open(path + 'DA_p.txt', 'r') as f:
            for i, line in enumerate(f):
                if i > 0:
                    row = line.strip().split("\t")
                    row = list(map(int, row))
                    self.DA_p.append(row[1:])
                    
        # 患者目前已经推迟的入院时长
        self.delay = [[]]
        if os.path.exists(path + 'true_earliest_admission_day.txt'):
            with open(path+'true_earliest_admission_day.txt', 'r') as f:
                for i, line in enumerate(f):
                    if i > 0:
                        row = line.strip().split("\t")
                        row = list(map(int, row))
                        self.delay.append(row[1])
                    
        # Regist_p 患者的注册时间
        self.Regist_p = [[]]
        if os.path.exists(path + 'Regist_p.txt'):
            with open(path + 'Regist_p.txt', 'r') as f:
                for i, line in enumerate(f):
                    if i > 0:
                        row = line.strip().split("\t")
                        row = list(map(int, row))
                        self.Regist_p.append(row[1:])
        
        # TL_p 患者的实际住院天数
        self.TL_p = [[]]
        if os.path.exists(path + 'Actual_length_p.txt'):
            with open(path + 'Actual_length_p.txt', 'r') as f:
                for i, line in enumerate(f):
                    if i > 0:
                        row = line.strip().split("\t")
                        row = list(map(int, row))
                        self.TL_p.append(row[1])
        
        # patient_state
        self.patient_state = [[]]
        if os.path.exists(path + 'patient_state.txt'):
            with open(path + 'patient_state.txt', 'r') as f:
                for i, line in enumerate(f):
                    if i > 0:
                        row = line.strip().split("\t")
                        row = list(map(int, row))
                        self.patient_state.append(row[1])
                        
        # patient_room_last_day
        self.patient_room_last_day = [[]]
        if os.path.exists(path + 'patient_room_last_day.txt'):
            with open(path + 'patient_room_last_day.txt', 'r') as f:
                for i, line in enumerate(f):
                    if i > 0:
                        row = line.strip().split("\t")
                        row = list(map(int, row))
                        self.patient_room_last_day.append(row[1])
        
        if os.path.exists(path + 'L_put.txt'):
        
            # DU_p 显示各病人出现在医院的概率
            ## DU_p[p][d] 表示病人p持续第d天出现在医院的概率
            ## DU_p[p]['max_date'] 表示病人p在医院出现的最晚日期, 后一天就出院
            ## DU_p[p]['min_date'] 表示病人p在医院出现的最早日期
            self.DU_p = [{} for p in range(self.patients+1)]
            p_flag = 1
            back_d = 0
            with open(path + 'L_put.txt', 'r') as f:
                for i, line in enumerate(f):
                    if i > 0:
                        row = line.strip().split("\t")
                        # print(row)
                        row1 = list(map(int, row[0:2]))
                        # print(row1)
                        row1.append(float(row[2]))
                        p = row1[0]
                        # print(row1)
                        self.DU_p[p].update({row1[1]:row1[2]})
                        if p == p_flag:
                            back_d = row1[1]
                        else:
                            self.DU_p[p_flag].update({'max_date':back_d+self.DA_p[p_flag][1] - 1})
                            self.DU_p[p_flag].update({'min_date':self.DA_p[p_flag][0]})
                            self.DU_p[p_flag].update({'max_stay':back_d})
                            p_flag = p
                            back_d = row1[1]
            back_d = row1[1]
            self.DU_p[p].update({'max_date':back_d + self.DA_p[p][1] - 1})
            self.DU_p[p].update({'min_date':self.DA_p[p][0]})
            self.DU_p[p].update({'max_stay':back_d})
            
            # print("back_d:", back_d, "DA_p[p][1]:", self.DA_p[p][1], "p:", p)
            
            
            ## 配置虚拟病人的信息
            min_date = 1E6
            max_date = 0
            for p in range(1, self.patients+1):
                if self.DU_p[p]['min_date'] < min_date:
                    min_date = self.DU_p[p]['min_date']
                if self.DU_p[p]['max_date'] > max_date:
                    max_date = self.DU_p[p]['max_date']
            for d in range(min_date, max_date+1):
                self.DU_p[0].update({d:1})
            self.DU_p[0].update({'max_date':max_date})
            self.DU_p[0].update({'min_date':min_date})
            
            ## total_number_of_day 用于记录每天需要安排的病人数
            self.total_number_of_day = [[0 for r in range(self.rooms)] for d in range(self.planning_horizon)]
            
            # P_dr 用于标记各天病人的决策次序
            ## P_dr[d][r][n]['p'] 表示第d天第n个决策的病人编号
            ## P_dr[d][r][n]['num'] 表示第d天第n个决策的编号
            self.P_dr = [[[] for r in range(self.rooms)] for d in range(self.planning_horizon)]
            for p in range(self.patients+1):
                for r in range(self.rooms):
                    if self.R_p[p][r] == 1:
                        for d in range(self.DU_p[p]['min_date'], self.DU_p[p]['max_date']+1):
                            if d < self.planning_horizon:
                                self.P_dr[d][r].append({'p':p,'num':self.total_number_of_day[d][r]})
                                self.total_number_of_day[d][r] += 1
                        
            # N_pdr
            ## N_pdr[p][d][r] 表示病人p在第d天第r个房间的最大的安排编号
            ## N_pdr1[p][d][r] 表示病人p在第d天第r个房间的最大的安排编号-1
            self.N_pdr = [{}for p in range(self.patients+1)]
            self.N_pdr1 = [{}for p in range(self.patients+1)]
            for p in range(self.patients+1):
                if p == 0:
                    for d in range(self.DU_p[p]['min_date'], self.DU_p[p]['max_date']+1):
                        if d < self.planning_horizon:
                            if d not in self.N_pdr[p].keys():
                                self.N_pdr[p].update({d:[]})
                                self.N_pdr1[p].update({d:[]})
                            for r in range(self.rooms):
                                self.N_pdr[p][d].append(0)
                                self.N_pdr1[p][d].append(0)
                else:
                    for d in range(self.DU_p[p]['min_date'], self.DU_p[p]['max_date']+1):
                        if d < self.planning_horizon:
                            if d not in self.N_pdr[p].keys():
                                self.N_pdr[p].update({d:{}})
                                self.N_pdr1[p].update({d:{}})
                            for r in range(self.rooms):
                                if self.R_p[p][r] == 1:
                                    for n in range(self.total_number_of_day[d][r]):
                                        if self.P_dr[d][r][n]['p'] == p:
                                            nv1 = n
                                            break
                                    self.N_pdr[p][d].update({r:min(nv1, 2* self.Q_r[r])})
                                    self.N_pdr1[p][d].update({r:min(nv1, 2*self.Q_r[r]-1)})
                                
            # B_pdr 病人p在第d天第r个病房的决策次序
            self.B_pdr = [{} for p in range(self.patients+1)]
            for d in range(self.planning_horizon):
                for r in range(self.rooms):
                    if self.total_number_of_day[d][r] > 0:
                        for n in range(self.total_number_of_day[d][r]):
                            p = self.P_dr[d][r][n]['p']
                            if d not in self.B_pdr[p].keys():
                                self.B_pdr[p].update({d:{}})
                            self.B_pdr[p][d].update({r:n})
                        
            # W_prdn SV模型的目标系数
            ## W_pdrn[p][d][r][n] 表示安排病人p+1在第d天第r个房间的第n+1个位置的目标系数
            ## 注意p不能=当日的最后一个病人
            
            
            self.W_pdirn = [{} for p in range(self.patients)]
            for p in range(self.patients):
                for r in range(self.rooms):
                    if self.R_p[p][r] == 1:
                        for d in range(self.DU_p[p]['min_date'], self.DU_p[p]['max_date']+1):
                            if d < self.planning_horizon:
                                num_d = self.total_number_of_day[d][r] # 当日的病人数
                                p_num = self.B_pdr[p][d][r]             # 病人p在第d天病房r的决策次序
                                if p_num < num_d-1:                # 如果病人p不是病房r当日的最后一个病人
                                    pp1 = self.P_dr[d][r][p_num+1]['p']
                                    for i in range(self.planning_horizon):
                                        if i >= self.DA_p[pp1][0] and i <= d and self.DU_p[pp1]['max_stay'] >= d-i + 1:
                                            if d not in self.W_pdirn[p].keys():
                                                self.W_pdirn[p].update({d:{}})
                                            if i not in self.W_pdirn[p][d].keys():
                                                self.W_pdirn[p][d].update({i:{}})
                                            if r not in self.W_pdirn[p][d][i].keys():
                                                self.W_pdirn[p][d][i].update({r:[]})
                                            for n in range(self.N_pdr1[p][d][r]+1):  # 这里需要考虑给pp1预留位置，所以需要N_pdr1
                                                # print(self.DU_p[25])
                                                # print("n:", n, "pp1:", pp1, "d:", d, "i:", i, "r:", r)
                                                # print(self.DU_p)
                                                # print(self.DU_p[pp1][d - i + 1], d, i, r, self.Q_r[r])
                                                # print("pp1:", pp1, "d-i+1:", d-i+1)
                                                # print(self.DU_p[pp1])
                                                nv = self.DU_p[pp1][d - i + 1] * self.W_op * max(0, n + 1 - max(n, self.Q_r[r])) # 计算pp1的影响
                                                self.W_pdirn[p][d][i][r].append(nv)
                                            
                                            
            self.S_pdr = [{} for p in range(self.patients+1)]
            for r in range(self.rooms):
                for d in range(self.planning_horizon):
                    if self.total_number_of_day[d][r] > 0:  
                        male = 0 # 当日男性病人数
                        female = 0 # 当日女性病人数
                        for n in range(self.total_number_of_day[d][r]):
                            p = self.P_dr[d][r][n]['p']
                            if d not in self.S_pdr[p].keys():
                                self.S_pdr[p].update({d:{}})
                                
                            if p == 0:
                                self.S_pdr[p][d].update({r:[0]})
                            else:
                                if self.PG_pg[p][1] == 1: # 如果是男性
                                    if female == 0:
                                        self.S_pdr[p][d].update({r:[0,1]})
                                    elif female > 0 and male == 0:
                                        self.S_pdr[p][d].update({r:[0,1,2,3]})
                                    elif female >0 and male >0:
                                        self.S_pdr[p][d].update({r:[0,1,2,3,4]})
                                    male += 1
                                else: # 如果是女性
                                    if male == 0:
                                        self.S_pdr[p][d].update({r:[0,2]})
                                    elif male > 0 and female == 0:
                                        self.S_pdr[p][d].update({r:[0,1,2,3]})
                                    elif female >0 and male >0:
                                        self.S_pdr[p][d].update({r:[0,1,2,3,4]})
                                    female += 1
            
            self.W_pdirs = [{} for p in range(self.patients)]
            for p in range(self.patients):
                for r in range(self.rooms):
                    if self.R_p[p][r] == 1:
                        for d in range(self.DU_p[p]['min_date'], self.DU_p[p]['max_date']+1):
                            if d < self.planning_horizon:
                                num_d = self.total_number_of_day[d][r] # 当日的病人数
                                p_num = self.B_pdr[p][d][r]             # 病人p在第d天的决策次序
                                if p_num < num_d-1:                # 如果病人p不是当日的最后一个病人
                                    pp1 = self.P_dr[d][r][p_num+1]['p']
                                    for i in range(self.planning_horizon):
                                        if i >= self.DA_p[pp1][0] and i <= d and self.DU_p[pp1]['max_stay'] >= d-i + 1:
                                            if d not in self.W_pdirs[p].keys():
                                                self.W_pdirs[p].update({d:{}})
                                            if i not in self.W_pdirs[p][d].keys():
                                                self.W_pdirs[p][d].update({i:{}})
                                            if r not in self.W_pdirs[p][d][i].keys():
                                                self.W_pdirs[p][d][i].update({r:{}})
                                            for s in self.S_pdr[p][d][r]:
                                                if s == 1 and self.PG_pg[pp1][0] == 1: # 如果房间性别为男，且下一个病人为女
                                                    nv = self.W_RG * self.DU_p[pp1][d -i + 1]
                                                elif s == 2 and self.PG_pg[pp1][1] == 1: # 如果房间性别为女，且下一个病人为男
                                                    nv = self.W_RG * self.DU_p[pp1][d -i + 1]
                                                else:
                                                    nv = 0
                                                self.W_pdirs[p][d][i][r].update({s:nv})
            
        


