execute_process(
    COMMAND "${GIT_EXECUTABLE}" apply --reverse --check "${patchFile}"
    WORKING_DIRECTORY "${sourceDirectory}"
    RESULT_VARIABLE patchAlreadyApplied
    OUTPUT_QUIET
    ERROR_QUIET
)

if(patchAlreadyApplied EQUAL 0)
    message(STATUS "Patch bereits eingespielt: ${patchFile}")
    return()
endif()

execute_process(
    COMMAND "${GIT_EXECUTABLE}" apply "${patchFile}"
    WORKING_DIRECTORY "${sourceDirectory}"
    RESULT_VARIABLE patchResult
    ERROR_VARIABLE patchError
)

if(NOT patchResult EQUAL 0)
    message(FATAL_ERROR "Patch fehlgeschlagen: ${patchFile}\n${patchError}")
endif()

message(STATUS "Patch eingespielt: ${patchFile}")
