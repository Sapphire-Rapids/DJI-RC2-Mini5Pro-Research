#ifndef FINDUAS_EID_RAW_GET_V2_STATE_H
#define FINDUAS_EID_RAW_GET_V2_STATE_H

#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdatomic.h>

enum AttemptTerminal {
    ATTEMPT_TERMINAL_NONE = 0,
    ATTEMPT_TERMINAL_RESPONSE = 1,
    ATTEMPT_TERMINAL_REMOTE_TIMEOUT = 2,
    ATTEMPT_TERMINAL_MALFORMED = 3,
    ATTEMPT_TERMINAL_LOCAL_DEADLINE = 4,
};

typedef struct AttemptSnapshot {
    unsigned int send_call_count;
    unsigned int callback_count;
    unsigned int duplicate_count;
    unsigned int cancel_call_count;
    enum AttemptTerminal terminal;
    int returned_handle_nonzero;
    int callback_handle_present;
    int handle_match;
    int payload_len;
    int protocol_result;
    int state;
} AttemptSnapshot;

typedef struct AttemptState {
    pthread_mutex_t mutex;
    pthread_cond_t terminal_changed;
    atomic_bool begun;
    atomic_uint send_call_count;
    atomic_uint callback_count;
    atomic_uint duplicate_count;
    atomic_uint cancel_call_count;
    enum AttemptTerminal terminal;
    int64_t returned_handle;
    int64_t callback_handle;
    bool returned_handle_ready;
    bool callback_handle_present;
    int payload_len;
    int protocol_result;
    int state;
} AttemptState;

int attempt_state_init(AttemptState *attempt);
void attempt_state_destroy_for_test(AttemptState *attempt);
bool attempt_state_begin(AttemptState *attempt);
bool attempt_state_note_send_call(AttemptState *attempt);
bool attempt_state_note_cancel_call(AttemptState *attempt);
void attempt_state_set_returned_handle(AttemptState *attempt, int64_t handle);
void attempt_state_on_response(
    AttemptState *attempt,
    int64_t callback_handle,
    const uint8_t *payload,
    int payload_len);
void attempt_state_on_timeout(AttemptState *attempt, int64_t callback_handle);
enum AttemptTerminal attempt_state_wait_until_deadline(AttemptState *attempt, int timeout_ms);
bool attempt_state_wait_for_quiet_window(AttemptState *attempt, int quiet_ms);
AttemptSnapshot attempt_state_snapshot(AttemptState *attempt);

#endif
