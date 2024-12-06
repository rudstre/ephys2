# CMakeLists.txt

# Set the minimum version of CMake that can be used
cmake_minimum_required(VERSION 3.5 FATAL_ERROR)

# Set the C++ version
set(CMAKE_CXX_STANDARD 17)

# Compiler options
# set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if (WIN32)
	message(STATUS "Using Windows-specific flags")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
else()
	message(STATUS "Using regular flags")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3")
endif()

# Set the project name
project(_cpp)

# Project directories
set(SRC_DIR "cpp/src")

# Scikit-build
if(SKBUILD)
	message(STATUS "The project is built using scikit-build")
	# Scikit-Build does not add your site-packages to the search path
	# automatically, so we need to add it _or_ the pybind11 specific directory
	# here.
	execute_process(
	COMMAND "${PYTHON_EXECUTABLE}" -c
	        "import pybind11; print(pybind11.get_cmake_dir())"
	OUTPUT_VARIABLE _tmp_dir
	OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ECHO STDOUT)
	list(APPEND CMAKE_PREFIX_PATH "${_tmp_dir}")
endif()

# Set sources
set(SOURCE_FILES
	${SRC_DIR}/arr_utils.cpp
	${SRC_DIR}/rhd2000.cpp
	${SRC_DIR}/rhd64.cpp
	${SRC_DIR}/intan_ofps.cpp
	${SRC_DIR}/snippet.cpp
	${SRC_DIR}/detect.cpp
	${SRC_DIR}/align.cpp
	${SRC_DIR}/link.cpp
	${SRC_DIR}/split.cpp
	${SRC_DIR}/mask.cpp
	${SRC_DIR}/spc.cpp
	${SRC_DIR}/spc/aux1.c
	${SRC_DIR}/spc/aux2.c
	${SRC_DIR}/spc/distance.c
	${SRC_DIR}/spc/edge.c
	${SRC_DIR}/spc/RaggedArray.c
	${SRC_DIR}/spc/utilities.c
	${SRC_DIR}/isosplit5.cpp
	${SRC_DIR}/isosplit5/isocut5.cpp
	${SRC_DIR}/isosplit5/jisotonic5.cpp
	${SRC_DIR}/pybind.cpp
)

# Include pybind11
find_package(pybind11 CONFIG REQUIRED)

# Add C++ extensions
pybind11_add_module(_cpp MODULE ${SOURCE_FILES})

# Link & install
target_link_libraries(_cpp PRIVATE)
target_compile_definitions(_cpp PUBLIC)
install(TARGETS _cpp LIBRARY DESTINATION .)
