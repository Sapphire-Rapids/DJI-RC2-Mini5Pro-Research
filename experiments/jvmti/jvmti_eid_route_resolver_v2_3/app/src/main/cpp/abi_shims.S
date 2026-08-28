    .text
    .p2align 2

    .global finduas_call_sret_member0
    .hidden finduas_call_sret_member0
    .type finduas_call_sret_member0, %function
finduas_call_sret_member0:
    mov x9, x0
    mov x8, x1
    mov x0, x2
    br x9
    .size finduas_call_sret_member0, .-finduas_call_sret_member0

    .global finduas_call_sret_core_get_key
    .hidden finduas_call_sret_core_get_key
    .type finduas_call_sret_core_get_key, %function
finduas_call_sret_core_get_key:
    ldr x10, [sp]
    mov x9, x0
    mov x8, x1
    mov x0, x2
    mov w1, w3
    mov w2, w4
    mov w3, w5
    mov w4, w6
    mov w5, w7
    mov x6, x10
    br x9
    .size finduas_call_sret_core_get_key, .-finduas_call_sret_core_get_key

    .global finduas_call_sret_get_abstraction
    .hidden finduas_call_sret_get_abstraction
    .type finduas_call_sret_get_abstraction, %function
finduas_call_sret_get_abstraction:
    mov x9, x0
    mov x8, x1
    mov x0, x2
    mov x1, x3
    br x9
    .size finduas_call_sret_get_abstraction, .-finduas_call_sret_get_abstraction

    .section .note.GNU-stack,"",%progbits
