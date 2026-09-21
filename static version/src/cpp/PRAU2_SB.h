//
// Created by Haichao  on 01/01/2024.
//pu

#ifndef PRAU2_CPP_PRAU2_SB_H
#define PRAU2_CPP_PRAU2_SB_H

#include <fstream>
#include <cstring>
#include <iostream>
#include <iomanip>
#include <regex>
#include "gurobi_c++.h"
#include "InstanceGet_SB.h"
#include "tools.h"
#include <cstdlib>
using namespace std;

class mycallback:public GRBCallback{
public:
	double BestSol = 1E10;
	timespec start_time;
	double TimeToBest;
	GRBModel* model;
protected:
	void callback(){
		if(where == GRB_CB_MIP){
			double obj = getDoubleInfo(GRB_CB_MIP_OBJBST);
			if (BestSol - obj > 1E-5){
				BestSol = obj;
				TimeToBest = diff_time(start_time);
			}
		}
	}
};


class PRAU_SB {
public:
	int example;

	int P;  //patients;
	int D;  //planning_horizon;
	int R;  //rooms;
	int scenario;
	int G = 2;
	double W_RG;
	double W_TR;
	double W_OP;
	double W_DE;
	int Max_Over;
	double** C_pr;
	int* Q_r;
	int** PG_pg;
	int** DA_p;
	int** L_pu;
	int* L_p;
	int* RT_r;
	int** RG_rg;
	int** R_p;
	GRBVar**** x_prid;
	GRBVar*** b_rdw;
	GRBVar*** u_rdw;
	GRBVar*** z_rdw;
	GRBVar** t_pd;
	GRBVar** alpha_pd;
	GRBLinExpr linexp;
	GRBEnv env = GRBEnv();
	GRBModel model = GRBModel(env);
	timespec StartTimeToBuildModel;
	double TimeToBuildModel;
	mycallback cb;
	double solution_time = 0;
public:
	PRAU_SB(InstanceGet_SB& ins, string result_path_file, string log_path_file,double in_solution_time);
	void RecieveData(InstanceGet_SB& ins, double in_solution_time);
	void ApplyMemory();
	void Modeling();
	void Solve(string pathfile);
	void SaveSolution(string pathfile);
	~PRAU_SB();
};

#endif //PRAU2_CPP_PRAU2_SB_H
