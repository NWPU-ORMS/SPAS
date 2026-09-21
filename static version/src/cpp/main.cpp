#include "InstanceGet_SB.h"
#include "PRAU2_SB.h"
#include <filesystem>
#include <string>
namespace fs = std::filesystem;

int Create_dir(fs::path& dir) {

	try {
		// 递归创建目录
		if (fs::create_directories(dir)) {
			std::cout << "文件夹创建成功: " << dir << std::endl;
		} else {
			std::cout << "文件夹已存在或无需创建: " << dir << std::endl;
		}
	} catch (const fs::filesystem_error& e) {
		std::cerr << "文件系统错误: " << e.what() << '\n';
	}

	return 0;
}



int main(int argc, char *argv[]) {

	cout << "instance:" << atoi(argv[1]) << endl;
	cout << "num:" << atoi(argv[2]) << endl;
	cout << "ptype:" << argv[3] << endl;
	cout << "TimeLimit:" << atoi(argv[4]) << endl;
	cout << "OP:" << atoi(argv[5]) << endl;


	int example = atoi(argv[1]);

	string pathReadExample = "example/Uset" + to_string(example) + "/N" + argv[2] + "/" + argv[3];
	string LogpathToSave = string("log/Uset") + argv[1] + "/N" + argv[2] + "/" + argv[3] + "/SBLog" + to_string(example) + "_op" +  argv[5] + ".txt";
	string ResultpathToSave = string("result/Uset") + argv[1] + "/N" + argv[2] + "/" + argv[3] + "/SBResult" + to_string(example) + "_op" +  argv[5] + ".txt";

//	cout << "pathReadExample: " << pathReadExample << endl;
//	cout << "ResultpathToSave: " << ResultpathToSave << endl;
//	cout << "LogpathToSave: " << LogpathToSave << endl;
//	cout << "TimeLimit: " << argv[3] << endl;

	// 创建保留结果的文件夹
	string myStrings[8] = {"result",
						   string("result/Uset")+argv[1],
						   string("result/Uset")+argv[1]+"/N" + argv[2],
						   string("result/Uset")+argv[1]+"/N" + argv[2]+"/"+argv[3],
						   "log",
						   string("log/Uset")+argv[1],
						   string("log/Uset")+argv[1]+"/N" + argv[2],
						   string("log/Uset")+argv[1]+"/N" + argv[2]+"/"+argv[3]};
	for (int i = 0; i < 8; i++) {
		fs::path dir(myStrings[i]);
		Create_dir(dir);
	}

	InstanceGet_SB ins(pathReadExample, example);
	ins.W_OP = atoi(argv[5]);
	int TimeLimit = atoi(argv[4]);
	PRAU_SB pra(ins, ResultpathToSave, LogpathToSave, TimeLimit);
}