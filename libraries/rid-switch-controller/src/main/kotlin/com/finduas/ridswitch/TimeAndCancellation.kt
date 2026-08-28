package com.finduas.ridswitch

import java.util.concurrent.Callable
import java.util.concurrent.ExecutionException
import java.util.concurrent.FutureTask
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong

fun interface MonotonicClock {
    fun nowNanos(): Long
}

fun interface EpochClock {
    fun nowEpochSeconds(): Long
}

object SystemMonotonicClock : MonotonicClock {
    override fun nowNanos(): Long = System.nanoTime()
}

object SystemEpochClock : EpochClock {
    override fun nowEpochSeconds(): Long = System.currentTimeMillis() / 1_000L
}

interface CancellationToken {
    val isCancelled: Boolean

    fun checkpoint() {
        if (isCancelled) throw TransactionCancelledException()
    }
}

class CancellationSource : CancellationToken {
    private val cancelled = AtomicBoolean(false)
    override val isCancelled: Boolean get() = cancelled.get()
    fun cancel() = cancelled.set(true)
}

internal object NeverCancelled : CancellationToken {
    override val isCancelled: Boolean = false
}

class TransactionCancelledException internal constructor() : RuntimeException("cancelled")
class DeadlineExceededException internal constructor() : RuntimeException("deadline exceeded")
class BoundedCallTimeoutException internal constructor() : RuntimeException("bounded call timed out")
class CallerInterruptedException internal constructor() : RuntimeException("caller interrupted")

class Deadline internal constructor(val endNanos: Long) {
    fun remainingNanos(clock: MonotonicClock): Long {
        val now = clock.nowNanos()
        return try {
            Math.subtractExact(endNanos, now)
        } catch (_: ArithmeticException) {
            if (endNanos >= now) Long.MAX_VALUE else Long.MIN_VALUE
        }
    }

    fun checkpoint(clock: MonotonicClock) {
        if (remainingNanos(clock) <= 0L) throw DeadlineExceededException()
    }

    companion object {
        internal fun after(clock: MonotonicClock, durationNanos: Long): Deadline {
            val now = clock.nowNanos()
            val end = try {
                Math.addExact(now, durationNanos)
            } catch (_: ArithmeticException) {
                Long.MAX_VALUE
            }
            return Deadline(end)
        }
    }
}

/** Every adapter call receives a finite deadline and an explicit cancellation policy. */
class CallContext internal constructor(
    val deadline: Deadline,
    val cancellation: CancellationToken,
    val cleanup: Boolean,
) {
    fun checkpoint(clock: MonotonicClock) {
        deadline.checkpoint(clock)
        cancellation.checkpoint()
    }
}

internal interface BoundedCallRunner {
    fun <T> run(context: CallContext, block: () -> T): T
}

/**
 * Enforces an outer JVM deadline even if an adapter forgets to enforce its own transport timeout.
 * A timed-out operation is interrupted and is treated as permanently uncertain by the controller.
 */
internal class JvmBoundedCallRunner(
    private val clock: MonotonicClock,
) : BoundedCallRunner {
    private val sequence = AtomicLong(0L)

    override fun <T> run(context: CallContext, block: () -> T): T {
        context.checkpoint(clock)
        val remaining = context.deadline.remainingNanos(clock)
        if (remaining <= 0L) throw DeadlineExceededException()

        val task = FutureTask(Callable {
            context.checkpoint(clock)
            block()
        })
        val worker = Thread(task, "rid-switch-bounded-${sequence.incrementAndGet()}").apply {
            isDaemon = true
            start()
        }

        try {
            return task.get(remaining, TimeUnit.NANOSECONDS)
        } catch (_: TimeoutException) {
            task.cancel(true)
            throw BoundedCallTimeoutException()
        } catch (_: InterruptedException) {
            task.cancel(true)
            // InterruptedException clears the flag. Cleanup must run before the caller is re-interrupted.
            throw CallerInterruptedException()
        } catch (error: ExecutionException) {
            throw error.cause ?: error
        } finally {
            if (!task.isDone) worker.interrupt()
        }
    }
}
