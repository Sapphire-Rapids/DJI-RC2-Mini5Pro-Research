package com.finduas.bridge;

import android.os.Binder;
import android.os.IBinder;
import android.os.IInterface;
import android.os.Parcel;
import android.os.Process;
import android.os.RemoteException;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * One-shot, read-only diagnostic for the adjacent RC331 "protocol" Binder ABI.
 *
 * <p>The only protocol request this class can construct is the hard-coded France EID GET:
 * sender 2/4 -> receiver 0x12/0x04, command 0x03/0x77, payload 0x02. It deliberately has no
 * argument parser, generic packet builder, SET request, socket transport, or persistence.</p>
 */
public final class FranceEidGetMain {
    private static final String SERVICE_NAME = "protocol";
    private static final String PROTOCOL_DESCRIPTOR = "com.dji.protocol.IProtocolManager";
    private static final String LISTENER_DESCRIPTOR = "com.dji.protocol.IPackListener";

    private static final int SYSTEM_UID = 1000;
    private static final int TRANSACTION_SEND_WITH_LISTEN = 4;
    private static final int CALLBACK_SUCCESS = 1;
    private static final int CALLBACK_FAILURE = 2;

    private static final int SENDER_TYPE = 0x02;
    private static final int SENDER_ID = 0x04;
    private static final int RECEIVER_TYPE = 0x12;
    private static final int RECEIVER_ID = 0x04;
    private static final int CMD_SET = 0x03;
    private static final int CMD_ID = 0x77;
    private static final int CMD_TYPE_REQUEST = 0;
    private static final int CMD_TYPE_ACK = 1;
    private static final int NEED_ACK_AFTER_EXEC = 2;
    private static final int ENCRYPTION_NONE = 0;
    private static final int TIMEOUT_MS = 500;
    private static final int PROCESS_WAIT_MS = 5000;
    private static final byte GET_OPERATION = 0x02;

    private static final int EXIT_USAGE = 64;
    private static final int EXIT_WRONG_UID = 65;
    private static final int EXIT_LOOKUP_FAILED = 66;
    private static final int EXIT_SERVICE_ABSENT = 67;
    private static final int EXIT_SERVICE_MISMATCH = 68;
    private static final int EXIT_TRANSACTION_FAILED = 69;
    private static final int EXIT_EXCEPTION = 70;
    private static final int EXIT_CALLBACK_TIMEOUT = 71;
    private static final int EXIT_PROTOCOL_FAILURE = 72;
    private static final int EXIT_MALFORMED_ACK = 73;

    private FranceEidGetMain() {
    }

    public static void main(String[] args) {
        int exit = run(args);
        System.exit(exit);
    }

    static int run(String[] args) {
        if (args == null || args.length != 0) {
            fail("arguments are forbidden; this probe has exactly one hard-coded GET");
            return EXIT_USAGE;
        }
        if (Process.myUid() != SYSTEM_UID) {
            fail("caller UID is not the required system UID 1000");
            return EXIT_WRONG_UID;
        }

        final IBinder service;
        try {
            service = checkService(SERVICE_NAME);
        } catch (ReflectiveOperationException | SecurityException e) {
            fail("ServiceManager.checkService failed: " + e.getClass().getSimpleName());
            return EXIT_LOOKUP_FAILED;
        }
        if (service == null) {
            fail("Binder service 'protocol' is absent; no request was sent");
            return EXIT_SERVICE_ABSENT;
        }

        try {
            if (!service.pingBinder()) {
                fail("Binder service is not alive; no request was sent");
                return EXIT_SERVICE_MISMATCH;
            }
            String descriptor = service.getInterfaceDescriptor();
            if (!PROTOCOL_DESCRIPTOR.equals(descriptor)) {
                fail("unexpected Binder descriptor; no request was sent");
                return EXIT_SERVICE_MISMATCH;
            }
        } catch (RemoteException | RuntimeException e) {
            fail("Binder identity check failed: " + e.getClass().getSimpleName());
            return EXIT_SERVICE_MISMATCH;
        }

        ResultCallback callback = new ResultCallback();
        Parcel request = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        try {
            request.writeInterfaceToken(PROTOCOL_DESCRIPTOR);
            request.writeInt(1); // non-null Pack
            writeHardCodedGetPack(request);
            request.writeStrongBinder(callback.asBinder());

            boolean dispatched = service.transact(
                    TRANSACTION_SEND_WITH_LISTEN, request, reply, 0);
            if (!dispatched) {
                fail("Binder transaction 4 was rejected");
                return EXIT_TRANSACTION_FAILED;
            }
            reply.readException();
        } catch (RemoteException | RuntimeException e) {
            fail("read-only GET dispatch failed: " + e.getClass().getSimpleName());
            return EXIT_EXCEPTION;
        } finally {
            reply.recycle();
            request.recycle();
        }

        try {
            if (!callback.await(PROCESS_WAIT_MS)) {
                fail("no correlated callback within 5000 ms");
                return EXIT_CALLBACK_TIMEOUT;
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            fail("interrupted while waiting for callback");
            return EXIT_EXCEPTION;
        }
        return callback.exitCode();
    }

    private static IBinder checkService(String name)
            throws ReflectiveOperationException {
        Class<?> serviceManager = Class.forName("android.os.ServiceManager");
        Method method = serviceManager.getDeclaredMethod("checkService", String.class);
        try {
            return (IBinder) method.invoke(null, name);
        } catch (InvocationTargetException e) {
            Throwable cause = e.getCause();
            if (cause instanceof SecurityException) {
                throw (SecurityException) cause;
            }
            throw e;
        }
    }

    /** Exact com.dji.protocol.Pack.writeToParcel order from adjacent RC331 framework.jar. */
    private static void writeHardCodedGetPack(Parcel parcel) {
        parcel.writeByte((byte) 0x55); // sof
        parcel.writeInt(1);            // version
        parcel.writeInt(0);            // length: server doPack recomputes
        parcel.writeInt(0);            // crc8: server native_fillCrc recomputes
        parcel.writeInt(SENDER_ID);
        parcel.writeInt(SENDER_TYPE);
        parcel.writeInt(RECEIVER_ID);
        parcel.writeInt(RECEIVER_TYPE);
        parcel.writeInt(-1);           // seq: server doPack allocates
        parcel.writeInt(CMD_TYPE_REQUEST);
        parcel.writeInt(NEED_ACK_AFTER_EXEC);
        parcel.writeInt(CMD_TYPE_REQUEST); // duplicated by the vendor Parcelable ABI
        parcel.writeInt(ENCRYPTION_NONE);
        parcel.writeInt(CMD_SET);
        parcel.writeInt(CMD_ID);
        parcel.writeInt(1);            // vendor's explicit data length
        parcel.writeByteArray(new byte[]{GET_OPERATION}); // Parcel adds its own array length
        parcel.writeInt(0);            // ccode
        parcel.writeInt(0);            // crc16: server native_fillCrc recomputes
        parcel.writeInt(TIMEOUT_MS);
        parcel.writeInt(0);            // retryCnt
        // maxRetryCnt is absent from the adjacent vendor Parcelable ABI.
    }

    private static void fail(String message) {
        System.err.println("FAIL_CLOSED " + message);
    }

    private static final class ResultCallback extends Binder implements IInterface {
        private final CountDownLatch done = new CountDownLatch(1);
        private final AtomicInteger result = new AtomicInteger(EXIT_CALLBACK_TIMEOUT);

        ResultCallback() {
            attachInterface(this, LISTENER_DESCRIPTOR);
        }

        @Override
        public IBinder asBinder() {
            return this;
        }

        @Override
        protected boolean onTransact(int code, Parcel data, Parcel reply, int flags)
                throws RemoteException {
            if (code == IBinder.INTERFACE_TRANSACTION) {
                if (reply != null) {
                    reply.writeString(LISTENER_DESCRIPTOR);
                }
                return true;
            }
            if (code == CALLBACK_SUCCESS) {
                data.enforceInterface(LISTENER_DESCRIPTOR);
                handleSuccess(data);
                return true;
            }
            if (code == CALLBACK_FAILURE) {
                data.enforceInterface(LISTENER_DESCRIPTOR);
                handleFailure(data);
                return true;
            }
            return super.onTransact(code, data, reply, flags);
        }

        private void handleSuccess(Parcel parcel) {
            try {
                if (parcel.readInt() == 0) {
                    malformed("null Pack callback");
                    return;
                }
                ParsedPack pack = ParsedPack.readFrom(parcel);
                if (parcel.dataAvail() != 0) {
                    malformed("trailing callback parcel data");
                    return;
                }
                String problem = validateAck(pack);
                if (problem != null) {
                    malformed(problem);
                    return;
                }
                int state = pack.data[0] & 0xff;
                System.out.println(
                        "OK france_eid_only=" + (state == 1 ? "enabled" : "disabled")
                                + " value=" + state + " ccode=0");
                result.set(0);
            } catch (RuntimeException e) {
                malformed("Pack parcel parse failed: " + e.getClass().getSimpleName());
                return;
            } finally {
                done.countDown();
            }
        }

        private void handleFailure(Parcel parcel) {
            try {
                if (parcel.readInt() == 0) {
                    fail("vendor callback reported a null ECode");
                } else {
                    int id = parcel.readInt();
                    int explicitLength = parcel.readInt();
                    if (explicitLength < 0 || explicitLength > 4096) {
                        malformed("invalid ECode description length");
                        return;
                    }
                    if (explicitLength > 0) {
                        byte[] description = new byte[explicitLength];
                        parcel.readByteArray(description);
                    }
                    if (parcel.dataAvail() != 0) {
                        malformed("trailing ECode parcel data");
                        return;
                    }
                    fail("vendor protocol callback failure id=" + id);
                }
                result.set(EXIT_PROTOCOL_FAILURE);
            } catch (RuntimeException e) {
                malformed("ECode parcel parse failed: " + e.getClass().getSimpleName());
                return;
            } finally {
                done.countDown();
            }
        }

        private void malformed(String reason) {
            fail("malformed or mismatched ACK: " + reason);
            result.set(EXIT_MALFORMED_ACK);
        }

        boolean await(long timeoutMs) throws InterruptedException {
            return done.await(timeoutMs, TimeUnit.MILLISECONDS);
        }

        int exitCode() {
            return result.get();
        }
    }

    private static String validateAck(ParsedPack pack) {
        if ((pack.sof & 0xff) != 0x55 || pack.version != 1 || pack.length != 15) {
            return "unexpected frame envelope";
        }
        if (pack.senderType != RECEIVER_TYPE || pack.senderId != RECEIVER_ID
                || pack.receiverType != SENDER_TYPE || pack.receiverId != SENDER_ID) {
            return "route is not the exact reverse of the fixed request";
        }
        if (pack.seq < 0 || pack.seq > 0xffff) {
            return "sequence is outside DUML v1 range";
        }
        if (pack.cmdType != CMD_TYPE_ACK || pack.duplicateCmdType != CMD_TYPE_ACK) {
            return "response cmdType is not ACK";
        }
        if (pack.isNeedAck != 0 && pack.isNeedAck != NEED_ACK_AFTER_EXEC) {
            return "unexpected ACK policy bits";
        }
        if (pack.encryptType != ENCRYPTION_NONE) {
            return "encrypted callback cannot be interpreted by this clear-only probe";
        }
        if (pack.cmdSet != CMD_SET || pack.cmdId != CMD_ID) {
            return "command does not match 0x03/0x77";
        }
        if (pack.ccode != 0) {
            return "nonzero ccode=" + pack.ccode;
        }
        if (pack.data == null || pack.data.length != 1) {
            return "GET ACK must contain exactly one state byte after ccode";
        }
        int state = pack.data[0] & 0xff;
        if (state != 0 && state != 1) {
            return "state byte is outside {0,1}";
        }
        return null;
    }

    /** Exact inverse of adjacent RC331 com.dji.protocol.Pack(Parcel). */
    private static final class ParsedPack {
        byte sof;
        int version;
        int length;
        int crc8;
        int senderId;
        int senderType;
        int receiverId;
        int receiverType;
        int seq;
        int cmdType;
        int isNeedAck;
        int duplicateCmdType;
        int encryptType;
        int cmdSet;
        int cmdId;
        byte[] data;
        int ccode;
        int crc16;
        int timeOut;
        int retryCnt;

        static ParsedPack readFrom(Parcel parcel) {
            ParsedPack pack = new ParsedPack();
            pack.sof = parcel.readByte();
            pack.version = parcel.readInt();
            pack.length = parcel.readInt();
            pack.crc8 = parcel.readInt();
            pack.senderId = parcel.readInt();
            pack.senderType = parcel.readInt();
            pack.receiverId = parcel.readInt();
            pack.receiverType = parcel.readInt();
            pack.seq = parcel.readInt();
            pack.cmdType = parcel.readInt();
            pack.isNeedAck = parcel.readInt();
            pack.duplicateCmdType = parcel.readInt();
            pack.encryptType = parcel.readInt();
            pack.cmdSet = parcel.readInt();
            pack.cmdId = parcel.readInt();
            int explicitLength = parcel.readInt();
            if (explicitLength < 0 || explicitLength > 4096) {
                throw new IllegalArgumentException("invalid Pack data length");
            }
            if (explicitLength > 0) {
                pack.data = new byte[explicitLength];
                parcel.readByteArray(pack.data);
            }
            pack.ccode = parcel.readInt();
            pack.crc16 = parcel.readInt();
            pack.timeOut = parcel.readInt();
            pack.retryCnt = parcel.readInt();
            return pack;
        }
    }
}
