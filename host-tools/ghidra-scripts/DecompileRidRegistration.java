// Decompile two representative RID key-registration sites.
// @category DJIResearch

import java.util.HashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileRidRegistration extends GhidraScript {
    private static final long[] SITES = { 0x02fbb838L, 0x030c8cccL };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        Set<Address> done = new HashSet<>();
        for (long value : SITES) {
            Address site = toAddr(value);
            Function function = getFunctionContaining(site);
            println("SITE=" + site + " function=" +
                (function == null ? "<none>" : function.getName(true)));
            if (function == null || !done.add(function.getEntryPoint())) {
                continue;
            }
            println("BEGIN_REGISTRATION entry=" + function.getEntryPoint() +
                " name=" + function.getName(true));
            DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_REGISTRATION entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
