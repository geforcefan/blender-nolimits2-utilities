add_executable(curvetest curvetest.cpp)
target_link_libraries(curvetest PRIVATE nolimits2track)
add_test(NAME curvetest COMMAND curvetest)
