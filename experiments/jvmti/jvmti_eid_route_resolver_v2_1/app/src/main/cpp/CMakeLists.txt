cmake_minimum_required(VERSION 3.22.1)

project(finduas_eid_route_resolver_v2_1 LANGUAGES C ASM)

add_library(
    finduas_eid_route_resolver_v2_1
    SHARED
    abi_shims.S
    agent.c
    module_inspect.c
    note_parser.c
    route_policy.c
    route_resolver.c
    target_profile.c
)

target_include_directories(
    finduas_eid_route_resolver_v2_1
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti
)

target_compile_features(finduas_eid_route_resolver_v2_1 PRIVATE c_std_11)
target_compile_definitions(finduas_eid_route_resolver_v2_1 PRIVATE _GNU_SOURCE)
target_compile_options(
    finduas_eid_route_resolver_v2_1
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
    finduas_eid_route_resolver_v2_1
    PRIVATE
        -nostartfiles
        -Wl,--as-needed
        -Wl,--gc-sections
        -Wl,--no-undefined
        -Wl,--version-script=${CMAKE_CURRENT_SOURCE_DIR}/exports.map
)

find_library(android_log_library log REQUIRED)
find_library(android_dl_library dl REQUIRED)
target_link_libraries(
    finduas_eid_route_resolver_v2_1
    PRIVATE
        ${android_log_library}
        ${android_dl_library}
)
