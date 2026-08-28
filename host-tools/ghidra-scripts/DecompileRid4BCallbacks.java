// Recover the anonymous std::function operators used by RidImportModule.
// Vtable slot +0x30 is operator(); slot +0x38 supplies the next boundary.
// Run with -readOnly.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileRid4BCallbacks extends GhidraScript {
    private static final long[][] RANGES = {
        {0x02cec914L, 0x02ceccb0L}, // SetNonceInfo response callback
        {0x02ced064L, 0x02ced358L}, // SetSharedKey response callback
        {0x02ced6f8L, 0x02ced9ecL}, // SetRIDInfo response callback
        {0x02cede50L, 0x02cedf60L}, // query-nonce response callback
        {0x02cee350L, 0x02ceea18L}  // initial query registration-code callback
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("could not open program");
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
                function = createFunction(entry, "rid4b_callback_" + Long.toHexString(start));
            }
            if (function == null) {
                println(String.format("NO_FUNCTION %08x", start));
                continue;
            }
            function.setBody(new AddressSet(entry, toAddr(endExclusive - 1)));
            println(String.format("BEGIN_RID4B_CALLBACK %08x-%08x %s", start,
                endExclusive - 1, function.getName(true)));
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println(String.format("END_RID4B_CALLBACK %08x", start));
        }
        decompiler.dispose();
    }
}
