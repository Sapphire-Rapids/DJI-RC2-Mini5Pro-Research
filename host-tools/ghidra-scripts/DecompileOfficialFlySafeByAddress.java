// Decompile one or more exact addresses from the current official FlySafe project.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileOfficialFlySafeByAddress extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0) {
            throw new IllegalArgumentException("at least one hex address is required");
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Could not open program in decompiler");
        }
        for (String arg : args) {
            Address address = toAddr(Long.decode(arg));
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                println("NO_FUNCTION address=" + address);
                continue;
            }
            println("BEGIN_EXACT entry=" + address + " name=" + function.getName(true));
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_EXACT entry=" + address);
        }
        decompiler.dispose();
    }
}
