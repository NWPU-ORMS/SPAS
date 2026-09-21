//
// Created by Haichao  on 01/01/2024.
//
#include "InstanceGet_SV.h"

InstanceGet_SV::InstanceGet_SV(int in_example){
	example = in_example;
	ProfileRead();
	ApplyMemory();
	DataRead();
}

void InstanceGet_SV::ProfileRead() {
	//var[0] = &example;
	var[1] = &R;
	var[2] = &P;
	var[3] = &D;
	var[4] = &scenario;
	regex  pattern("[0-9]+");
	smatch results;

	//逐行读取
	string str1;
	int line = 0;
	line = 1;
	Fin.open("example/Uset" + to_string(example) + "/profile.txt");
	cout << "example/Uset" + to_string(example) + "/profile.txt" <<endl;
	while (getline(Fin, str1)) {
		regex_search(str1, results, pattern);
		*var[line] = stoi(results.str(), 0, 10);
		line++;
		if (line == 5){
			break;
		}
	}
	Fin.close();
	cout << "R:" << R << endl;
	cout << "P:" << P << endl;
	cout << "D:" << D << endl;
	cout << "example:" << example << endl;
	cout << "scenario:" << scenario << endl;
}

void InstanceGet_SV::ApplyMemory() {
	//C_prd
	int p, r, d, g;
	C_pr = new double* [P];
	for (p = 0; p < P; p++) {
		C_pr[p] = new double [R];
	}
	for (p = 0; p < P; p++) {
		for (r = 0; r < R; r++) {
			C_pr[p][r] = 0;
		}
	}

	//Q_r
	Q_r = new int[R];
	for (r = 0; r < R; r++) {
		Q_r[r] = 0;
	}

	//RT_r
	RT_r = new int[R];
	for (r = 0; r < R; r++) {
		RT_r[r] = 0;
	}

	//PG_pg
	PG_pg = new int* [P];
	for (p = 0; p < P; p++) {
		PG_pg[p] = new int[G];
	}
	for (p = 0; p < P; p++) {
		for (g = 0; g < G; g++) {
			PG_pg[p][g] = 0;
		}
	}

	//RG_rg
	RG_rg = new int* [R];
	for (r = 0; r < R; r++) {
		RG_rg[r] = new int[G];
	}
	for (r = 0; r < R; r++) {
		for (g = 0; g < G; g++) {
			RG_rg[r][g] = 0;
		}
	}

	//DA_p
	DA_p = new int* [P];
	for (p = 0; p < P; p++) {
		DA_p[p] = new int[2];
	}
	for (p = 0; p < P; p++) {
		for (int i = 0; i < 2; i++) {
			DA_p[p][i] = 0;
		}
	}

	//L_p
	L_p = new int[P];

	//L_ps
	L_pu = new int* [P];
	for (p = 0; p < P; p++) {
		L_pu[p] = new int[scenario];
	}
	for (p = 0; p < P; p++) {
		for (int i = 0; i < scenario; i++) {
			L_pu[p][i] = 0;
		}
	}

	//R_p
	R_p = new int* [P];
	for (p = 0; p < P; p++){
		R_p[p] = new int[R];
	}
	for (p = 0; p < P; p++){
		for (r = 0; r < R; r++){
			R_p[p][r] = 0;
		}
	}
}

InstanceGet_SV::~InstanceGet_SV() {
	int p, r, d, g;
	for (p = 0; p < P; p++) {
		delete[] C_pr[p];
	}
	delete[] C_pr;


	for (p = 0; p < P; p++) {
		delete[] PG_pg[p];
	}
	delete[] PG_pg;


	for (r = 0; r < R; r++) {
		delete[] RG_rg[r];
	}
	delete[] RG_rg;

	for (p = 0; p < P; p++) {
		delete[] DA_p[p];
	}
	delete[] DA_p;

	delete[] L_p;

	for (p = 0; p < P; p++) {
		delete[] L_pu[p];
	}
	delete[] L_pu;

	delete[] Q_r;

	delete[] RT_r;

	for (p = 0; p < P; p++){
		delete[] R_p[p];
	}
	delete[] R_p;
}

void InstanceGet_SV::DataRead() {
	int p, r, d, g;
	string line;
	//C_prd
	{
		Fin.open("example/Uset" + to_string(example) + "/C_pr.txt");
		getline(Fin, line);
		while (!Fin.eof()) {
			Fin >> p >> r;
			Fin >> C_pr[p - 1][r - 1];
		}
		Fin.close();
	}
	//Q_r
	{
		Fin.open("example/Uset" + to_string(example) + "/Q_r.txt");
		getline(Fin, line);
		while (!Fin.eof()) {
			Fin >> r;
			Fin >> Q_r[r - 1];
		}
		Fin.close();
	}
	//RT_r
	{
		Fin.open("example/Uset" + to_string(example) + "/RT_r.txt");
		getline(Fin, line);
		while (!Fin.eof()) {
			Fin >> r;
			Fin >> RT_r[r - 1];
		}
		Fin.close();
	}
	//PG_pg
	{
		Fin.open("example/Uset" + to_string(example) + "/PG_pg.txt");
		getline(Fin, line);
		int p1;
		for (p = 0; p < P; p++) {
			Fin >> p1;
			for (g = 0; g < G; g++) {
				Fin >> PG_pg[p][g];
			}
		}
		Fin.close();
	}
	//RG_rg
	{
		Fin.open("example/Uset" + to_string(example) + "/RG_rg.txt");
		getline(Fin, line);
		int r1;
		for (r = 0; r < R; r++) {
			Fin >> r1;
			for (g = 0; g < G; g++) {
				Fin >> RG_rg[r][g];
			}
		}
		Fin.close();
	}
	//DA_p
	{
		Fin.open("example/Uset" + to_string(example) + "/DA_p.txt");
		getline(Fin, line);
		int p1;
		for (p = 0; p < P; p++) {
			Fin >> p1;
			for (int i = 0; i < 2; i++) {
				Fin >> DA_p[p][i];
			}
		}
		Fin.close();
	}
	//L_p
	{
		Fin.open("example/Uset" + to_string(example) + "/L_p.txt");
		getline(Fin, line);
		int k;
		for (p = 0; p < P; p++) {
			Fin >> k;
			Fin >> L_p[p];
		}
		Fin.close();
	}
	//L_pu
	{
		Fin.open("example/Uset" + to_string(example) + "/L_pu.txt");
		for (p = 0; p < P; p++) {
			for (int i = 0; i < scenario; i++) {
				Fin >> L_pu[p][i];
//				cout << L_pu[p][i] << " ";
			}
//			cout << endl;
		}
		Fin.close();
	}
	//R_p
	{
		Fin.open("example/Uset" + to_string(example) + "/R_p.txt");
		getline(Fin, line);
		while (!Fin.eof()) {
			Fin >> p >> r;
			Fin >> R_p[p-1][r-1];
		}
		Fin.close();
	}
}