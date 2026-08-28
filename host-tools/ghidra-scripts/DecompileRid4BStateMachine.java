// Offline, read-only recovery of the DJI Fly 1.21.10 RidImportModule state machine.
// The mini-debug symbols import as one-byte function bodies, so this script
// temporarily expands each body to the next exact symbol boundary before
// decompiling. Run with -readOnly; no project or binary changes are saved.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileRid4BStateMachine extends GhidraScript {
    private static final long[][] RANGES = {
        {0x02ce5cacL, 0x02ce6a20L}, // CreateCharacteristics
        {0x02ce6a20L, 0x02ce6ac8L}, // Setup
        {0x02ce6ac8L, 0x02ce6ec4L}, // SetRIDReqPack
        {0x02ce6ec4L, 0x02ce71f0L}, // CheckRIDRspPack
        {0x02ce71f0L, 0x02ce73acL}, // SendRIDReqPack
        {0x02ce73acL, 0x02ce85b4L}, // SetNonceInfo
        {0x02ce85b4L, 0x02ce96d8L}, // SetSharedKey
        {0x02ce96d8L, 0x02cea4c8L}, // SetRIDInfo
        {0x02cea4c8L, 0x02cea7e8L}, // ParseNonceInfoRsp
        {0x02cea7e8L, 0x02ceae28L}, // ParseSharedKeyRsp
        {0x02ceae28L, 0x02ceb374L}, // GetRIDInfo
        {0x02ceb374L, 0x02cebc68L}, // ActionRIDRegistedInfo
        {0x02cebc68L, 0x02cec48cL}, // GetRIDImportResult
        {0x02cec48cL, 0x02cec558L}, // ConvertRetCodeToErrorCode
        {0x02cec558L, 0x02cf01ecL}, // OnRIDWorkingStatusPush
        {0x02cf038cL, 0x02cf0420L}  // 0x11/0x4b request constructor
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("could not open program in decompiler");
        }
        for (long[] range : RANGES) {
            long start = range[0];
            long endExclusive = range[1];
            Address entry = toAddr(start);
            for (long at = start; at < endExclusive; at += 4) {
                disassemble(toAddr(at));
            }
            Function function = getFunctionAt(entry);
            if (function == null) {
                function = createFunction(entry, null);
            }
            if (function == null) {
                println(String.format("NO_FUNCTION %08x", start));
                continue;
            }
            function.setBody(new AddressSet(entry, toAddr(endExclusive - 1)));
            println(String.format("BEGIN_RID4B %08x-%08x %s", start,
                endExclusive - 1, function.getName(true)));
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println(String.format("END_RID4B %08x", start));
        }
        decompiler.dispose();
    }
}
