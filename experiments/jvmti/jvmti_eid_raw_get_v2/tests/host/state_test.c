#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#include "state.h"

static void test_single_send_guard(void) {
    AttemptState attempt;
    assert(attempt_state_init(&attempt) == 0);
    assert(!attempt_state_note_send_call(&attempt));
    assert(attempt_state_begin(&attempt));
    assert(!attempt_state_begin(&attempt));
    assert(attempt_state_note_send_call(&attempt));
    assert(!attempt_state_note_send_call(&attempt));
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.send_call_count == 1u);
    attempt_state_destroy_for_test(&attempt);
}

static void test_callback_before_return(void) {
    AttemptState attempt;
    const uint8_t payload[2] = {0u, 1u};
    assert(attempt_state_init(&attempt) == 0);
    assert(attempt_state_begin(&attempt));
    assert(attempt_state_note_send_call(&attempt));
    attempt_state_on_response(&attempt, 77, payload, 2);
    attempt_state_set_returned_handle(&attempt, 77);
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.terminal == ATTEMPT_TERMINAL_RESPONSE);
    assert(snapshot.handle_match == 1);
    assert(snapshot.payload_len == 2);
    assert(snapshot.protocol_result == 0);
    assert(snapshot.state == 1);
    assert(attempt_state_wait_for_quiet_window(&attempt, 1));
    attempt_state_destroy_for_test(&attempt);
}

static void test_duplicate_rejects_quiet_window(void) {
    AttemptState attempt;
    const uint8_t payload[2] = {0u, 1u};
    assert(attempt_state_init(&attempt) == 0);
    attempt_state_on_response(&attempt, 9, payload, 2);
    attempt_state_on_response(&attempt, 9, payload, 2);
    assert(!attempt_state_wait_for_quiet_window(&attempt, 1));
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.callback_count == 2u);
    assert(snapshot.duplicate_count == 1u);
    attempt_state_destroy_for_test(&attempt);
}

static void test_raw_nonzero_result_is_preserved(void) {
    AttemptState attempt;
    const uint8_t payload[2] = {9u, 0u};
    assert(attempt_state_init(&attempt) == 0);
    attempt_state_on_response(&attempt, 12, payload, 2);
    attempt_state_set_returned_handle(&attempt, 12);
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.protocol_result == 9);
    assert(snapshot.state == 0);
    attempt_state_destroy_for_test(&attempt);
}

static void test_malformed_and_duplicate(void) {
    AttemptState attempt;
    const uint8_t payload[1] = {0u};
    assert(attempt_state_init(&attempt) == 0);
    attempt_state_on_response(&attempt, 3, payload, 1);
    attempt_state_on_timeout(&attempt, 3);
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.terminal == ATTEMPT_TERMINAL_MALFORMED);
    assert(snapshot.callback_count == 2u);
    assert(snapshot.duplicate_count == 1u);
    assert(snapshot.protocol_result == -1);
    assert(snapshot.state == -1);
    attempt_state_destroy_for_test(&attempt);
}

static void test_remote_timeout(void) {
    AttemptState attempt;
    assert(attempt_state_init(&attempt) == 0);
    attempt_state_on_timeout(&attempt, 4);
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.terminal == ATTEMPT_TERMINAL_REMOTE_TIMEOUT);
    assert(snapshot.callback_count == 1u);
    attempt_state_destroy_for_test(&attempt);
}

static void test_local_deadline_and_cancel_guard(void) {
    AttemptState attempt;
    assert(attempt_state_init(&attempt) == 0);
    assert(attempt_state_wait_until_deadline(&attempt, 1) ==
           ATTEMPT_TERMINAL_LOCAL_DEADLINE);
    assert(attempt_state_note_cancel_call(&attempt));
    assert(!attempt_state_note_cancel_call(&attempt));
    AttemptSnapshot snapshot = attempt_state_snapshot(&attempt);
    assert(snapshot.cancel_call_count == 1u);
    attempt_state_destroy_for_test(&attempt);
}

int main(void) {
    test_single_send_guard();
    test_callback_before_return();
    test_raw_nonzero_result_is_preserved();
    test_malformed_and_duplicate();
    test_remote_timeout();
    test_local_deadline_and_cancel_guard();
    test_duplicate_rejects_quiet_window();
    puts("state tests: 7/7 PASS");
    return 0;
}
