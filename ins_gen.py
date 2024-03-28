import random
from datetime import datetime
import json
import os

def select_from_distribution(distribution):
    n = len(distribution)
    sum_ = sum(distribution)
    val = random.randint(1, sum_)
    accumulated_prob = 0
    for j in range(n):
        if val <= distribution[j] + accumulated_prob:
            break
        accumulated_prob += distribution[j]
    return j

class InsGenerate:
    
    def __init__(self, departments, rooms, features, patients, specialisms, days, overstay_risk):
        self.departments = departments
        self.rooms = rooms
        self.features = features
        self.patients = patients
        self.specialisms = specialisms
        self.days = days
        self.overstay_risk = overstay_risk

    def Generate(self):
        
        pediatric_dept_prob = 10
        geriatric_dept_prob = 10
        prob_needed_feature = 10
        over_stay_risk = 30
        
        # other parameters
        max_number_of_main_specialisms_per_dept = self.specialisms // 2 + 1
        max_age = 90
        incumbent_patients = self.patients // 20  # 5%

        # distributions
        length_distribution = [10, 20, 20, 10, 8, 8, 8, 8, 6, 6]
        max_length = len(length_distribution)
        available_capacities = [1, 2, 4, 6]
        policy_distributions = [60, 15, 15, 10]
        policies = ["SG", "Ma", "Fe", "All"]

        # statistics
        self.total_capacity = 0
        self.total_occupancy = 0
        self.daily_occupancy = [0] * self.days

        # print("Date: " + datetime.now().strftime('%A %dth of %B %Y %I:%M:%S %p'))
        # print("Departments: " + str(departments))
        # print("Rooms: " + str(rooms))
        # print("Features: " + str(features))
        # print("Patients: " + str(patients))
        # print("Specialisms: " + str(specialisms))
        # print("Days: " + str(days))
        # print("\nDEPARTMENTS (name, age_constraint, main_specialisms_list, aux_specialisms_list):")

        self.Departments_dict = {i:{"age_constraint":[], "main_spec":[], "aux_spec":[]} for i in range(self.departments)}
        for i in range(self.departments):
            s = "Dept_" + str(i) + " "
            type_ = random.randint(1, 100)
            if type_ <= pediatric_dept_prob:
                s += "<= 16"
                self.Departments_dict[i].update({"age_constraint": "<= 16"})
            elif type_ <= pediatric_dept_prob + geriatric_dept_prob:
                s += ">= 65"
                self.Departments_dict[i].update({"age_constraint": ">= 65"})
            else:
                s += "*"
                self.Departments_dict[i].update({"age_constraint": "*"})
            specs = []
            num_main_spec = random.randint(1, max_number_of_main_specialisms_per_dept)
            s += " ("
            for j in range(1, num_main_spec + 1):
                while True:
                    main_spec = random.randint(0, self.specialisms - 1)
                    if main_spec not in specs:
                        break
                specs.append(main_spec)
            specs.sort()
            for j in range(num_main_spec):
                self.Departments_dict[i]['main_spec'].append(specs[j])
                if j < num_main_spec - 1:
                    s += str(specs[j]) + ","
                else:
                    s += str(specs[j]) + ") "
            min_aux_specs = min(self.specialisms, 1)
            if self.specialisms - num_main_spec <= min_aux_specs + 1:
                num_aux_spec = min_aux_specs
            else:
                num_aux_spec = random.randint(min_aux_specs, self.specialisms - num_main_spec - 1)

            if num_aux_spec == 0:  # currently impossible: min_aux_specs = 2
                s += "-"
            else:
                aux_specs = []
                s += "("
                for j in range(1, num_aux_spec + 1):
                    while True:
                        aux_spec = random.randint(0, self.specialisms - 1)
                        if aux_spec not in specs and aux_spec not in aux_specs:
                            break
                    aux_specs.append(aux_spec)
                aux_specs.sort()
                for j in range(num_aux_spec):
                    self.Departments_dict[i]['aux_spec'].append(aux_specs[j])
                    if j < num_aux_spec - 1:
                        s += str(aux_specs[j]) + ","
                    else:
                        s += str(aux_specs[j]) + ")"
            # print(s)

        self.Rooms_dict = {i:{"name":None, "capacity":None, "dept_index":None, "gender_policy":None, "features_list":[]} for i in range(self.rooms)}
        # print("\nROOMS (name, capacity, dept_index, gender_policy (SG/Ma/Fe/All), features_list):")
        for i in range(self.rooms):
            s = str(i)
            self.Rooms_dict[i]['name'] = "Room_" + str(s)
            
            capacity = available_capacities[random.randint(0, len(available_capacities) - 1)]
            self.total_capacity += capacity
            s += " " + str(capacity)
            self.Rooms_dict[i]['capacity'] = capacity
            
            department = random.randint(0, self.departments - 1)
            s += " " + str(department)
            self.Rooms_dict[i]['dept_index'] = department
            
            policy = select_from_distribution(policy_distributions)
            s += " " + policies[policy] + " "
            self.Rooms_dict[i]['gender_policy'] = policies[policy]

            num_features = random.randint(2, self.features)
            if num_features == 0:
                s += "-"
            else:
                selected_features = []
                s += "("
                for j in range(1, num_features + 1):
                    while True:
                        feature = random.randint(0, self.features - 1)
                        if feature not in selected_features:
                            break
                    selected_features.append(feature)
                selected_features.sort()
                for j in range(num_features):
                    self.Rooms_dict[i]['features_list'].append(selected_features[j])
                    if j < num_features - 1:
                        s += str(selected_features[j]) + ","
                    else:
                        s += str(selected_features[j]) + ")"
            # print(s)

        self.Patients_dict = {i:{"name":None, "age":None, "gender":None, 
                            "registration": None, "admission": None, "discharge":None, "length":None, "variability":None, "max_admission":None,
                            "treatment":None, "preferred_capacity":None, "room_property_list":[]} for i in range(self.patients)}
        # print("\nPATIENTS (name, age, gender, [registration, admission, discharge, variability, max_admission], treatment, preferred_capacity, room_property_list):")
        for i in range(self.patients):
            s = "Pat_" + str(i) + " "
            self.Patients_dict[i]['name'] = "Pat_" + str(i)
            
            age = random.randint(1, max_age)
            s += str(age) + " "
            self.Patients_dict[i]['age'] = age
            
            if random.randint(0, 1):
                self.Patients_dict[i]['gender'] = "Fe"
                s += "Fe "
            else:
                self.Patients_dict[i]['gender'] = "Ma"
                s += "Ma "

            length = select_from_distribution(length_distribution) + 1
            if i < incumbent_patients:
                admission = 0
                length = (length + 1) // 2
            else:
                admission = random.randint(0, self.days - 1)
            self.Patients_dict[i]['admission'] = admission

            length = min(length, self.days - admission)
            discharge = admission + length
            self.Patients_dict[i]['discharge'] = discharge
            self.Patients_dict[i]['length'] = length
            
            registration = random.randint(0, admission)
            self.Patients_dict[i]['registration'] = registration
            
            
            # variability = 1 if random.randint(1, 100) <= over_stay_risk else 0
            self.Patients_dict[i]['variability'] = []
            for j in range(self.overstay_risk):
                if j == 0:
                    variability = random.random() * 100
                    self.Patients_dict[i]['variability'].append(variability)
                else:
                    while 1:
                        variability = random.random() * 100
                        if variability <= self.Patients_dict[i]['variability'][j-1]:
                            break
                    self.Patients_dict[i]['variability'].append(variability)

            if random.randint(0, 1) == 0:  # 50%
                max_admission = "<=" + str(random.randint(admission, self.days - length))
            else:
                max_admission = "*"
            self.Patients_dict[i]['max_admission'] = max_admission

            for j in range(admission, admission + length):
                self.daily_occupancy[j] += 1
            self.total_occupancy += length

            s += "[" + str(registration) + ", " + str(admission) + ", " + str(discharge) + ", " + str(variability) + ", " + max_admission + "] "

            treatment = random.randint(0, self.specialisms - 1)
            s += str(treatment)
            self.Patients_dict[i]['treatment'] = treatment

            capacity_preference = available_capacities[random.randint(0, len(available_capacities) - 1)]
            if capacity_preference == available_capacities[-1]:
                s += " * "
                self.Patients_dict[i]['preferred_capacity'] = "*"
            else:
                s += " <=" + str(capacity_preference) + " "
                self.Patients_dict[i]['preferred_capacity'] = "<=" + str(capacity_preference)
            
            # s += " * " if capacity_preference == available_capacities[-1] else " <=" + str(capacity_preference) + " "

            squared_num_features = random.randint(0, self.features**2)
            num_features = int(squared_num_features**0.5)
            if num_features == 0:
                s += "-"
            else:
                selected_features = []
                s += "("
                for j in range(1, num_features + 1):
                    while True:
                        feature = random.randint(0, self.features - 1)
                        if feature not in selected_features:
                            break
                    selected_features.append(feature)
                selected_features.sort()
                for j in range(num_features):
                    need = "n" if random.randint(1, 100) <= prob_needed_feature else "p"
                    if j < num_features - 1:
                        s += str(selected_features[j]) + need + ","
                    else:
                        s += str(selected_features[j]) + need + ")"
                    self.Patients_dict[i]['room_property_list'].append((selected_features[j], need))
            # print(s)

        # print("\nEND.\n")
        # print("--------------------------------------------------")
        # print("Total capacity = " + str(total_capacity) + " X " + str(days) + " = " + str(total_capacity * days) + " beds*days")
        # print("Total occupancy = " + str(total_occupancy) + " (" + str(100 * total_occupancy / (total_capacity * days)) + "%)")
        # print("Daily occupancy = ", end='')
        self.capacity_ratio = []
        self.total_ratio = self.total_occupancy/(self.total_capacity * self.days)
        for day_occupancy in self.daily_occupancy:
            self.capacity_ratio.append(day_occupancy / self.total_capacity)
            # print(str(int(100 * day_occupancy / total_capacity)) + "%, ", end='')
        # print("\n")

    def FeasibleValidCapacity(self):
        self.feasible_flag = 1
        for d in range(self.days):
            if self.capacity_ratio[d] > 1:
                self.feasible_flag = 0
                break
    
    def DataChange_TestBed(self):
        
        w_alpha = 2
        w_g = 50
        w_sp = 20
        w_pe = 20
        w_rc = 10
        w_t = 100
        w_o = 1

        ## 病房信息生成
        ### Q_r 信息生成
        self.Q_r = []
        for r in range(self.rooms):
            self.Q_r.append([r, self.Rooms_dict[r]['capacity']])
        ### RT,RG 信息生成
        self.RT = []
        self.RG = []
        for r in range(self.rooms):
            rg  = self.Rooms_dict[r]['gender_policy']
            if rg == 'SG':
                self.RT.append([r, 2])
                self.RG.append([r, 0, 0])
            else:
                self.RT.append([r, 1])
                if rg == 'Ma':
                    self.RG.append([r, 0, 1])
                elif rg == 'Fe':
                    self.RG.append([r, 1, 0])
                else:
                    self.RG.append([r, 1, 1])


        ### DA_p 
        self.DA_p = []
        for p in range(self.patients):
            ad = self.Patients_dict[p]['admission']
            mad = self.Patients_dict[p]['max_admission']
            if mad != '*':
                mad = int(mad[2:])
            else:
                mad = ad
            self.DA_p.append([p, ad, mad])
        ### L_p 
        self.L_p = []
        for p in range(self.patients):
            self.L_p.append([p, self.Patients_dict[p]['length']])
        ### PG 
        self.PG = []
        for p in range(self.patients):
            pg = self.Patients_dict[p]['gender']
            if pg == 'Ma':
                self.PG.append([p, 0, 1])
            else:
                self.PG.append([p, 1, 0])

        ## w_pr 
        self.W_pr = []
        self.R_p = []
        for p in range(self.patients):
            for r in range(self.rooms):
                value = 0
                rp_value = 1
                dep = self.Rooms_dict[r]['dept_index']
                
                ### gender
                rg = self.Rooms_dict[r]['gender_policy']
                pg = self.Patients_dict[p]['gender']
                if rg != 'All' or rg != 'SG': 
                    if rg != pg: # soft constraint
                        value += w_g
                
                ### level of expertise
                sp = self.Patients_dict[p]['treatment']
                if sp not in self.Departments_dict[dep]['main_spec'] and sp not in self.Departments_dict[dep]['aux_spec']: # hard constraint
                    rp_value = 0
                elif sp not in self.Departments_dict[dep]['main_spec'] and sp in self.Departments_dict[dep]['aux_spec']: # soft constraint
                    value += w_sp
                
                ### patient age - hard constraint
                age = self.Patients_dict[p]['age']
                age_constraint = self.Departments_dict[dep]['age_constraint']
                if age_constraint == '*':
                    pass
                elif age_constraint == '<= 16':
                    if age > 16:
                        rp_value = 0
                elif age_constraint == '>= 65':
                    if age < 65:
                        rp_value = 0
                
                ### preferred equipment
                for propertylist in self.Patients_dict[p]['room_property_list']:
                    if propertylist == '-':
                        continue
                    property = propertylist[0]
                    need = propertylist[1]
                    if need == 'n': # hard constraint
                        if property not in self.Rooms_dict[r]['features_list']:
                            rp_value = 0
                    elif need == 'p': # soft constraint
                        if property not in self.Rooms_dict[r]['features_list']:
                            value += w_pe
                
                ### capacity
                preferred_capacity = self.Patients_dict[p]['preferred_capacity']
                if preferred_capacity != '*':
                    preferred_capacity = int(preferred_capacity[2:])
                    if preferred_capacity < self.Rooms_dict[r]['capacity']:
                        value += w_rc
                
                self.W_pr.append([p, r, value])
                self.R_p.append([p, r, rp_value])

        ## 
        self.L_put = []
        for p in range(self.patients):
            length = self.Patients_dict[p]['length']
            for l in range(length):
                self.L_put.append([p, l, 1])
            for j in range(self.overstay_risk):
                self.L_put.append([p, length + j, self.Patients_dict[p]['variability'][j]*0.01])

                
    def FeasibleValidRp(self):
        ## R_p 
        for p in range(self.patients):
            v = sum(self.R_p[p])
            if v == 0:
                # print("R_p error! patient " + str(p) + " can't be assigned to any room!")
                self.feasible_flag = 0
    
    def ScenarioGenerate(self, scenario):
    
        ## 
        self.L_pu = [[0 for s in range(scenario)] for i in range(self.patients)]
        for p in range(self.patients):
            for s in range(scenario):
                if scenario == 0:
                    rd = 50
                else:
                    rd = random.random() * 100
                
                stay_ = 0
                for j in range(self.overstay_risk):
                    if rd <= self.Patients_dict[p]['variability'][j]:
                        stay_ = j + 1
                    else:
                        break
                    
                self.L_pu[p][s] = stay_
                
    
    def Output(self, example, num, scenario):
        
        if scenario == 1:
            ptype = 'S1'
        else:
            ptype = 'Sn'
            
        file_list = ['Uset'+str(example), 'N'+ str(num), ptype]
        
        file_path  = 'example'
        
        for file in file_list:
            file_path = file_path + '/' + file
            if not os.path.exists(file_path):
                os.mkdir(file_path)
        
        
        with open(file_path+'/Departments_dict.txt', 'w') as file:
            json.dump(self.Departments_dict, file)

        with open(file_path+'/Rooms_dict.txt', 'w') as file:
            json.dump(self.Rooms_dict, file)
            
        with open(file_path+'/Patients_dict.txt', 'w') as file:
            json.dump(self.Patients_dict, file)

        profile_path = file_path+'/profile.txt'
        with open(profile_path, 'w') as f:
            f.write('Rooms:'+str(self.rooms)+'\n')
            f.write('Patients:'+str(self.patients)+'\n')
            f.write('Planning horizon:'+str(self.days)+'\n')
            f.write('Scenario size:'+str(scenario)+'\n')
            f.write("--------------------------------------------------\n")
            f.write("Total capacity = " + str(self.total_capacity) + " X " + str(self.days) + " = " + str(self.total_capacity * self.days) + " beds*days\n")
            f.write("Total occupancy = " + str(self.total_occupancy) + " (" + str(100 * self.total_occupancy / (self.total_capacity * self.days)) + "%)\n")
            f.write("Daily occupancy = ")
            for day_occupancy in self.daily_occupancy:
                f.write(str(int(100 * day_occupancy / self.total_capacity)) + "%, ")

        with open(file_path+'/C_pr.txt', 'w') as f:
            f.write("p"+'\t'+"r"+'\t'+"C_pr"+'\n')
            for w_ in self.W_pr:
                f.write(str(w_[0] + 1)+'\t'+str(w_[1] + 1)+'\t'+str(w_[2])+'\n')

        with open(file_path+'/DA_p.txt', 'w') as f:
            f.write("p"+'\t'+"ad_min"+'\t'+"ad_max"+'\n')
            for da in self.DA_p:
                f.write(str(da[0] + 1)+'\t'+str(da[1])+'\t'+str(da[2])+'\n')

        with open(file_path+'/L_p.txt', 'w') as f:
            f.write("p"+'\t'+"L_p"+'\n')
            for l in self.L_p:
                f.write(str(l[0]+1)+'\t'+str(l[1])+'\n')

        with open(file_path+'/L_pu.txt', 'w') as f:
            for p in range(self.patients):
                for s in range(scenario):
                    f.write(str(self.L_pu[p][s])+'\t')
                f.write('\n')

        with open(file_path+'/L_put.txt', 'w') as f:
            f.write("p"+'\t'+"d"+'\t'+"Pr(p,d)"+'\n')
            for l in self.L_put:
                f.write(str(l[0]+1)+'\t'+str(l[1]+1)+'\t'+"{:.2f}".format(l[2])+'\n')
                
        with open(file_path+'/PG_pg.txt', 'w') as f:
            f.write("p"+'\t'+"Fe"+'\t'+"Ma"+'\n')
            for pg in self.PG:
                f.write(str(pg[0]+1)+'\t'+str(pg[1])+'\t'+str(pg[2])+'\n')

        with open(file_path+'/Q_r.txt', 'w') as f:
            f.write("r"+'\t'+"Q_r"+'\n')
            for q in self.Q_r:
                f.write(str(q[0]+1)+'\t'+str(q[1])+'\n')

        with open(file_path+'/R_p.txt', 'w') as f:
            f.write("p"+'\t'+"r"+'\t'+"R_p"+'\n')
            for rp in self.R_p:
                f.write(str(rp[0]+1)+'\t'+str(rp[1]+1)+'\t'+str(rp[2])+'\n')
                
        with open(file_path+'/RG_rg.txt', 'w') as f:
            f.write("r"+'\t'+"Fe"+'\t'+"Ma"+'\n')
            for rg in self.RG:
                f.write(str(rg[0] + 1)+'\t'+str(rg[1])+'\t'+str(rg[2])+'\n')

        with open(file_path+'/RT_r.txt', 'w') as f:
            f.write("r"+'\t'+"RT_r"+'\n')
            for rt in self.RT:
                f.write(str(rt[0] + 1)+'\t'+str(rt[1])+'\n')