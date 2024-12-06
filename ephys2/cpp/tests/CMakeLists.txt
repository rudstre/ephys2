cmake_minimum_required(VERSION 3.5 FATAL_ERROR)

set(CMAKE_CXX_STANDARD 17)

project(test)

include_directories(/usr/local/include)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/../bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/../bin)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/../bin)

find_library(EPHYS2_LIB ephys2 HINTS /usr/local/lib/)

# Add test executables here
add_executable(test_rhd test_rhd.cpp)
target_link_libraries(test_rhd PUBLIC ${EPHYS2_LIB})