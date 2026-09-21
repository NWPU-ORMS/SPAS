//
// Created by Haichao on 2021/5/17.
//

#ifndef TOOLS_H
#define TOOLS_H
#include <time.h>

inline double diff_time(timespec start){ //inline函数会告诉编译器每次包含头文件时都可以创建一个新的函数副本，但链接器会忽略除一个之外的所有副本。
	timespec temp, end;
	clock_gettime(CLOCK_REALTIME, &end);
	double diff_time;
	if ((end.tv_nsec-start.tv_nsec)<0) {
		temp.tv_sec = end.tv_sec-start.tv_sec-1;
		temp.tv_nsec = 1e9+end.tv_nsec-start.tv_nsec;
	} else {
		temp.tv_sec = end.tv_sec-start.tv_sec;
		temp.tv_nsec = end.tv_nsec-start.tv_nsec;
	}
	diff_time = temp.tv_sec + temp.tv_nsec/1e9;
	return diff_time;
}

#endif //TOOLS_H
