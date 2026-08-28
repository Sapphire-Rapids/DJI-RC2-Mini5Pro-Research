package com.finduas.systemuidbridge.check;

import android.os.IBinder;
import android.os.Parcel;
import android.os.Process;
import android.os.RemoteException;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

/**
 * Read-only capability probe for DJI's optional "protocol" Binder service.
 *
 * <p>This program has one IPC path: IProtocolManager transaction 1
 * ({@code isEnable()}). It does not open a socket, create a wire-protocol packet,
 * register a listener, execute another process, or write device state.</p>
 */
public final class ProtocolServiceCheck {
    private static final String OUTPUT_VERSION = "1";
    private static final String SERVICE_NAME = "protocol";
    private static final String INTERFACE_DESCRIPTOR = "com.dji.protocol.IProtocolManager";
    private static final String CHECK_SERVICE_METHOD = "checkService";
    private static final int SYSTEM_UID = 1000;
    private static final int TRANSACTION_IS_ENABLE = 1;
    private static final int SYNCHRONOUS_FLAGS = 0;

    private ProtocolServiceCheck() {
    }

    public static void main(String[] args) {
        Result result;
        if (args != null && args.length != 0) {
            result = Result.failure(
                    "USAGE_ERROR",
                    "This fixed probe accepts no arguments.",
                    64
            );
        } else if (Process.myUid() != SYSTEM_UID) {
            result = Result.failure(
                    "WRONG_UID",
                    "The launcher did not inherit Android system UID 1000.",
                    65
            );
        } else {
            result = runReadOnlyCheck();
        }

        emit(result);
        if (result.exitCode != 0) {
            System.exit(result.exitCode);
        }
    }

    private static Result runReadOnlyCheck() {
        final IBinder binder;
        try {
            Class<?> serviceManager = Class.forName("android.os.ServiceManager");
            Method checkService = serviceManager.getDeclaredMethod(
                    CHECK_SERVICE_METHOD,
                    String.class
            );
            Object rawBinder = checkService.invoke(null, SERVICE_NAME);
            if (rawBinder == null) {
                return Result.failure(
                        "SERVICE_ABSENT",
                        "ServiceManager.checkService returned null.",
                        2
                );
            }
            if (!(rawBinder instanceof IBinder)) {
                return Result.failure(
                        "LOOKUP_TYPE_MISMATCH",
                        "The protocol service object is not an IBinder.",
                        4
                );
            }
            binder = (IBinder) rawBinder;
            if (!binder.pingBinder()) {
                return Result.failure(
                        "SERVICE_UNREACHABLE",
                        "The protocol Binder is not alive.",
                        4
                );
            }
            String descriptor = binder.getInterfaceDescriptor();
            if (!INTERFACE_DESCRIPTOR.equals(descriptor)) {
                return Result.failure(
                        "DESCRIPTOR_MISMATCH",
                        "The protocol Binder descriptor did not match the recovered ABI.",
                        4
                );
            }
        } catch (ClassNotFoundException error) {
            return lookupUnavailable();
        } catch (NoSuchMethodException error) {
            return lookupUnavailable();
        } catch (IllegalAccessException error) {
            return lookupUnavailable();
        } catch (InvocationTargetException error) {
            Throwable cause = error.getTargetException();
            if (cause instanceof SecurityException) {
                return Result.failure(
                        "LOOKUP_DENIED",
                        "Access to ServiceManager.checkService was denied.",
                        3
                );
            }
            return Result.failure(
                    "LOOKUP_ERROR",
                    "ServiceManager.checkService failed.",
                    3
            );
        } catch (SecurityException error) {
            return Result.failure(
                    "LOOKUP_DENIED",
                    "Access to ServiceManager.checkService was denied.",
                    3
            );
        } catch (LinkageError error) {
            return lookupUnavailable();
        } catch (RemoteException error) {
            return Result.failure(
                    "SERVICE_UNREACHABLE",
                    "The protocol Binder identity check failed.",
                    4
            );
        }

        Parcel request = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            request.writeInterfaceToken(INTERFACE_DESCRIPTOR);
            boolean accepted = binder.transact(
                    TRANSACTION_IS_ENABLE,
                    request,
                    reply,
                    SYNCHRONOUS_FLAGS
            );
            if (!accepted) {
                return Result.failure(
                        "TRANSACTION_UNSUPPORTED",
                        "Binder rejected IProtocolManager transaction 1.",
                        5
                );
            }

            reply.readException();
            int rawValue = reply.readInt();
            if (reply.dataAvail() != 0) {
                return Result.failure(
                        "MALFORMED_REPLY",
                        "Transaction 1 returned trailing Parcel data.",
                        8
                );
            }
            if (rawValue == 0) {
                return Result.success(
                        "TRANSPORT_DISABLED",
                        false,
                        "ProtocolManagerService.isEnable returned false."
                );
            }
            if (rawValue == 1) {
                return Result.success(
                        "TRANSPORT_ENABLED",
                        true,
                        "ProtocolManagerService.isEnable returned true."
                );
            }
            return Result.failure(
                    "MALFORMED_REPLY",
                    "Transaction 1 returned a non-boolean integer.",
                    8
            );
        } catch (SecurityException error) {
            return Result.failure(
                    "TRANSACTION_DENIED",
                    "The service denied read-only transaction 1.",
                    6
            );
        } catch (RemoteException error) {
            return Result.failure(
                    "REMOTE_ERROR",
                    "Binder failed during read-only transaction 1.",
                    7
            );
        } catch (RuntimeException error) {
            return Result.failure(
                    "MALFORMED_REPLY",
                    "The transaction 1 reply could not be decoded.",
                    8
            );
        } finally {
            reply.recycle();
            request.recycle();
        }
    }

    private static Result lookupUnavailable() {
        return Result.failure(
                "LOOKUP_UNAVAILABLE",
                "ServiceManager.checkService is unavailable to this process.",
                3
        );
    }

    private static void emit(Result result) {
        System.out.println("finduas.protocol_check.version=" + OUTPUT_VERSION);
        System.out.println("finduas.protocol_check.service=" + SERVICE_NAME);
        System.out.println("finduas.protocol_check.interface=" + INTERFACE_DESCRIPTOR);
        System.out.println("finduas.protocol_check.caller_uid_system=true");
        System.out.println("finduas.protocol_check.transaction=" + TRANSACTION_IS_ENABLE);
        System.out.println("finduas.protocol_check.operation=isEnable_read_only");
        System.out.println("finduas.protocol_check.result=" + result.name);
        System.out.println("finduas.protocol_check.is_enable=" + result.value);
        System.out.println("finduas.protocol_check.detail=" + result.detail);
    }

    private static final class Result {
        private final String name;
        private final String value;
        private final String detail;
        private final int exitCode;

        private Result(String name, String value, String detail, int exitCode) {
            this.name = name;
            this.value = value;
            this.detail = detail;
            this.exitCode = exitCode;
        }

        private static Result success(
                String name,
                boolean value,
                String detail
        ) {
            return new Result(name, Boolean.toString(value), detail, 0);
        }

        private static Result failure(String name, String detail, int exitCode) {
            return new Result(name, "unknown", detail, exitCode);
        }
    }
}
