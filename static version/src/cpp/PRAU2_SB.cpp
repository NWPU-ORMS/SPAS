//
// Created by Haichao  on 01/01/2024.
//

#include "PRAU2_SB.h"


PRAU_SB::PRAU_SB(InstanceGet_SB& ins, string result_path_file, string log_path_file,double in_solution_time) {
	RecieveData(ins, in_solution_time);
	ApplyMemory();
	Modeling();
	Solve(log_path_file);
	SaveSolution(result_path_file);
}

void PRAU_SB::RecieveData(InstanceGet_SB& ins, double in_solution_time) {
	P = ins.P;
	D = ins.D;
	R = ins.R;
	C_pr = ins.C_pr;
	Q_r = ins.Q_r;
	PG_pg = ins.PG_pg;
	DA_p = ins.DA_p;
	L_pu = ins.L_pu;
	RT_r = ins.RT_r;
	RG_rg = ins.RG_rg;
	W_RG = ins.W_RG;
	W_TR = ins.W_TR;
	W_OP = ins.W_OP;
	W_DE = ins.W_DE;
	R_p = ins.R_p;
	L_p = ins.L_p;
	Max_Over = ins.Max_Over;
	scenario = ins.scenario;
	example = ins.example;
	solution_time = in_solution_time;
}

void PRAU_SB::ApplyMemory() {
	int p, r, d;
	alpha_pd = new GRBVar * [P];
	for (p = 0; p < P; p++) {
		alpha_pd[p] = new GRBVar[D];
	}

	x_prid = new GRBVar * * * [P];
	for (p = 0; p < P; p++) {
		x_prid[p] = new GRBVar * * [R];
	}
	for (p = 0; p < P; p++) {
		for (r = 0; r < R; r++) {
			x_prid[p][r] = new GRBVar*[D];
		}
	}
	for (p = 0; p < P; p++) {
		for (r = 0; r < R; r++) {
			for (d = 0; d < D; d++) {
				x_prid[p][r][d] = new GRBVar[D];
			}
		}
	}

	z_rdw = new GRBVar ** [R];
	u_rdw = new GRBVar ** [R];
	b_rdw = new GRBVar ** [R];
	for (r = 0; r < R; r++) {
		z_rdw[r] = new GRBVar*[D];
		u_rdw[r] = new GRBVar*[D];
		b_rdw[r] = new GRBVar*[D];
	}
	for (r = 0; r < R; r++) {
		for (d = 0; d < D; d++) {
			z_rdw[r][d] = new GRBVar[scenario];
			u_rdw[r][d] = new GRBVar[scenario];
			b_rdw[r][d] = new GRBVar[scenario];
		}
	}

	t_pd = new GRBVar * [P];
	for (p = 0; p < P; p++) {
		t_pd[p] = new GRBVar [D];
	}
}

PRAU_SB::~PRAU_SB(){
	int p, r, d, g;
	for (p = 0; p < P; p++) {
		delete[] alpha_pd[p];
	}
	delete[] alpha_pd;

	for (p = 0; p < P; p++) {
		for (r = 0; r < R; r++) {
			for (d = 0; d < D; d++) {
				delete[] x_prid[p][r][d];
			}
		}
	}
	for (p = 0; p < P; p++) {
		for (r = 0; r < R; r++) {
			delete[] x_prid[p][r];
		}
	}
	for (p = 0; p < P; p++) {
		delete[] x_prid[p];
	}
	delete[] x_prid;

	for (r = 0; r < R; r++) {
		for (d = 0; d < D; d++) {
			delete[] z_rdw[r][d];
			delete[] u_rdw[r][d];
			delete[] b_rdw[r][d];
		}
	}
	for (r = 0; r < R; r++) {
		delete[] z_rdw[r];
		delete[] u_rdw[r];
		delete[] b_rdw[r];
	}
	delete[] z_rdw;
	delete[] u_rdw;
	delete[] b_rdw;

	for (p = 0; p < P; p++) {
		delete[] t_pd[p];
	}
	delete[] t_pd;
}

void PRAU_SB::Modeling() {
	cout << "开始建模" <<endl;
	clock_gettime(CLOCK_REALTIME,&StartTimeToBuildModel); //获取建模开始时间

	int p, r, i, d, g, s;
	//----------------构建变量---------------------
	for (p = 0; p < P; p++){
		for (d = 0; d < D; d++){
			if (d >= DA_p[p][0] && d <= DA_p[p][1]){
				alpha_pd[p][d] = model.addVar(0, 1, 0, GRB_BINARY, "alpha_"+to_string(p)+"_" + to_string(d));
			}
		}
	}

	for (p = 0; p<P; p++){
		for (r = 0; r<R; r++){
			if (R_p[p][r] == 1) {
				for (i = 0; i < D; i++) {
					if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
						for (d = i; d < i + L_p[p]; d++) {
							if (d < D) {
								x_prid[p][r][i][d] = model.addVar(0, 1, 0, GRB_BINARY,
								                                  "x_" + to_string(p) + "_" + to_string(r) + "_" +
								                                  to_string(i) + "_" + to_string(d));
							}
						}
					}
				}
			}
		}
	}

	for (r = 0; r < R; r++) {
		if (RT_r[r] == 2) {
			for (d = 0; d < D; d++) {
				for (s = 0; s < scenario; s++) {
					u_rdw[r][d][s] = model.addVar(0, 1, 0, GRB_BINARY, "u_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
					b_rdw[r][d][s] = model.addVar(0, 1, 0, GRB_BINARY, "b_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
				}
			}
		}
	}

	for (r = 0; r < R; r++) { //病房r超过正常容量的数量不能超过其2倍
		for (d = 0; d < D; d++) {
			for (s = 0; s < scenario; s++) {
				z_rdw[r][d][s] = model.addVar(0, Q_r[r], 0, GRB_INTEGER,
				                              "z_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
			}
		}
	}

	for (p = 0; p < P; p++) {
		for (d = 0; d < D; d++) {
			if (d > DA_p[p][0] && d < DA_p[p][1] + L_p[p]) {
				t_pd[p][d] = model.addVar(0, 1, 0, GRB_BINARY, "t_" + to_string(p) + "_" + to_string(d));
			}
		}
	}
	cout << "构建目标函数" <<endl;
	//-----------------目标函数------------------------
	linexp = 0;
	for (p = 0; p < P; p++) {
		for (d = 0; d < D; d++) {
			if (d >= DA_p[p][0] && d <= DA_p[p][1]) {
				linexp += W_DE*(d - DA_p[p][0]) * alpha_pd[p][d];
			}
		}
	}
	for (p = 0; p<P; p++){
		for (r = 0; r<R; r++){
			if (R_p[p][r] == 1) {
//				cout << "p:" << p << " r:" << r << endl;
				for (i = 0; i < D; i++) {
					if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
						for (d = i; d < i + L_p[p]; d++) {
							if (d < D) {
								linexp += C_pr[p][r] * x_prid[p][r][i][d];
//								cout << C_pr[p][r] <<endl;
							}
						}
					}
				}
			}
		}
	}
	for (p = 0; p < P; p++) {
		if (L_p[p] >= 2) {
			for (d = 0; d < D; d++) {
				if (d > DA_p[p][0] && d < DA_p[p][1] + L_p[p]) {
					linexp += W_TR * t_pd[p][d];
				}
			}
		}
	}
	for (s = 0; s < scenario; s++) {
		for (p = 0; p < P; p++){
//			cout << p << " " << s << " " << L_pu[p][s] <<endl;
			for (r = 0; r < R; r++) {
				if (R_p[p][r] == 1) {
					for (i = 0; i < D; i++) {
						if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
							for (d = i + L_p[p]; d < i + L_p[p] + L_pu[p][s]; d++) {
								if (d < D) {
									int dd1 = i + L_p[p] - 1;
									linexp += C_pr[p][r] * x_prid[p][r][i][dd1] * (double) 1 / scenario;
//									cout << p << " " << r << " " << i << " " << d << " "<< dd1 << " " << s << " "<< C_pr[p][r] *  (double) 1 / scenario<<endl;
								}
							}
						}
					}
				}
			}
		}
	}
	for (s = 0; s < scenario; s++) {
		for (r = 0; r < R; r++) {
			if (RT_r[r] == 2) {
				for (d = 0; d < D; d++) {
					linexp += W_RG * b_rdw[r][d][s] * (double)1/scenario;
				}
			}
		}
	}

	for (s = 0; s < scenario; s++) {
		for (r = 0; r < R; r++) {
			for (d = 0; d < D; d++) {
				linexp += W_OP * z_rdw[r][d][s] * (double)1/scenario;
			}
		}
	}

	model.setObjective(linexp, GRB_MINIMIZE);


	cout << "构建约束" <<endl;
//	-----------------约束------------------------
//	 约束1
	for(p=0; p<P; p++){
		linexp = 0;
		for(d=0; d<D; d++) {
			if (d >= DA_p[p][0] && d <= DA_p[p][1]) {
				linexp += alpha_pd[p][d];
			}
		}
		model.addConstr(linexp == 1, "C1_" + to_string(p));
	}

	// 约束2
	for (p = 0; p <P; p++){
		for (i = 0; i < D; i++){
			if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
				for (d = i; d < i + L_p[p]; d++){
					if (d < D) {
						linexp = 0;
						for (r = 0; r < R; r++) {
							if (R_p[p][r] == 1) {
								linexp += x_prid[p][r][i][d];
							}
						}
						model.addConstr(linexp == alpha_pd[p][i],
						                "C2_" + to_string(p) + "_" + to_string(i) + "_" + to_string(d));
					}
				}
			}
		}
	}

	//	 约束2-1
	int num;
	for (r = 0; r < R; r++){
		for (d = 0; d < D; d++){
			for (s = 0; s < scenario; s++) {
				linexp = 0;
				linexp += Q_r[r];
				num = 0;
				for (p = 0; p < P; p++){
					if (R_p[p][r] == 1) {
						for (i = 0; i < D; i++) {
							if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
								if (d >= i && d < i + L_p[p]) {
									linexp -= x_prid[p][r][i][d];
									num++;
								}
							}
						}
					}
				}
				if (num > 0){
					model.addConstr(linexp >= 0, "C2-1_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
				}
			}
		}
	}

//	 约束3
//	int num;
	for (r = 0; r < R; r++){
		for (d = 0; d < D; d++){
			for (s = 0; s < scenario; s++) {
				linexp = 0;
				linexp += z_rdw[r][d][s]+Q_r[r];
				num = 0;
				for (p = 0; p < P; p++){
					if (R_p[p][r] == 1) {
						for (i = 0; i < D; i++) {
							if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
								if (d >= i && d < i + L_p[p]) {
									linexp -= x_prid[p][r][i][d];
									num++;
								} else if (d >= i + L_p[p] && d < i + L_p[p] + L_pu[p][s]) {
									int dd1 = i + L_p[p] - 1;
									linexp -= x_prid[p][r][i][dd1];
									num++;
								}
							}
						}
					}
				}
				if (num > 0){
					model.addConstr(linexp >= 0, "C3_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
				}
			}
		}
	}

//	 约束4
	for (r = 0; r < R; r++) {
		if (RT_r[r] == 2){
			for (d = 0; d <D;d++){
				for (s = 0; s <scenario; s++){
					linexp = 0;
					num = 0;
					linexp += 2*Q_r[r] * (u_rdw[r][d][s] + b_rdw[r][d][s]);
					for (p = 0; p < P; p++){
						if (R_p[p][r] == 1 && PG_pg[p][0] == 1){
							for (i = 0;i <D; i++){
								if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
									if (d >= i && d < i + L_p[p]){
										linexp -= x_prid[p][r][i][d];
										num ++;
									}
									else if (d >= i + L_p[p] && d < i + L_p[p] + L_pu[p][s]){
										int dd1 = i + L_p[p] - 1;
										linexp -= x_prid[p][r][i][dd1];
										num ++;
									}
								}
							}
						}
					}
					if (num > 0){
						model.addConstr(linexp >= 0, "C4_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
					}
				}
			}
		}
	}

	// 约束5
	for (r = 0; r < R; r++) {
		if (RT_r[r] == 2){
			for (d = 0; d <D;d++){
				for (s = 0; s <scenario; s++){
					linexp = 0;
					num = 0;
					linexp += 2 * Q_r[r]  * (1 - u_rdw[r][d][s] + b_rdw[r][d][s]);
					for (p = 0; p < P; p++){
						if (R_p[p][r] == 1 && PG_pg[p][1] == 1){
							for (i = 0;i <D; i++){
								if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
									if (d >= i && d < i + L_p[p]){
										linexp -= x_prid[p][r][i][d];
										num ++;
									}
									else if (d >= i + L_p[p] && d < i + L_p[p] + L_pu[p][s]){
										int dd1 = i + L_p[p] - 1;
										linexp -= x_prid[p][r][i][dd1];
										num ++;
									}
								}
							}
						}
					}
					if (num > 0){
						model.addConstr(linexp >= 0, "C5_" + to_string(r) + "_" + to_string(d) + "_" + to_string(s));
					}
				}
			}
		}
	}

	// 约束6
	for (p = 0; p <P; p++) {
		if (L_p[p] >= 2) {
			for (r = 0; r < R; r++) {
				if (R_p[p][r] == 1) {
					for (d = 0; d < D; d++) {
						if (d > DA_p[p][0] && d < DA_p[p][1] + L_p[p]) {
							linexp = 0;
							linexp += t_pd[p][d];
							if (d > DA_p[p][0] && d <= DA_p[p][1]) {
								linexp += alpha_pd[p][d];
							}
							for (i = 0; i < D; i++) {
								if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
									if (d > i && d < i + L_p[p]) {
										linexp -= x_prid[p][r][i][d];
										linexp -= -x_prid[p][r][i][d - 1];
										num++;
									}
								}
							}
							model.addConstr(linexp >= 0,
							                "C6_" + to_string(p) + "_" + to_string(r) + "_" + to_string(d));
						}
					}
				}
			}
		}
	}
	TimeToBuildModel = diff_time(StartTimeToBuildModel);
}

void PRAU_SB::Solve(string pathfile) {
//	clock_gettime(CLOCK_REALTIME,&start_time); //获取开始时间
//	BestSol = 1E+10;
	cout << "开始求解" <<endl;
	model.set("Method", "3");
	if (solution_time > 1){
		model.set("TimeLimit", to_string(solution_time));
	}
//	model.set("LogFile", "log/SBModel/SBLog" + to_string(example) + ".txt");
	model.set("LogFile", pathfile);

	clock_gettime(CLOCK_REALTIME,&cb.start_time);
	model.setCallback(&cb);
	model.optimize();
	cout << "求解结束" <<endl;
//	cout << "最优解为：" << cb.BestSol << endl;
//	cout << "最优解出现时间：" << cb.TimeToBest << endl;
//	cout << "模型构建时间：" << TimeToBuildModel << endl;
}

void PRAU_SB::SaveSolution(string pathfile){
	ofstream outFile; //文件输出变量
	int p, r, i, d, g;
	outFile.open(pathfile);
	// 将结果写入为json格式
	outFile << "{"; //开始写入
	// 写入统计信息
	if (model.get(GRB_IntAttr_Status) != 3){
		outFile << "\"Objective\"\: " << model.get(GRB_DoubleAttr_ObjVal) << "\, ";
		outFile << "\"TimeToBest\"\: " << cb.TimeToBest << "\, ";
		outFile << "\"TimeToEnd\"\: " << model.get(GRB_DoubleAttr_Runtime) << "\, ";
		outFile << "\"LowerBound\"\: " << model.get(GRB_DoubleAttr_ObjBound) << "\, ";
		outFile << "\"NodeCount\"\: " << model.get(GRB_DoubleAttr_NodeCount) << "\, ";
	}
	else{
		outFile << "\"Objective\"\: -" << "\, ";
		outFile << "\"TimeToBest\"\: -" << "\, ";
		outFile << "\"TimeToEnd\"\: -" <<  "\, ";
		outFile << "\"LowerBound\"\: -" <<  "\, ";
		outFile << "\"NodeCount\"\: -" << "\, ";
	}
	outFile << "\"TimeToBuildModel\"\: " << TimeToBuildModel << "\, ";
	outFile << "\"NumVars\"\: " << model.get(GRB_IntAttr_NumVars) << "\, ";
	outFile << "\"NumConstrs\"\: " << model.get(GRB_IntAttr_NumConstrs) << "\, ";
	// 写入各患者信息
	if (model.get(GRB_IntAttr_Status) != 3) {
		for (p = 0; p < P; p++) {
			outFile << "\"" << p + 1 << "\"\: \{";

			for (i = 0; i < D; i++) {
				if (i >= DA_p[p][0] && i <= DA_p[p][1]) {
					if (abs(alpha_pd[p][i].get(GRB_DoubleAttr_X) - 1) < 1E-3) {
						outFile << "\"Admission\"\: " << to_string(i) << "\, ";

						for (d = i; d < i + L_p[p]; d++) {
							if (d < D) {
								for (r = 0; r < R; r++) {
									if (R_p[p][r] == 1) {
										if (abs(x_prid[p][r][i][d].get(GRB_DoubleAttr_X) - 1) < 1E-3) {
											outFile << "\"" << to_string(d) << "\"\: " << to_string(r);
										}
									}
								}
								if (d < i + L_p[p] - 1 && d < D - 1) {
									outFile << "\, ";
								}
							}
						}
					}
				}
			}
			if (p < P - 1) {
				outFile << "}, ";
			} else {
				outFile << "}";
			}
		}
	}
	outFile << "}"; //结束写入
	outFile.close();
}