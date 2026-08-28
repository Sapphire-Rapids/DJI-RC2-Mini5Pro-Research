// Work-only recovery of the MSDK 5.18 QueryLicenseFromFC queued task vtable.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileFlySafeLicenseTask extends GhidraScript {
    private static final long[] TARGETS = {
        0x01c8f7e4L, 0x01c8f830L, 0x01c8f88cL, 0x01c8f930L,
        0x01c8f9c0L, 0x01c8fa00L, 0x01c8fa50L, 0x01c8fcd8L,
        0x01c8fcf4L
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        decompiler.openProgram(currentProgram);
        for (int i = 0; i < TARGETS.length; i++) {
            long target = TARGETS[i];
            long endExclusive = i + 1 < TARGETS.length ? TARGETS[i + 1] : target + 0x100;
            Address address = toAddr(target);
            for (long at = target; at < endExclusive; at += 4) {
                disassemble(toAddr(at));
            }
            Function function = getFunctionAt(address);
            if (function == null) {
                function = createFunction(address, "flysafe_license_task_" + Long.toHexString(target));
            }
            if (function != null) {
                function.setBody(new AddressSet(address, toAddr(endExclusive - 1)));
            }
            println(String.format("BEGIN_FLYSAFE_TASK %08x %s", target,
                function == null ? "<none>" : function.getName(true)));
            if (function != null) {
                DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
                if (result != null && result.decompileCompleted()
                        && result.getDecompiledFunction() != null) {
                    println(result.getDecompiledFunction().getC());
                } else {
                    println("DECOMPILE_FAILED="
                        + (result == null ? "null" : result.getErrorMessage()));
                }
            }
            println(String.format("END_FLYSAFE_TASK %08x", target));
        }
        decompiler.dispose();
    }
}
