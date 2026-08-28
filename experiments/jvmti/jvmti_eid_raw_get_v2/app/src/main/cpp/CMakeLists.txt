cmake_minimum_required(VERSION 3.22.1)

project(finduas_eid_raw_get_v2 LANGUAGES C)

set(FINDUAS_GENERATED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../../build/generated")
if(NOT EXISTS "${FINDUAS_GENERATED_DIR}/helper_dex.inc")
    message(FATAL_ERROR "missing generated helper_dex.inc; run scripts/build_helper_dex.sh first")
endif()

add_library(
    finduas_eid_raw_get_v2
    SHARED
    agent.c
    jni_bridge.c
    route_snapshot.c
    state.c
)

target_include_directories(
    finduas_eid_raw_get_v2
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti
        ${FINDUAS_GENERATED_DIR}
)

target_compile_features(finduas_eid_raw_get_v2 PRIVATE c_std_11)
target_compile_definitions(finduas_eid_raw_get_v2 PRIVATE _POSIX_C_SOURCE=200809L)
target_compile_options(
    finduas_eid_raw_get_v2
    PRIVATE
        -Wall
        -Wextra
        -Werror
        -mno-outline-atomics
        -fvisibility=hidden
        -ffunction-sections
        -fdata-sections
)

target_link_options(
    finduas_eid_raw_get_v2
    PRIVATE
        -nostartfiles
        -Wl,--as-needed
        -Wl,--gc-sections
        -Wl,--no-undefined
        -Wl,--version-script=${CMAKE_CURRENT_SOURCE_DIR}/exports.map
)

find_library(android_log_library log REQUIRED)
target_link_libraries(finduas_eid_raw_get_v2 PRIVATE ${android_log_library})
