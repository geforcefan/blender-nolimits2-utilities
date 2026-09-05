include(FetchContent)

set(libnolimitsCommit "aa4ea2dce4fd26f909df888505a5b7464ea171e8")

set(zlibVersion "1.3.1")

find_package(Git REQUIRED)

FetchContent_Declare(zlib
    GIT_REPOSITORY "https://github.com/madler/zlib.git"
    GIT_TAG "v${zlibVersion}"
    GIT_SHALLOW TRUE
    EXCLUDE_FROM_ALL
)
set(ZLIB_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(zlib)
target_include_directories(zlibstatic PUBLIC "${zlib_SOURCE_DIR}" "${zlib_BINARY_DIR}")

FetchContent_Declare(libnolimits
    GIT_REPOSITORY "https://github.com/geforcefan/libnolimits.git"
    GIT_TAG "${libnolimitsCommit}"
    SOURCE_SUBDIR noCMakeProject
    PATCH_COMMAND "${CMAKE_COMMAND}"
            "-DGIT_EXECUTABLE=${GIT_EXECUTABLE}"
            "-DpatchFile=${CMAKE_CURRENT_LIST_DIR}/libnolimits-doubles.patch"
            "-DsourceDirectory=<SOURCE_DIR>"
            -P "${CMAKE_CURRENT_LIST_DIR}/apply_patch.cmake"
)

FetchContent_MakeAvailable(libnolimits)

file(GLOB_RECURSE libnolimitsSources "${libnolimits_SOURCE_DIR}/libnolimits/*.cpp")
add_library(libnolimits STATIC ${libnolimitsSources})
set_target_properties(libnolimits PROPERTIES CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON)
target_include_directories(libnolimits SYSTEM PUBLIC "${libnolimits_SOURCE_DIR}")
target_compile_options(libnolimits PRIVATE -w)
target_link_libraries(libnolimits PUBLIC zlibstatic glmHeaders)
