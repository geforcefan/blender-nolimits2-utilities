add_library(nolimits2track STATIC
    curve.cpp
    math.cpp
    nurbs.cpp
    roll.cpp
    spline.cpp
    track.cpp
)
target_include_directories(nolimits2track PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(nolimits2track PUBLIC glmHeaders)
