cmake_minimum_required(VERSION 3.20)
project(nolimits2_utilities CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/fp:precise /W4)
else()
    add_compile_options(-ffp-contract=off -fno-fast-math -Wall -Wextra)
endif()

include(cmake/glm.cmake)

enable_testing()
add_subdirectory(src)
add_subdirectory(tests)
