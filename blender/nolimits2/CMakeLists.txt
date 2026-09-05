cmake_minimum_required(VERSION 3.20)
project(nolimits2 CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(MSVC)
    add_compile_options(/fp:precise /W4)
else()
    add_compile_options(-ffp-contract=off -fno-fast-math -Wall -Wextra)
endif()

find_package(Python 3.12 COMPONENTS Interpreter Development.Module ${SKBUILD_SABI_COMPONENT} REQUIRED)
find_package(nanobind CONFIG REQUIRED)

set(repositoryRoot "${CMAKE_CURRENT_SOURCE_DIR}/../..")
include("${repositoryRoot}/cmake/glm.cmake")
include("${repositoryRoot}/cmake/libnolimits.cmake")
add_subdirectory("${repositoryRoot}/src" src)

nanobind_add_module(nolimits2 STABLE_ABI NB_STATIC module.cpp blender_spline.cpp park.cpp)
target_link_libraries(nolimits2 PRIVATE nolimits2track libnolimits)

install(TARGETS nolimits2 LIBRARY DESTINATION .)
