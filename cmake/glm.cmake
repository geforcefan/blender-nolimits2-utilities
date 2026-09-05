include(FetchContent)

set(glmVersion "1.0.1")

FetchContent_Declare(glm
    GIT_REPOSITORY "https://github.com/g-truc/glm.git"
    GIT_TAG "${glmVersion}"
    GIT_SHALLOW TRUE
    SOURCE_SUBDIR noCMakeProject
)

FetchContent_MakeAvailable(glm)

add_library(glmHeaders INTERFACE)
target_include_directories(glmHeaders SYSTEM INTERFACE "${glm_SOURCE_DIR}")
target_compile_definitions(glmHeaders INTERFACE GLM_ENABLE_EXPERIMENTAL)
