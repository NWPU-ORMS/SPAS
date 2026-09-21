cmake_minimum_required(VERSION 3.27)
project(PRAU2_cpp)

set(CMAKE_CXX_STANDARD 17)
#****************Gurobi配置****************************
#头文件
include_directories("/Library/gurobi911/mac64/include")
#静态链接库
find_library(gurobi_static NAMES libgurobi_g++4.2.a
        PATHS "/Library/gurobi911/mac64/lib")
#动态链接库
find_library(gurobi_dynamic NAMES gurobi91
        PATHS "/Library/gurobi912")
if(NOT gurobi_static)
    message(FATAL_ERROR "Failed to find Gurobi lib")
endif()
message(${gurobi_static})
message(${gurobi_dynamic})


add_executable(PRAU2_cpp
        PRAU2_SB.h
        PRAU2_SB.cpp
        InstanceGet_SV.h
        InstanceGet_SV.cpp
        main.cpp
        tools.h
        InstanceGet_SB.cpp
        InstanceGet_SB.h
)
#add_executable(PRAU2_cpp main.cpp tools.h)
target_link_libraries(${PROJECT_NAME} ${gurobi_static} ${gurobi_dynamic})