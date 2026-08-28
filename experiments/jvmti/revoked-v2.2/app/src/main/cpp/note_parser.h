#ifndef FINDUAS_EID_ROUTE_V22_NOTE_PARSER_H
#define FINDUAS_EID_ROUTE_V22_NOTE_PARSER_H

#include <stddef.h>
#include <stdint.h>

#define FINDUAS_GNU_BUILD_ID_SIZE 20u

int finduas_parse_unique_gnu_build_id(
    const uint8_t *notes,
    size_t notes_size,
    uint8_t output[FINDUAS_GNU_BUILD_ID_SIZE]);

#endif
