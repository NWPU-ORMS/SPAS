# Simulator for the stochastic patient admission scheduling problem
import gurobipy as gp
from gurobipy import GRB
from InstanceGet_SV3 import Instance
import json

class Simulator:
    
    def __init__(self, instance:Instance, solution):
        self.instance = instance
        self.solution = solution
        self.expected_cost = 0
        self.patient_room_cost_regular = 0
        self.patient_cost_trans = 0
        self.delay_cost = 0
        self.total_cost_for_scenario = [0 for i in range(self.instance.scenario)]
        self.room_cost_over = [0 for i in range(self.instance.scenario)]
        self.patient_room_cost_stochastic = [0 for i in range(self.instance.scenario)]
        self.room_cost_gender = [0 for i in range(self.instance.scenario)]
        
        self.patient_room_cost_expected = 0
        self.room_cost_over_expected = 0
        self.room_cost_gender_expected = 0
        
    
     # 采用抽样评估的方法，评估方案的期望成本
    def runTrueScenario2(self,result_file):
        # 计算目标值的各项组成部分
        
        self.result = {
            'delay_per_person':0, 
            'room_gender_per_room_day':0,
            'levels_of_expertise_per_person':0, 
            'preferred_room_capacity_per_person':0,
            'preferred_euipment_per_person':0,
            'patient_trans_per_person':0, 
            'room_over':0,
            'reject_person':0,
            'admitted_person':0,
        }
       
        self.rolling_day = self.solution['rolling_day']
        
        ## 计算延迟入院成本
        patient_to_be_admitted = 0
        for p in range(1, self.instance.patients+1):
            if self.solution[p]['state'] != -1:
                i = self.solution[p]['admission_day']
                # print(i, self.instance.DA_p[p][0], self.rolling_day)
                if i != -1:
                    self.result['delay_per_person'] += i - self.instance.DA_p[p][0]
                    patient_to_be_admitted += 1
                    # print('delay_cost:', self.result['delay_cost'])
                else:
                    if self.instance.DA_p[p][1] <= self.rolling_day:
                        self.result['delay_per_person'] += self.rolling_day - self.instance.DA_p[p][0]
                        self.result['reject_person'] += 1
                        
        self.result['delay_per_person'] = self.result['delay_per_person'] / self.instance.patients
        self.result['admitted_person'] = patient_to_be_admitted
        
        ## 计算患者正常时间内的住房费用
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['admission_day']
            if self.solution[p]['state'] != 0 and i != -1:
                for d in range(self.rolling_day):
                    if d >= i and d < i + self.instance.L_p[p]:
                        r = self.solution[p]['schedule'][d]
                        # self.patient_room_cost_regular += self.instance.C_pr[p][r]
                        
                        ### gender
                        rg = self.instance.Rooms_dict[str(r)]['gender_policy']
                        pg = self.instance.Patients_dict[str(p-1)]['gender']
                        if rg != 'All' or rg != 'SG': 
                            if rg != pg: 
                                self.result['room_gender_per_room_day'] += 1/(self.rolling_day* self.instance.rooms)
                                
                        ### level of expertise
                        sp = self.instance.Patients_dict[str(p-1)]['treatment'] # 疾病类型
                        dep = self.instance.Rooms_dict[str(r)]['dept_index']    # 病房所在科室
                        if sp not in self.instance.Departments_dict[str(dep)]['main_spec']:
                            if sp in self.instance.Departments_dict[str(dep)]['aux_spec']: # soft constraint
                                self.result['levels_of_expertise_per_person'] += 1/ patient_to_be_admitted
                                print("patient:", p, "room:", r, "sp:", sp, "dep:", dep, "main_spec:", self.instance.Departments_dict[str(dep)]['main_spec'], "aux_spec:", self.instance.Departments_dict[str(dep)]['aux_spec'])
                            
                        ### preferred equipment
                        for propertylist in self.instance.Patients_dict[str(p-1)]['room_property_list']:
                            if propertylist == '-':
                                continue
                            property = propertylist[0]
                            need = propertylist[1]
                            if need == 'p':
                                if property not in self.instance.Rooms_dict[str(r)]['features_list']:
                                    self.result['preferred_euipment_per_person'] += 1/ patient_to_be_admitted
                        
                        ### preferred room capacity
                        preferred_capacity = self.instance.Patients_dict[str(p-1)]['preferred_capacity']
                        if preferred_capacity != '*':
                            preferred_capacity = int(preferred_capacity[2:])
                            if preferred_capacity < self.instance.Rooms_dict[str(r)]['capacity']:
                                self.result['preferred_room_capacity_per_person'] += 1/ patient_to_be_admitted
        
        
        ## 计算患者转移费用
        for p in range(1, self.instance.patients+1):
            if self.solution[p]['state'] != 0 and self.instance.L_p[p] >= 2 and self.solution[p]['admission_day'] != -1:
                i = self.solution[p]['admission_day']
                if i != -1:
                    for d in range(self.rolling_day):
                        if d > i and d < i + self.instance.L_p[p]:
                            r1 = self.solution[p]['schedule'][d-1]
                            r2 = self.solution[p]['schedule'][d]
                            if abs(r1 - r2)>0.0001:
                                self.result['patient_trans_per_person'] += 1/patient_to_be_admitted
                                # print(p, d, r1, r2)
        
        ## 与场景相关的费用

        ## 住房费用
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['admission_day']
            if i != -1:
                dd1 = i + self.instance.L_p[p] - 1
                if dd1 < self.rolling_day:
                    r = self.solution[p]['schedule'][dd1]
                    for d in range(self.rolling_day):
                        if d >= i + self.instance.L_p[p] and d < i + self.instance.TL_p[p]:
                            # self.patient_room_cost_stochastic[w] += self.instance.C_pr[p][r]
                            
                            ### gender
                            rg = self.instance.Rooms_dict[str(r)]['gender_policy']
                            pg = self.instance.Patients_dict[str(p-1)]['gender']
                            if rg != 'All' or rg != 'SG': 
                                if rg != pg: 
                                    self.result['room_gender_per_room_day'] += 1/(self.rolling_day* self.instance.rooms)
                            
                            ### level of expertise
                            sp = self.instance.Patients_dict[str(p-1)]['treatment']
                            dep = self.instance.Rooms_dict[str(r)]['dept_index']
                            if sp not in self.instance.Departments_dict[str(dep)]['main_spec'] and sp in self.instance.Departments_dict[str(dep)]['aux_spec']: # soft constraint
                                self.result['levels_of_expertise_per_person'] += 1/ patient_to_be_admitted
                                
                            ### preferred equipment
                            for propertylist in self.instance.Patients_dict[str(p-1)]['room_property_list']:
                                if propertylist == '-':
                                    continue
                                property = propertylist[0]
                                need = propertylist[1]
                                if need == 'p':
                                    if property not in self.instance.Rooms_dict[str(r)]['features_list']:
                                        self.result['preferred_euipment_per_person'] += 1/ patient_to_be_admitted
                            
                            ### preferred room capacity
                            preferred_capacity = self.instance.Patients_dict[str(p-1)]['preferred_capacity']
                            if preferred_capacity != '*':
                                preferred_capacity = int(preferred_capacity[2:])
                                if preferred_capacity < self.instance.Rooms_dict[str(r)]['capacity']:
                                    self.result['preferred_room_capacity_per_person'] += 1/ patient_to_be_admitted
                        
                        
                        
        ## 性别和容量惩罚
        gender_rd = [[[0,0] for d in range(self.rolling_day)] for r in range(self.instance.rooms)] # [0,0]分别表示男生数量和女数量
        number_rd = [[0 for d in range(self.rolling_day)] for r in range(self.instance.rooms)] # 每天每个房间的人数
        
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['admission_day']
            if i != -1:
                for d in range(self.rolling_day):
                    if d >= i and d < i + self.instance.TL_p[p]:
                        if d >= i and d < i + self.instance.L_p[p]:
                            r = self.solution[p]['schedule'][d]
                        elif d >= i + self.instance.L_p[p] and d < i + self.instance.TL_p[p]:
                            dd1 = i + self.instance.L_p[p] - 1
                            r = self.solution[p]['schedule'][dd1]
                        
                        number_rd[r][d] += 1
                        
                        if self.instance.PG_pg[p][0] == 1: # 男生
                            gender_rd[r][d][0] += 1
                        else:
                            gender_rd[r][d][1] += 1
        
        for r in range(self.instance.rooms):
            for d in range(self.rolling_day):
                over_capacity = number_rd[r][d] - self.instance.Q_r[r] # 超过容量的人数
                if over_capacity > 0:
                    # self.room_cost_over[w] += over_capacity * self.instance.W_op
                    self.result['room_over'] += over_capacity
                    
                    
                if self.instance.RT_r[r] == 2: # 独立房间
                    if gender_rd[r][d][0] > 0 and gender_rd[r][d][1] > 0:
                        # self.room_cost_gender[w] += self.instance.W_RG
                        self.result['room_gender_per_room_day'] += 1/(self.rolling_day* self.instance.rooms)
                            
            
        with open(result_file, 'w') as file:
            json.dump(self.result, file)
    
    # 采用抽样评估的方法，评估方案的期望成本
    def runTrueScenario(self,result_file):
        # 计算目标值的各项组成部分
        
        self.result = {
            'total_cost': 0, 
            'delay_cost':0, 
            'room_cost_gender':0,
            'levels_of_expertise':0, 
            'preferred_room_capacity':0,
            'preferred_euipment':0,
            'patient_cost_trans':0, 
            'room_cost_over':0
        }
       
        self.rolling_day = self.solution['rolling_day']
        
        ## 计算延迟入院成本
        for p in range(1, self.instance.patients+1):
            if self.solution[p]['state'] != -1:
                i = self.solution[p]['admission_day']
                # print(i, self.instance.DA_p[p][0], self.rolling_day)
                if i != -1:
                    self.result['delay_cost'] += self.instance.W_DE  * (i - self.instance.DA_p[p][0])
                    # print('delay_cost:', self.result['delay_cost'])
                else:
                    if self.instance.DA_p[p][1] <= self.rolling_day: # 已经超过最大延迟时间
                        self.result['delay_cost'] += self.instance.W_DE1  * (self.rolling_day - self.instance.DA_p[p][0])
        
        ## 计算患者正常时间内的住房费用
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['admission_day']
            if self.solution[p]['state'] != 0 and i != -1:
                for d in range(self.rolling_day):
                    if d >= i and d < i + self.instance.L_p[p]:
                        r = self.solution[p]['schedule'][d]
                        # self.patient_room_cost_regular += self.instance.C_pr[p][r]
                        
                        ### gender
                        rg = self.instance.Rooms_dict[str(r)]['gender_policy']
                        pg = self.instance.Patients_dict[str(p-1)]['gender']
                        if rg != 'All' or rg != 'SG': 
                            if rg != pg: 
                                self.result['room_cost_gender'] += self.instance.W_RG
                        
                        ### level of expertise
                        sp = self.instance.Patients_dict[str(p-1)]['treatment']
                        dep = self.instance.Rooms_dict[str(r)]['dept_index']
                        if sp not in self.instance.Departments_dict[str(dep)]['main_spec'] and sp in self.instance.Departments_dict[str(dep)]['aux_spec']: # soft constraint
                            self.result['levels_of_expertise'] += self.instance.W_SP
                            
                        ### preferred equipment
                        for propertylist in self.instance.Patients_dict[str(p-1)]['room_property_list']:
                            if propertylist == '-':
                                continue
                            property = propertylist[0]
                            need = propertylist[1]
                            if need == 'p':
                                if property not in self.instance.Rooms_dict[str(r)]['features_list']:
                                    self.result['preferred_euipment'] += self.instance.W_PE
                        
                        ### preferred room capacity
                        preferred_capacity = self.instance.Patients_dict[str(p-1)]['preferred_capacity']
                        if preferred_capacity != '*':
                            preferred_capacity = int(preferred_capacity[2:])
                            if preferred_capacity < self.instance.Rooms_dict[str(r)]['capacity']:
                                self.result['preferred_room_capacity'] += self.instance.W_RC
        
        ## 计算患者转移费用
        for p in range(1, self.instance.patients+1):
            if self.solution[p]['state'] != 0 and self.instance.L_p[p] >= 2:
                i = self.solution[p]['admission_day']
                if i != -1:
                    for d in range(self.rolling_day):
                        if d > i and d < i + self.instance.L_p[p]:
                            r1 = self.solution[p]['schedule'][d-1]
                            r2 = self.solution[p]['schedule'][d]
                            if r1 != r2:
                                self.result['patient_cost_trans'] += self.instance.W_tr
                                # print(p, d, r1, r2)
        
        ## 与场景相关的费用

        ## 住房费用
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['admission_day']
            if i != -1:
                dd1 = i + self.instance.L_p[p] - 1
                if dd1 < self.rolling_day:
                    r = self.solution[p]['schedule'][dd1]
                    for d in range(self.rolling_day):
                        if d >= i + self.instance.L_p[p] and d < i + self.instance.TL_p[p]:
                            # self.patient_room_cost_stochastic[w] += self.instance.C_pr[p][r]
                            
                            ### gender
                            rg = self.instance.Rooms_dict[str(r)]['gender_policy']
                            pg = self.instance.Patients_dict[str(p-1)]['gender']
                            if rg != 'All' or rg != 'SG': 
                                if rg != pg: 
                                    self.result['room_cost_gender'] += self.instance.W_RG
                            
                            ### level of expertise
                            sp = self.instance.Patients_dict[str(p-1)]['treatment']
                            dep = self.instance.Rooms_dict[str(r)]['dept_index']
                            if sp not in self.instance.Departments_dict[str(dep)]['main_spec'] and sp in self.instance.Departments_dict[str(dep)]['aux_spec']: # soft constraint
                                self.result['levels_of_expertise'] += self.instance.W_SP
                                
                            ### preferred equipment
                            for propertylist in self.instance.Patients_dict[str(p-1)]['room_property_list']:
                                if propertylist == '-':
                                    continue
                                property = propertylist[0]
                                need = propertylist[1]
                                if need == 'p':
                                    if property not in self.instance.Rooms_dict[str(r)]['features_list']:
                                        self.result['preferred_euipment'] += self.instance.W_PE
                            
                            ### preferred room capacity
                            preferred_capacity = self.instance.Patients_dict[str(p-1)]['preferred_capacity']
                            if preferred_capacity != '*':
                                preferred_capacity = int(preferred_capacity[2:])
                                if preferred_capacity < self.instance.Rooms_dict[str(r)]['capacity']:
                                    self.result['preferred_room_capacity'] += self.instance.W_RC
                        
                        
                        
        ## 性别和容量惩罚
        gender_rd = [[[0,0] for d in range(self.rolling_day)] for r in range(self.instance.rooms)] # [0,0]分别表示男生数量和女数量
        number_rd = [[0 for d in range(self.rolling_day)] for r in range(self.instance.rooms)] # 每天每个房间的人数
        
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['admission_day']
            if i != -1:
                for d in range(self.rolling_day):
                    if d >= i and d < i + self.instance.TL_p[p]:
                        if d >= i and d < i + self.instance.L_p[p]:
                            r = self.solution[p]['schedule'][d]
                        elif d >= i + self.instance.L_p[p] and d < i + self.instance.TL_p[p]:
                            dd1 = i + self.instance.L_p[p] - 1
                            r = self.solution[p]['schedule'][dd1]
                        
                        number_rd[r][d] += 1
                        
                        if self.instance.PG_pg[p][0] == 1: # 男生
                            gender_rd[r][d][0] += 1
                        else:
                            gender_rd[r][d][1] += 1
        
        for r in range(self.instance.rooms):
            for d in range(self.rolling_day):
                over_capacity = number_rd[r][d] - self.instance.Q_r[r] # 超过容量的人数
                if over_capacity > 0:
                    # self.room_cost_over[w] += over_capacity * self.instance.W_op
                    self.result['room_cost_over'] += over_capacity * self.instance.W_op
                if self.instance.RT_r[r] == 2: # 独立房间
                    if gender_rd[r][d][0] > 0 and gender_rd[r][d][1] > 0:
                        # self.room_cost_gender[w] += self.instance.W_RG
                        self.result['room_cost_gender'] += self.instance.W_RG
        
        ## 总费用
        self.result['total_cost'] = self.result['delay_cost'] + self.result['room_cost_gender'] + self.result['levels_of_expertise']+ self.result['preferred_room_capacity']+ self.result['preferred_euipment']+ self.result['patient_cost_trans']+ self.result['room_cost_over']
            
        with open(result_file, 'w') as file:
            json.dump(self.result, file)
    
    ## 采用状态变量的方法，评估方案的期望成本
    def runLargeScaleApproximate(self):
        # 计算目标值的各项组成部分
        ## 计算延迟入院成本
        for p in range(1, self.instance.patients+1):
            d = self.solution[p]['Admission']
            if d == -1:
                self.delay_cost += self.instance.W_DE*1000  * (self.instance.planning_horizon - self.instance.DA_p[p][0]+ self.instance.delay[p])
            else:
                self.delay_cost += self.instance.W_DE  * (d - self.instance.DA_p[p][0]+ self.instance.delay[p])
        
        ## 计算患者正常时间内的住房费用
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['Admission']
            if i != -1:
                for d in range(self.instance.planning_horizon):
                    if d >= i and d < i + self.instance.L_p[p]:
                        r = self.solution[p][d]
                        self.patient_room_cost_regular += self.instance.C_pr[p][r]
        
        ## 计算患者转移费用
        for p in range(1, self.instance.patients+1):
            if self.instance.L_p[p] >= 2:
                i = self.solution[p]['Admission']
                if i != -1:
                    for d in range(self.instance.planning_horizon):
                        if d > i and d < i + self.instance.L_p[p]:
                            r1 = self.solution[p][d-1]
                            r2 = self.solution[p][d]
                            if r1 != r2:
                                self.patient_cost_trans += self.instance.W_tr
        
        for p in range(1, self.instance.patients+1):
            if self.instance.patient_state[p] == 1:
                r1 = self.instance.patient_room_last_day[p]
                r2 = self.solution[p][0]
                if r1 != r2:
                    self.patient_cost_trans += self.instance.W_tr

        
        ## 与期望场景相关的费用
        ## 住房费用
        for p in range(1, self.instance.patients+1):
            i = self.solution[p]['Admission']
            if i != -1:
                if self.instance.patient_state[p] == 2:
                    r = self.instance.patient_room_last_day[p]
                    for d in range(self.instance.planning_horizon):
                        if d >= i + self.instance.L_p[p] and d <= i + self.instance.DU_p[p]['max_stay'] - 1:
                            self.patient_room_cost_expected += self.instance.DU_p[p][d - i + 1] * self.instance.C_pr[p][r]
                elif self.instance.patient_state[p] == 0 or self.instance.patient_state[p] == 1:
                    dd1 = i + self.instance.L_p[p] - 1
                    for d in range(self.instance.planning_horizon):
                        if d >= i + self.instance.L_p[p] and d <= i + self.instance.DU_p[p]['max_stay'] - 1:
                            r = self.solution[p][dd1]
                            self.patient_room_cost_expected += self.instance.DU_p[p][d - i + 1] * self.instance.C_pr[p][r]
        
        ## 性别和容量惩罚
        self.StateVariable()
        
        ## 总费用
        if self.model.getAttr("Status") != 3:
            self.expected_cost = self.delay_cost + self.patient_room_cost_regular  + self.patient_cost_trans + self.patient_room_cost_expected + self.room_cost_gender_expected + self.room_cost_over_expected
        else:
            self.expected_cost = 'NA'
            print('Infeasible Model')
    
    
    def StateVariable(self):
        self.model = gp.Model("PRAU2_SV")
        
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
                                i1 = self.solution[pp1]['Admission']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i  and d <= self.instance.DU_p[pp1]['max_stay'] + i -1 :
                                        linexp = 0
                                        x_value = 0
                                        
                                        for n in range(self.instance.N_pdr1[p][d][r]+1):
                                            linexp += self.y1[p,d,i,r,n]
                                        
                                        if i == i1:
                                            # 判断病房
                                            if self.instance.patient_state[pp1] == 0 or self.instance.patient_state[pp1] == 1:
                                                if d < i + self.instance.L_p[pp1]:
                                                    dd1 = d
                                                elif d >= i + self.instance.L_p[pp1]:
                                                    dd1 = i + self.instance.L_p[pp1] - 1

                                                r1 = self.solution[pp1][dd1]
                                            elif self.instance.patient_state[pp1] == 2:
                                                r1 = self.instance.patient_room_last_day[pp1]

                                            if r == r1:
                                                x_value = 1
                                        
                                        linexp -= x_value
                                        
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
                                i1 = self.solution[pp1]['Admission']

                                linexp = 0
                                x_value = 0
                                for n in range(self.instance.N_pdr[p][d][r]+1):
                                    linexp += self.y0[p,d,r,n]
                                linexp -= 1
                                
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i and d <= self.instance.DU_p[pp1]['max_stay'] + i -1:
                                        if i == i1:
                                            if self.instance.patient_state[pp1] == 0 or self.instance.patient_state[pp1] == 1:
                                                if d < i + self.instance.L_p[pp1]:
                                                    dd1 = d
                                                elif d >= i + self.instance.L_p[pp1]:
                                                    dd1 = i + self.instance.L_p[pp1] - 1
                                                r1 = self.solution[pp1][dd1]
                                            elif self.instance.patient_state[pp1] == 2:
                                                r1 = self.instance.patient_room_last_day[pp1]
                                            
                                            if r == r1:
                                                x_value = 1
                                                
                                linexp -= - x_value
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
                                i1 = self.solution[pp1]['Admission']
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i  and d <= self.instance.DU_p[pp1]['max_stay'] + i -1 :
                                        
                                        linexp = 0
                                        x_value = 0
                                        for s in self.instance.S_pdr[p][d][r]:
                                            linexp += self.q1[p,d,i,r,s]
                                            
                                        if i == i1:
                                            # 判断病房
                                            if self.instance.patient_state[pp1] == 0 or self.instance.patient_state[pp1] == 1:
                                                if d < i + self.instance.L_p[pp1]:
                                                    dd1 = d
                                                elif d >= i + self.instance.L_p[pp1]:
                                                    dd1 = i + self.instance.L_p[pp1] - 1

                                                r1 = self.solution[pp1][dd1]
                                            elif self.instance.patient_state[pp1] == 2:
                                                r1 = self.instance.patient_room_last_day[pp1]

                                            if r == r1:
                                                x_value = 1
                                            
                                        linexp -= x_value
                                        
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
                                i1 = self.solution[pp1]['Admission']

                                linexp = 0
                                for s in self.instance.S_pdr[p][d][r]:
                                    linexp += self.q0[p,d,r,s]
                                linexp -= 1
                                x_value = 0
                                for i in range(self.instance.planning_horizon):
                                    if i >= self.instance.DA_p[pp1][0] and i <= self.instance.DA_p[pp1][1] and d >= i and d <= self.instance.DU_p[pp1]['max_stay'] + i -1:
                                        if i == i1:
                                            if self.instance.patient_state[pp1] == 0 or self.instance.patient_state[pp1] == 1:
                                                if d < i + self.instance.L_p[pp1]:
                                                    dd1 = d
                                                elif d >= i + self.instance.L_p[pp1]:
                                                    dd1 = i + self.instance.L_p[pp1] - 1
                                                r1 = self.solution[pp1][dd1]
                                            elif self.instance.patient_state[pp1] == 2:
                                                r1 = self.instance.patient_room_last_day[pp1]
                                            
                                            if r == r1:
                                                x_value = 1
                                                
                                linexp -= - x_value
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
                                p_num = self.instance.B_pdr[p][d][r]                         # 病人p在第d天的决策次序
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
                                self.model.addConstr(linexp == 0, name='C6_'+str(p)+'_'+str(d)+'_'+str(r)+'_'+str(n))
                        
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
                                
        self.model.setParam('OutputFlag', 0)
        self.model.optimize()
        
        if self.model.getAttr("Status") != 3:

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
                                                self.room_cost_over_expected += self.instance.W_pdirn[p][d][i][r][n] * self.y1[p,d,i,r,n].x
            
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
                                                self.room_cost_gender_expected += self.instance.W_pdirs[p][d][i][r][s] * self.q1[p,d,i,r,s].x
                        