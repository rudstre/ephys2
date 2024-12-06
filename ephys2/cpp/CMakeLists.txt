# CMakeLists.txt

# Set the minimum version of CMake that can be used
cmake_minimum_required(VERSION 3.5 FATAL_ERROR)

# Set the C++ version
SET(CMAKE_CXX_STANDARD 17)

# Set the project name to current directory names
project(ephys2)

# Global include directory
include_directories(/usr/local/include)

# Project directories
set(PROJECT_SOURCE_DIR "src")
set(PROJECT_INCLUDE_DIR "include/ephys2")

# Set sources to compile
SET(SOURCE_FILES
	${PROJECT_SOURCE_DIR}/rhd.cpp
	${PROJECT_INCLUDE_DIR}/rhd.h
)

# Add library
add_library(ephys2 SHARED ${SOURCE_FILES})

# Set public headers to include
target_include_directories(ephys2 PRIVATE include/ephys2)

# Install
install(TARGETS ephys2 DESTINATION lib)

# Install the headers
install(FILES include/ephys2.h DESTINATION include)

# Create base directory
install(DIRECTORY include/ephys2 DESTINATION include)
