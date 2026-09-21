//
// Created by Haichao  on 03/01/2024.
//

#ifndef PRAU2_CPP_INSTANCEGET_SB_H
#define PRAU2_CPP_INSTANCEGET_SB_H


#include <fstream>
#include <cstring>
#include <iostream>
#include <regex>
#include <string>
using namespace std;
//using std::setw;


class InstanceGet_SB {
public:
	int* var[5];
	double** C_pr;
	int* Q_r;           //病房r的可住病人数
	int** PG_pg;        //病人p的性别
	int** DA_p;         //病人p的可入院日期
	int* L_p;         //病人p的规定住院天数
	int** L_pu;          //病人p的实际住院天数
	int* RT_r;          //2 - NDR，1 - DR
	int** RG_rg;        //
	int** R_p;			//病人p可去的病房
	int W_OP = 1;
	int W_RG = 50;
	int W_TR = 100;
	int Max_Over = 2;
	int W_DE = 2;
	int P;  //patients;
	int D;  //planning_horizon;
	int R;  //rooms;
	int G = 2;
	int scenario;
	int example;
	ifstream Fin;     //文件读取变量
	ofstream outFile; //文件输出变量


public:
	InstanceGet_SB(string example_file, int in_example);
	void ApplyMemory();
	void ProfileRead(string example_file);
	void DataRead(string example_file);
	~InstanceGet_SB();
};


#endif //PRAU2_CPP_INSTANCEGET_SB_H
