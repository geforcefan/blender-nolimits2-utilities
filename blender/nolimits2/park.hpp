#pragma once

#include "track.hpp"

#include <glm/vec2.hpp>

#include <cstddef>
#include <string>
#include <vector>

namespace NoLimits::NoLimits2 {
class Coaster;
}

namespace nolimits2 {

struct Coaster {
    std::string name;
    std::vector<nolimits2track::Track> tracks;
};

struct Park {
    std::vector<Coaster> coasters;

    static Park read(const void* bytes, std::size_t byte_count);

private:
    static glm::dvec2 heartline_position(const NoLimits::NoLimits2::Coaster& coaster);
};

}
