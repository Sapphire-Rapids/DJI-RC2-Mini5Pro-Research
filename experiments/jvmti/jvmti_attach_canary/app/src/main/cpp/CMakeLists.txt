cmake_minimum_required(VERSION 3.22.1)

project(finduas_jvmti_attach_canary LANGUAGES C)

add_library(finduas_jvmti_canary SHARED canary.c)

target_include_directories(
    finduas_jvmti_canary
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/third_party/aosp_android_11_jvmti
)

target_compile_features(finduas_jvmti_canary PRIVATE c_std_11)
target_compile_options(
    finduas_jvmti_canary
    PRIVATE
        -Wall
        -Wextra
        -Werror
        -fvisibility=hidden
        -ffunction-sections
        -fdata-sections
)

target_link_options(
    finduas_jvmti_canary
    PRIVATE
        -nostartfiles
        -Wl,--as-needed
        -Wl,--gc-sections
        -Wl,--no-undefined
        -Wl,--version-script=${CMAKE_CURRENT_SOURCE_DIR}/exports.map
)

find_library(android_log_library log REQUIRED)
target_link_libraries(finduas_jvmti_canary PRIVATE ${android_log_library})
