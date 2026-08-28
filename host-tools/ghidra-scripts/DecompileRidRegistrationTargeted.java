// Create and inspect only the two large product-abstraction constructors that
// register the RID-related named parameters. The entry points were recovered
// by bounded AArch64 prologue/return scans around exact literal references.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileRidRegistrationTargeted extends GhidraScript {
    private static final long[][] TARGETS = {
        {0x02fb3ba8L, 0x02fbb838L},
        {0x030c5524L, 0x030c8cccL}
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        for (long[] target : TARGETS) {
            Address entry = toAddr(target[0]);
            Address site = toAddr(target[1]);
            disassemble(entry);
            Function function = getFunctionAt(entry);
            if (function == null) {
                function = createFunction(entry, "rid_registration_" + Long.toHexString(target[0]));
            }
            println("TARGET entry=" + entry + " site=" + site + " function=" +
                (function == null ? "<none>" : function.getName(true)) + " contains=" +
                (function != null && function.getBody().contains(site)));
            if (function == null) {
                continue;
            }
            println("BODY ranges=" + function.getBody());
            DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println("BEGIN_TARGET_DECOMPILE " + entry);
                println(result.getDecompiledFunction().getC());
                println("END_TARGET_DECOMPILE " + entry);
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
        }
        decompiler.dispose();
    }
}
