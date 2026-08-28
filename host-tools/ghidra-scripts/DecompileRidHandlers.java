// Targeted decompilation of RID parameter-handler functions recovered from GOT.
// @category DJIResearch

import java.util.HashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileRidHandlers extends GhidraScript {
    private static final long[] ENTRIES = {
        0x027e2960L, 0x026132b0L, 0x027e2a14L,
        0x02617ef8L, 0x027e3328L, 0x02618288L
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        Set<Address> done = new HashSet<>();

        for (long value : ENTRIES) {
            Address address = toAddr(value);
            disassemble(address);
            Function function = getFunctionAt(address);
            if (function == null) {
                function = createFunction(address, "rid_handler_" + Long.toHexString(value));
            }
            if (function == null || !done.add(function.getEntryPoint())) {
                println("NO_FUNCTION address=" + address);
                continue;
            }
            println("BEGIN_HANDLER entry=" + function.getEntryPoint() + " name=" + function.getName(true));
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_HANDLER entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
