#include "state.h"

#include <errno.h>
#include <string.h>
#include <time.h>

static clockid_t condition_clock_id(void) {
#if defined(__ANDROID__)
    return CLOCK_MONOTONIC;
#else
    /* Darwin lacks pthread_condattr_setclock; host tests use its default clock. */
    return CLOCK_REALTIME;
#endif
}

static void signal_first_terminal_locked(
    AttemptState *attempt,
    enum AttemptTerminal terminal,
    int64_t callback_handle,
    const uint8_t *payload,
    int payload_len) {
    if (attempt->terminal != ATTEMPT_TERMINAL_NONE) {
        atomic_fetch_add_explicit(&attempt->duplicate_count, 1u, memory_order_relaxed);
        (void)pthread_cond_broadcast(&attempt->terminal_changed);
        return;
    }

    attempt->callback_handle = callback_handle;
    attempt->callback_handle_present = true;
    attempt->payload_len = payload_len;
    attempt->protocol_result = -1;
    attempt->state = -1;

    if (terminal == ATTEMPT_TERMINAL_RESPONSE && payload != NULL && payload_len == 2) {
        attempt->protocol_result = (int)payload[0];
        attempt->state = (int)payload[1];
        attempt->terminal = ATTEMPT_TERMINAL_RESPONSE;
    } else if (terminal == ATTEMPT_TERMINAL_REMOTE_TIMEOUT) {
        attempt->terminal = ATTEMPT_TERMINAL_REMOTE_TIMEOUT;
    } else {
        attempt->terminal = ATTEMPT_TERMINAL_MALFORMED;
    }
    (void)pthread_cond_broadcast(&attempt->terminal_changed);
}

int attempt_state_init(AttemptState *attempt) {
    if (attempt == NULL) {
        return EINVAL;
    }
    memset(attempt, 0, sizeof(*attempt));
    atomic_init(&attempt->begun, false);
    atomic_init(&attempt->send_call_count, 0u);
    atomic_init(&attempt->callback_count, 0u);
    atomic_init(&attempt->duplicate_count, 0u);
    atomic_init(&attempt->cancel_call_count, 0u);
    attempt->payload_len = -1;
    attempt->protocol_result = -1;
    attempt->state = -1;

    int error = pthread_mutex_init(&attempt->mutex, NULL);
    if (error != 0) {
        return error;
    }
    pthread_condattr_t condition_attributes;
    error = pthread_condattr_init(&condition_attributes);
    if (error != 0) {
        (void)pthread_mutex_destroy(&attempt->mutex);
        return error;
    }
#if defined(__ANDROID__)
    error = pthread_condattr_setclock(&condition_attributes, CLOCK_MONOTONIC);
    if (error != 0) {
        (void)pthread_condattr_destroy(&condition_attributes);
        (void)pthread_mutex_destroy(&attempt->mutex);
        return error;
    }
#endif
    error = pthread_cond_init(&attempt->terminal_changed, &condition_attributes);
    const int attribute_destroy_error = pthread_condattr_destroy(&condition_attributes);
    if (error != 0) {
        (void)pthread_mutex_destroy(&attempt->mutex);
        return error;
    }
    if (attribute_destroy_error != 0) {
        (void)pthread_cond_destroy(&attempt->terminal_changed);
        (void)pthread_mutex_destroy(&attempt->mutex);
        return attribute_destroy_error;
    }
    return 0;
}

void attempt_state_destroy_for_test(AttemptState *attempt) {
    if (attempt != NULL) {
        (void)pthread_cond_destroy(&attempt->terminal_changed);
        (void)pthread_mutex_destroy(&attempt->mutex);
    }
}

bool attempt_state_begin(AttemptState *attempt) {
    bool expected = false;
    return attempt != NULL && atomic_compare_exchange_strong_explicit(
                                  &attempt->begun,
                                  &expected,
                                  true,
                                  memory_order_acq_rel,
                                  memory_order_acquire);
}

bool attempt_state_note_send_call(AttemptState *attempt) {
    if (attempt == NULL ||
        !atomic_load_explicit(&attempt->begun, memory_order_acquire)) {
        return false;
    }
    unsigned int expected = 0u;
    return atomic_compare_exchange_strong_explicit(
        &attempt->send_call_count,
        &expected,
        1u,
        memory_order_acq_rel,
        memory_order_acquire);
}

bool attempt_state_note_cancel_call(AttemptState *attempt) {
    unsigned int expected = 0u;
    return attempt != NULL && atomic_compare_exchange_strong_explicit(
                                  &attempt->cancel_call_count,
                                  &expected,
                                  1u,
                                  memory_order_acq_rel,
                                  memory_order_acquire);
}

void attempt_state_set_returned_handle(AttemptState *attempt, int64_t handle) {
    if (attempt == NULL) {
        return;
    }
    (void)pthread_mutex_lock(&attempt->mutex);
    attempt->returned_handle = handle;
    attempt->returned_handle_ready = true;
    (void)pthread_cond_broadcast(&attempt->terminal_changed);
    (void)pthread_mutex_unlock(&attempt->mutex);
}

void attempt_state_on_response(
    AttemptState *attempt,
    int64_t callback_handle,
    const uint8_t *payload,
    int payload_len) {
    if (attempt == NULL) {
        return;
    }
    atomic_fetch_add_explicit(&attempt->callback_count, 1u, memory_order_relaxed);
    (void)pthread_mutex_lock(&attempt->mutex);
    signal_first_terminal_locked(
        attempt,
        ATTEMPT_TERMINAL_RESPONSE,
        callback_handle,
        payload,
        payload_len);
    (void)pthread_mutex_unlock(&attempt->mutex);
}

void attempt_state_on_timeout(AttemptState *attempt, int64_t callback_handle) {
    if (attempt == NULL) {
        return;
    }
    atomic_fetch_add_explicit(&attempt->callback_count, 1u, memory_order_relaxed);
    (void)pthread_mutex_lock(&attempt->mutex);
    signal_first_terminal_locked(
        attempt,
        ATTEMPT_TERMINAL_REMOTE_TIMEOUT,
        callback_handle,
        NULL,
        0);
    (void)pthread_mutex_unlock(&attempt->mutex);
}

enum AttemptTerminal attempt_state_wait_until_deadline(AttemptState *attempt, int timeout_ms) {
    if (attempt == NULL || timeout_ms <= 0) {
        return ATTEMPT_TERMINAL_LOCAL_DEADLINE;
    }

    struct timespec deadline = {0, 0};
    if (clock_gettime(condition_clock_id(), &deadline) != 0) {
        (void)pthread_mutex_lock(&attempt->mutex);
        if (attempt->terminal == ATTEMPT_TERMINAL_NONE) {
            attempt->terminal = ATTEMPT_TERMINAL_LOCAL_DEADLINE;
        }
        (void)pthread_mutex_unlock(&attempt->mutex);
        return ATTEMPT_TERMINAL_LOCAL_DEADLINE;
    }
    deadline.tv_sec += timeout_ms / 1000;
    deadline.tv_nsec += (long)(timeout_ms % 1000) * 1000000L;
    if (deadline.tv_nsec >= 1000000000L) {
        ++deadline.tv_sec;
        deadline.tv_nsec -= 1000000000L;
    }

    (void)pthread_mutex_lock(&attempt->mutex);
    while (attempt->terminal == ATTEMPT_TERMINAL_NONE) {
        const int wait_error =
            pthread_cond_timedwait(&attempt->terminal_changed, &attempt->mutex, &deadline);
        if (wait_error == ETIMEDOUT) {
            attempt->terminal = ATTEMPT_TERMINAL_LOCAL_DEADLINE;
            attempt->payload_len = -1;
            attempt->protocol_result = -1;
            attempt->state = -1;
            break;
        }
        if (wait_error != 0) {
            attempt->terminal = ATTEMPT_TERMINAL_LOCAL_DEADLINE;
            break;
        }
    }
    const enum AttemptTerminal terminal = attempt->terminal;
    (void)pthread_mutex_unlock(&attempt->mutex);
    return terminal;
}

bool attempt_state_wait_for_quiet_window(AttemptState *attempt, int quiet_ms) {
    if (attempt == NULL || quiet_ms <= 0) {
        return false;
    }

    struct timespec deadline = {0, 0};
    if (clock_gettime(condition_clock_id(), &deadline) != 0) {
        return false;
    }
    deadline.tv_sec += quiet_ms / 1000;
    deadline.tv_nsec += (long)(quiet_ms % 1000) * 1000000L;
    if (deadline.tv_nsec >= 1000000000L) {
        ++deadline.tv_sec;
        deadline.tv_nsec -= 1000000000L;
    }

    (void)pthread_mutex_lock(&attempt->mutex);
    if (attempt->terminal != ATTEMPT_TERMINAL_RESPONSE) {
        (void)pthread_mutex_unlock(&attempt->mutex);
        return false;
    }

    int wait_error = 0;
    while (atomic_load_explicit(&attempt->duplicate_count, memory_order_acquire) == 0u &&
           wait_error == 0) {
        wait_error =
            pthread_cond_timedwait(&attempt->terminal_changed, &attempt->mutex, &deadline);
    }
    const bool quiet = wait_error == ETIMEDOUT &&
                       atomic_load_explicit(&attempt->callback_count, memory_order_acquire) == 1u &&
                       atomic_load_explicit(&attempt->duplicate_count, memory_order_acquire) == 0u;
    (void)pthread_mutex_unlock(&attempt->mutex);
    return quiet;
}

AttemptSnapshot attempt_state_snapshot(AttemptState *attempt) {
    AttemptSnapshot snapshot = {0u, 0u, 0u, 0u, ATTEMPT_TERMINAL_NONE, 0, 0, 0, -1, -1, -1};
    if (attempt == NULL) {
        return snapshot;
    }

    snapshot.send_call_count =
        atomic_load_explicit(&attempt->send_call_count, memory_order_acquire);
    snapshot.callback_count =
        atomic_load_explicit(&attempt->callback_count, memory_order_acquire);
    snapshot.duplicate_count =
        atomic_load_explicit(&attempt->duplicate_count, memory_order_acquire);
    snapshot.cancel_call_count =
        atomic_load_explicit(&attempt->cancel_call_count, memory_order_acquire);

    (void)pthread_mutex_lock(&attempt->mutex);
    snapshot.terminal = attempt->terminal;
    snapshot.returned_handle_nonzero =
        attempt->returned_handle_ready && attempt->returned_handle != 0;
    snapshot.callback_handle_present = attempt->callback_handle_present;
    snapshot.handle_match = attempt->returned_handle_ready && attempt->callback_handle_present &&
                            attempt->returned_handle == attempt->callback_handle;
    snapshot.payload_len = attempt->payload_len;
    snapshot.protocol_result = attempt->protocol_result;
    snapshot.state = attempt->state;
    (void)pthread_mutex_unlock(&attempt->mutex);
    return snapshot;
}
