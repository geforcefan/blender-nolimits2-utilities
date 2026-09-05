#include "park.hpp"

#include <libnolimits/File/MemoryFile.h>
#include <libnolimits/NL2/Coaster/Coaster.h>
#include <libnolimits/NL2/Coaster/Mode.h>
#include <libnolimits/NL2/Coaster/Style.h>
#include <libnolimits/NL2/Coaster/Track/CustomTrack.h>
#include <libnolimits/NL2/Coaster/Track/RollPoint.h>
#include <libnolimits/NL2/Coaster/Track/Track.h>
#include <libnolimits/NL2/Coaster/Track/Vertex.h>
#include <libnolimits/NL2/Park.h>

#include <stdexcept>
#include <utility>

namespace nolimits2 {

Park Park::read(const void* bytes, std::size_t byte_count) {
    NoLimits::File::MemoryFile file;
    file.setBuffer(const_cast<void*>(bytes), static_cast<long>(byte_count));
    file.openRB();
    if (file.readChunkName() != "NL2P") {
        file.close();
        throw std::runtime_error("not a NoLimits 2 park file, chunk NL2P missing");
    }
    NoLimits::NoLimits2::Park parsed;
    file.readChunk(&parsed);
    file.close();

    const auto roll_point = [](const NoLimits::NoLimits2::RollPoint& read, bool strict) {
        return nolimits2track::Track::RollPoint{
            .position = read.getPosition(), .roll = read.getRoll(), .vertical = read.getVertical(), .strict = strict};
    };

    Park park;
    for (const NoLimits::NoLimits2::Coaster* coaster : parsed.getCoaster()) {
        Coaster converted{.name = coaster->getName()};
        const glm::dvec2 coaster_heartline_position = heartline_position(*coaster);
        for (const NoLimits::NoLimits2::Track* track : coaster->getTrack()) {
            const auto* custom_track = dynamic_cast<const NoLimits::NoLimits2::CustomTrack*>(track);
            if (custom_track == nullptr) {
                continue;
            }
            nolimits2track::Track read{.closed = custom_track->getClosed(), .heartline_position = coaster_heartline_position};
            for (const NoLimits::NoLimits2::Vertex* vertex : custom_track->getVertex()) {
                const glm::dvec4 position = vertex->getPosition();
                read.vertices.push_back({.position = glm::dvec3(position), .weight = position.w, .strict = vertex->getStrict()});
            }
            for (const NoLimits::NoLimits2::RollPoint* point : custom_track->getRollPoint()) {
                read.roll_points.push_back(roll_point(*point, point->getStrict()));
            }
            read.start_roll_point = roll_point(*custom_track->getFirstRollPoint(), false);
            read.end_roll_point = roll_point(*custom_track->getLastRollPoint(), false);
            converted.tracks.push_back(std::move(read));
        }
        park.coasters.push_back(std::move(converted));
    }
    return park;
}

glm::dvec2 Park::heartline_position(const NoLimits::NoLimits2::Coaster& coaster) {
    using NoLimits::NoLimits2::Mode;
    using NoLimits::NoLimits2::Style;
    const Mode& mode = *coaster.getMode();
    if (mode.getSplinePosition() == Mode::Custom) {
        return mode.getSplinePositionOffset();
    }
    if (mode.getSplinePosition() == Mode::CenterOfRail) {
        return glm::dvec2(0.0);
    }
    switch (coaster.getStyle()->getStyleType()) {
        case Style::ClassicSteelLoopingCoaster:
            return glm::dvec2(0.0, 1.1);
        case Style::CorkscrewCoaster:
            return glm::dvec2(0.0, 0.65);
        case Style::InvertedCoaster2Seats:
            return glm::dvec2(0.0, -0.9);
        case Style::TwistedSitdownCoaster:
            return glm::dvec2(0.0, 1.2);
        case Style::InvertedCoaster4Seats:
            return glm::dvec2(0.0, -1.1);
        case Style::HyperCoaster:
            return glm::dvec2(0.0, 0.9);
        case Style::TwistedFloorlessCoaster:
            return glm::dvec2(0.0, 1.3);
        case Style::TwistedStandUpCoaster:
            return glm::dvec2(0.0, 1.6);
        case Style::HyperCoaster4SeatsAcross:
            return glm::dvec2(0.0, 1.1);
        case Style::WoodenCoasterTrailered2:
            return glm::dvec2(0.0, 1.0);
        case Style::WoodenCoasterClassic4:
            return glm::dvec2(0.0, 1.0);
        case Style::WoodenCoasterClassic6:
            return glm::dvec2(0.0, 1.0);
        case Style::WoodenCoasterTrailered4:
            return glm::dvec2(0.0, 1.0);
        case Style::LimLaunchedCoaster:
            return glm::dvec2(0.0, 1.0);
        case Style::InvertedFaceToFaceCoaster:
            return glm::dvec2(0.0, -0.9);
        case Style::InvertedImpulseCoaster:
            return glm::dvec2(0.0, -1.16);
        case Style::SuspendedCoaster:
            return glm::dvec2(0.0, -1.7);
        case Style::VekomaFlyingDutchman:
            return glm::dvec2(0.0, 0.8);
        case Style::MaurerSoehneSpinningCoaster:
            return glm::dvec2(0.0, 1.15);
        case Style::TwistedDiveCoaster:
            return glm::dvec2(0.0, 1.8);
        case Style::Coaster4D:
            return glm::dvec2(0.0, 0.95);
        case Style::TwistedFlyingCoaster:
            return glm::dvec2(0.0, -1.1);
        case Style::RocketCoaster:
            return glm::dvec2(0.0, 1.1);
        case Style::VekomaMinetrainCoaster:
            return glm::dvec2(0.0, 1.2);
        case Style::VekomaMinetrainCoasterWithLocomotive:
            return glm::dvec2(0.0, 1.2);
        case Style::GerstlauerEuroFighter:
            return glm::dvec2(0.0, 1.1);
        case Style::VekomaMotorbikeCoaster:
            return glm::dvec2(0.0, 1.1);
        case Style::GerstlauerBobsledCoaster:
            return glm::dvec2(0.0, 1.1);
        case Style::GerstlauerSpinningCoaster:
            return glm::dvec2(0.0, 1.1);
        case Style::GerstlauerEuroFighter2:
            return glm::dvec2(0.0, 1.1);
        case Style::ClassicSteelLoopingCoasterModern:
            return glm::dvec2(0.0, 1.1);
        case Style::MaurerSoehneXCarCoaster:
            return glm::dvec2(0.0, 1.3);
        case Style::ZamperlaTwisterCoaster:
            return glm::dvec2(0.0, 1.1);
        case Style::MackLaunchedCoaster:
            return glm::dvec2(0.0, 1.5);
        case Style::HyperCoaster4SeatsStaggered:
            return glm::dvec2(0.0, 1.1);
        case Style::HyperCoaster4SeatsStaggeredWithScoops:
            return glm::dvec2(0.0, 1.1);
        case Style::GravityGroupTimberliner:
            return glm::dvec2(0.0, 1.0);
        case Style::TwistedWingCoaster:
            return glm::dvec2(0.0, 0.5);
    }
    return glm::dvec2(0.0);
}

}
