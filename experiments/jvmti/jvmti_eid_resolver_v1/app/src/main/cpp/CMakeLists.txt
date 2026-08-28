cmake_minimum_required(VERSION 3.22.1)

project(finduas_eid_resolver_v1 LANGUAGES C)

add_library(finduas_eid_resolver_v1 SHARED resolver.c)

target_include_directories(
    finduas_eid_resolver_v1
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../jvmti_attach_canary/app/src/main/cpp/third_party/aosp_android_11_jvmti
)

target_compile_features(finduas_eid_resolver_v1 PRIVATE c_std_11)
target_compile_options(
    finduas_eid_resolver_v1
    PRIVATE
        -Wall
        -Wextra
        -Werror
        -fvisibility=hidden
        -ffunction-sections
        -fdata-sections
)

target_link_options(
    finduas_eid_resolver_v1
    PRIVATE
        -nostartfiles
        -Wl,--as-needed
        -Wl,--gc-sections
        -Wl,--no-undefined
        -Wl,--version-script=${CMAKE_CURRENT_SOURCE_DIR}/exports.map
)

find_library(android_log_library log REQUIRED)
target_link_libraries(finduas_eid_resolver_v1 PRIVATE ${android_log_library})
