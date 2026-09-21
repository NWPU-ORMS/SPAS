from InstanceGet_SV3 import Instance
import os
import time
from PRAUWT3_SB import PRAUWT_SB
from PRAU3_SV2 import PRAU2_SV
from Simulator3 import Simulator as TSim
import shutil
import json


def remaining(deadline):
    return max(0.0, deadline - time.monotonic())


def fix_first_stage(solver, solution):
    """Fix admission, room assignments, and transfer decisions to a SAA plan."""
    for (p, d), var in solver.alpha.items():
        admission = solution[p]['Admission']
        var.LB = var.UB = int(admission != -1 and d == admission)
    for p, var in solver.alpha2.items():
        var.LB = var.UB = int(solution[p]['Admission'] == -1)
    for (p, r, i, d), var in solver.x.items():
        if solver.instance.patient_state[p] == 2:
            value = int(i == 0 and r == solver.instance.patient_room_last_day[p])
        else:
            admission = solution[p]['Admission']
            value = int(admission != -1 and i == admission and solution[p].get(d) == r)
        var.LB = var.UB = value
    for (p, d), var in solver.t.items():
        admission = solution[p]['Admission']
        if admission == -1:
            value = 0
        else:
            value = int(admission < d < admission + solver.instance.L_p[p]
                        and solution[p].get(d - 1) != solution[p].get(d)
                        and solution[p].get(d - 1) is not None
                        and solution[p].get(d) is not None)
        var.LB = var.UB = value
    for p, var in solver.t0.items():
        r0 = solution[p].get(0)
        r1 = solver.instance.patient_room_last_day[p]
        var.LB = var.UB = int(r0 is not None and r0 != r1)


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
    
class RPO:
    
    def __init__(self, instance:Instance, time_limit, rolling_day = -1, result_path = "", log_path = ""):
        self.instance = instance # 实例
        self.ins4Today = []  #每次 SAA_SV 求解的实例
        self.TimeToBuildModel = 0
        self.solution = []
        self.time_limit = time_limit #每一轮求解的时间限制
        self.rolling_day = rolling_day # 当前的滚动日期
        self.planning_window = 14 # 规划窗口
        self.patient_state = {}     #记录病人状态 
        # patient_state = {p:{
            # 'admission_day':AD,                 # 入院时间
            # 'fix_los_end':AD+length-1,          # 固定住院结束日期
            # 'discharge_day':AD+actual_length,   # 出院时间
            # 'state':N,                          # 病人状态 -1-未注册 0-未入院，已注册 1-可安排，未离院 2-不可安排，未离院  3-已离院
            # 'schedule':[]},                     # 入院后每天的安排情况
            # ...}
        self.Patient_list_now = []  # 当前病人列表 第一列表示重排后的病人编号，第二列表示原始病人编号
        self.init_patient_state() # 初始化病人状态
        self.result_path = result_path # 结果保存路径
        self.log_path = log_path # 日志保存路径
        
    def init_patient_state(self):
        # 初始化所有病人状态，全体患者
        for p in range(1, self.instance.patients+1):
            self.patient_state[p]={
                'admission_day':-1, 
                'fix_los_end':-1, 
                'discharge_day':-1, 
                'state':-1, 
                'schedule':{}, 
                'regist_day': self.instance.Regist_p[p][0],
                'earliest_admission_day': self.instance.DA_p[p][0],
                'latest_admission_day':self.instance.DA_p[p][1],
                }
        self.patient_room_last_day = [-1 for p in range(self.instance.patients+1)]
            
        
            
    def update_patient_state_before(self):
        # 每天运行开始前，根据系统运行时间推进，更新新增的病人状态
        for p in range(1, self.instance.patients+1):
            if self.patient_state[p]['state'] == -1 and self.instance.Regist_p[p][0] <= self.rolling_day and self.instance.DA_p[p][0]-self.rolling_day < self.planning_window:
                # 未注册
                self.patient_state[p]['state'] = 0 #更新为未入院，已注册
                # 对于self.patient_state[p]['state'] == -1的患者，后续需要更新其DA_p
            
                
            
    def update_patient_state_after(self):
        # 每天运行结束后，根据解信息，更新病人状态
        # for p in range(1, self.instance.patients+1):
        #     if self.patient_state[p]['state'] == -1:
        #         self.instance.DA_p[p][0] -= 1
        #         self.instance.DA_p[p][1] -= 1
        #         if self.instance.DA_p[p][0] < 0:
        #             self.instance.DA_p[p][0] = 1
        #         elif self.instance.DA_p[p][1] < 0:
        #             self.instance.DA_p[p][1] = 1
        
        
        for patient_com in self.Patient_list_now:
            new_id = patient_com[0]
            old_id = patient_com[1]
            
            
            # 可安排，未入院
            if self.patient_state[old_id]['state'] == 0:
                if self.solution[self.rolling_day][new_id]['Admission']==0:
                    self.patient_state[old_id]['state'] = 1
                    self.patient_state[old_id]['admission_day'] = self.rolling_day
                    self.patient_state[old_id]['fix_los_end'] = self.rolling_day + self.instance.L_p[old_id] - 1
                    self.patient_state[old_id]['discharge_day'] = self.rolling_day + self.instance.TL_p[old_id] - 1
                    self.patient_state[old_id]['schedule'][self.rolling_day] = self.solution[self.rolling_day][new_id][0]
                    self.patient_room_last_day[old_id] = self.solution[self.rolling_day][new_id][0]
                elif self.solution[self.rolling_day][new_id]['Admission']==-1: #未能安排
                    if self.instance.DA_p[old_id][1] <= self.rolling_day + self.planning_window:      #且已经超过了最大可入院时间
                        self.patient_state[old_id]['state'] = 3  #拒绝患者入院，告知让其找其他医院
                    
            # 可安排，已入院
            if self.patient_state[old_id]['state'] == 1:
                self.patient_state[old_id]['schedule'][self.rolling_day] = self.solution[self.rolling_day][new_id][0]
                self.patient_room_last_day[old_id] = self.solution[self.rolling_day][new_id][0]
                if self.rolling_day == self.patient_state[old_id]['fix_los_end']:
                    self.patient_state[old_id]['state'] = 2
                
                if self.rolling_day == self.patient_state[old_id]['discharge_day']:
                    self.patient_state[old_id]['state'] = 3
            
            # 不可安排，已入院
            if self.patient_state[old_id]['state'] == 2:
                d = self.patient_state[old_id]['fix_los_end']
                self.patient_state[old_id]['schedule'][self.rolling_day] = self.patient_state[old_id]['schedule'][d]
                self.patient_room_last_day[old_id] = self.patient_state[old_id]['schedule'][d]
                if self.rolling_day == self.patient_state[old_id]['discharge_day']:
                    self.patient_state[old_id]['state'] = 3
            
        
    
        
    def GetPatientList(self):
        # 患者分类：
        # 1. 未注册：无需考虑
        # 2. 已注册：
        #   2.1 未入院：按照新患者考虑，修正 AD_p
        #   2.2 已入院，且未离院：记录患者前一天的房间号
        #   2.3 已离院：不考虑
        
        # 获取病人列表
        self.Patient_list_now = []
        p_num = 1
        for p in range(1, self.instance.patients+1):
            # print("患者", p, "的状态为", self.patient_state[p]['state'])
            if self.patient_state[p]['state'] == 0 or self.patient_state[p]['state'] == 1 or self.patient_state[p]['state'] == 2:
                # print("患者", p, "的状态为", self.patient_state[p]['state'])
                self.Patient_list_now.append([p_num, p])
                p_num += 1
    
    def ins_get(self):
        file_path = self.instance.path + 'Day_' + str(self.rolling_day) + '/'
        self.ins4Today.append(Instance(file_path, in_OP = self.instance.W_op)) # 实例化一个新的实例
    
    # 准备下一天的求解算例
    def ins_update(self):
        # 生成新的算例，即未来规划窗口内的算例
        self.GetPatientList()
        file_path = self.instance.path + 'Day_' + str(self.rolling_day)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        ## 需要修改的信息
        # C_pr
        with open(file_path+'/C_pr.txt', 'w') as f:
            f.write("p"+'\t'+"r"+'\t'+"C_pr"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                for r in range(self.instance.rooms):
                    f.write(str(new_id) + '\t' + str(r+1) + '\t' + str(self.instance.C_pr[old_id][r]) + '\n')
                    
        # DA_p
        with open(file_path+'/DA_p.txt', 'w') as f:
            f.write("p"+'\t'+"ad_min"+'\t'+"ad_max"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                if self.patient_state[old_id]['state'] == 0:
                    d1 = self.instance.DA_p[old_id][0]-self.rolling_day
                    d2 = self.instance.DA_p[old_id][1]-self.rolling_day
                    if d1 < 0:
                        d1 = 0
                    if d2 < 0:
                        d2 = 0
                    f.write(str(new_id) + '\t' + str(d1) + '\t' + str(d2) + '\n')
                else:
                    f.write(str(new_id) + '\t' + str(0) + '\t' + str(0) + '\n')
        
        # L_p
        remaining_los = [[]]
        with open(file_path+'/L_p.txt', 'w') as f:
            f.write("p"+'\t'+"L_p"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                if self.patient_state[old_id]['state'] == 0:
                    f.write(str(new_id) + '\t' + str(self.instance.L_p[old_id]) + '\n')
                    remaining_los.append(self.instance.L_p[old_id])
                else:
                    lp = self.patient_state[old_id]['fix_los_end'] - self.rolling_day + 1
                    remaining_los.append(lp)
                    if lp < 0:
                        lp = 0
                    f.write(str(new_id) + '\t' + str(lp) + '\n')
                
        
        # L_pu
        with open(file_path +'/L_pu.txt', 'w') as f:
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                f.write(str(new_id))
                if self.patient_state[old_id]['state'] == 0:
                    for s in range(self.instance.scenario):
                        f.write('\t' + str(self.instance.L_ps[old_id][s]))
                else:
                    lpu = self.patient_state[old_id]['fix_los_end'] - self.rolling_day + 2
                    if lpu >= 0:
                        for s in range(self.instance.scenario):
                            f.write('\t' + str(self.instance.L_ps[old_id][s]))
                    else:
                        for s in range(self.instance.scenario):
                            new_over = self.instance.L_ps[old_id][s] + lpu
                            if new_over < 0:
                                new_over = 1
                            f.write('\t' + str(new_over))
                
                f.write('\n')
        
        # L_put
        with open(file_path +'/L_put.txt', 'w') as f:
            f.write("p"+'\t'+"d"+'\t'+"Pr(p,d)"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                minD = self.instance.DU_p[old_id]['min_date']
                maxD = self.instance.DU_p[old_id]['max_stay']
                
                # print("minD:", minD, " maxD:", maxD)
                # print(self.instance.DU_p[old_id])
                
                if remaining_los[new_id] == self.instance.L_p[old_id]:
                    for d in range(1, maxD+1):
                        f.write(str(new_id) + '\t' + str(d) + '\t' + str(self.instance.DU_p[old_id][d]) + '\n')
                else:
                    if remaining_los[new_id] <= 0:
                        new_minD = -1*remaining_los[new_id] + self.instance.L_p[old_id] + 1
                    else:
                        delta_lp = self.instance.L_p[old_id] - remaining_los[new_id]
                        new_minD = delta_lp + 1
                        # print("remaining_los[new_id]:", remaining_los[new_id], " delta_lp:", delta_lp, "new_minD:", new_minD, " maxD:", maxD)
                        # input()
                        
                    new_d = 0
                    
                    for d in range(new_minD, maxD+1):
                        new_d += 1
                        if d== new_minD:
                            f.write(str(new_id) + '\t' + str(new_d) + '\t' + str(1) + '\n')
                        else:
                            f.write(str(new_id) + '\t' + str(new_d) + '\t' + str(self.instance.DU_p[old_id][d]) + '\n')
                
        
        # PG_pg
        with open(file_path+'/PG_pg.txt', 'w') as f:
            f.write("p"+'\t'+"Fe"+'\t'+"Ma"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                f.write(str(new_id) + '\t' + str(self.instance.PG_pg[old_id][0]) + '\t' + str(self.instance.PG_pg[old_id][1]) + '\n')
        
        # profile
        with open(file_path+'/profile.txt', 'w') as f:
            f.write('Rooms:'+str(self.instance.rooms)+'\n')
            f.write('Patients:'+str(len(self.Patient_list_now))+'\n')
            f.write('Planning horizon:'+str(self.planning_window)+'\n')
            f.write('Scenario size:'+str(self.instance.scenario)+'\n')
            
            
        # patient_room_last_day
        with open(file_path+'/patient_room_last_day.txt', 'w') as f:
            f.write("p"+'\t'+"r"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                # print(new_id, old_id, self.patient_room_last_day[old_id])
                f.write(str(new_id) + '\t' + str(self.patient_room_last_day[old_id]) + '\n')
        
        # true_delta_earlest_admission_day
        # 距离最早入院，目前已延迟的天数
        with open(file_path+'/true_earliest_admission_day.txt', 'w') as f:
            f.write("p"+'\t'+"ad"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                tl = self.rolling_day - self.instance.DA_p[old_id][0]
                if tl < 0:
                    tl = 0
                f.write(str(new_id) + '\t' + str(tl) + '\n')
                
        # patient_state
        with open(file_path+'/patient_state.txt', 'w') as f:
            f.write("p"+'\t'+"state"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                f.write(str(new_id) + '\t' + str(self.patient_state[old_id]['state']) + '\n')
        
        
        # patient_list
        with open(file_path+'/patient_list.txt', 'w') as f:
            f.write("p_now"+'\t'+"p_old"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                f.write(str(new_id) + '\t' + str(old_id) + '\n')
                
        # R_p
        with open(file_path+'/R_p.txt', 'w') as f:
            f.write("p"+'\t'+"r"+'\t'+"R_p"+'\n')
            for patient_com in self.Patient_list_now:
                new_id = patient_com[0]
                old_id = patient_com[1]
                for r in range(self.instance.rooms):
                    f.write(str(new_id) + '\t' + str(r+1) + '\t' + str(self.instance.R_p[old_id][r]) + '\n')
        
        ## 直接复制的信息
        # Q_r, R_p, RG_rg, RT_r
        shutil.copy(self.instance.path + 'Q_r.txt', file_path)
        shutil.copy(self.instance.path + 'RG_rg.txt', file_path)
        shutil.copy(self.instance.path + 'RT_r.txt', file_path)
        
    # 采用SAA_SV求解
    def SAA_SV(self, scenarios=10, max_iter=3):
        log_path = os.path.join(self.log_path or 'log', 'SAASV') + os.sep
        result_path = os.path.join(self.result_path or 'result', 'SAASV') + os.sep
        os.makedirs(log_path, exist_ok=True)
        os.makedirs(result_path, exist_ok=True)
        if self.time_limit <= 0 or scenarios <= 0 or max_iter <= 0:
            raise ValueError('time_limit, scenarios, and max_iter must be positive')

        instance = self.ins4Today[-1]
        stem = (str(self.instance.patients) + '_' + str(self.rolling_day) + '_'
                + str(self.instance.W_DE1) + '_' + str(self.instance.W_tr) + '_'
                + str(self.instance.W_op))

        start = time.monotonic()
        saa_deadline = start + self.time_limit / 2
        final_deadline = start + self.time_limit
        best_plan = None
        best_cost = float('inf')
        previous_plan = None

        for iteration in range(1, max_iter + 1):
            stage_left = remaining(saa_deadline)
            if stage_left <= 0:
                break
            saa = PRAUWT_SB(instance, scenarios)
            saa_log = log_path + 'WSSAALog_' + stem + '_iter' + str(iteration) + '.txt'
            try:
                saa.Solve(time_limit=stage_left, log_file=saa_log,
                          deadline=saa_deadline,
                          input_solution=best_plan or previous_plan)
            except TimeoutError:
                break
            if saa.model.SolCount == 0:
                print('SAA iteration', iteration, ': no feasible solution')
                continue

            plan = saa.get_assignment()
            previous_plan = plan
            cost = evaluate_with_sv(instance, plan, saa_deadline)
            plan['SVFixedObjective'] = cost
            saa.output(plan, result_path + 'WSSAAResult_' + stem + '_iter' + str(iteration) + '.txt')
            print('SAA iteration', iteration, ': fixed SV objective =', cost)
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
        sv_log = log_path + 'WSSVLog_' + stem + '.txt'
        sv.Solve(time_limit=sv_limit, log_file=sv_log,
                 input_solution=best_plan, deadline=final_deadline)
        result = sv.get_assignment()
        result['BestSAAFixedObjective'] = None if best_cost == float('inf') else best_cost
        result['SAAMaxIter'] = max_iter
        result['SAAScenarios'] = scenarios
        result['SimulateCost'] = result['Objective']
        self.solution.append(result)
        sv.output(result, result_path + 'WSSVResult_' + stem + '.txt')
    
        # 采用EVP求解
    def TotalSolutionOutput(self, result_file):
        # 保存结果
        with open(result_file, 'w') as file:
            json.dump(self.patient_state, file)
    
    def SAA_SV_solve(self, total_rolling_day):
        # 采用 SAA_SV 方法进行滚动求解
        for h in range(total_rolling_day):
            self.rolling_day += 1
            print("*********SAA_SV enters day ", h, " of solving*********")
            self.update_patient_state_before()
            self.ins_update() #生成新算例
            self.ins_get()
            self.SAA_SV()
            self.update_patient_state_after()
            
        self.patient_state['rolling_day'] = self.rolling_day
        
        # 保存结果
        ## 患者信息
        result_dir = os.path.join(self.result_path or 'result', 'SAASV')
        os.makedirs(result_dir, exist_ok=True)
        stem = (str(self.instance.patients) + '_' + str(self.instance.W_DE1)
                + '_' + str(self.instance.W_tr) + '_' + str(self.instance.W_op))
        result_path = os.path.join(result_dir, 'SAASVTotal_solution_' + stem + '.txt')
        self.TotalSolutionOutput(result_path)
        tsim = TSim(self.instance, self.patient_state)
        result_file = os.path.join(result_dir, 'SAASVCost_component_' + stem + '.txt')
        tsim.runTrueScenario(result_file)
        result_file = os.path.join(result_dir, 'SAASVCost_component2_' + stem + '.txt')
        tsim.runTrueScenario2(result_file)
    
