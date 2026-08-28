// Offline helper: decompile only the requested virtual addresses from an existing project.
// Usage: -postScript DecompileAtAddresses.java 0x5eeecc 0x5ef2ac
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileAtAddresses extends GhidraScript {
    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Could not open program in decompiler");
        }

        for (String arg : getScriptArgs()) {
            long offset = Long.decode(arg);
            Address address = currentProgram.getAddressFactory()
                .getDefaultAddressSpace().getAddress(offset);
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                function = currentProgram.getFunctionManager().getFunctionContaining(address);
            }
            if (function == null) {
                println("NO_FUNCTION address=" + address);
                continue;
            }
            println("BEGIN_DECOMPILE requested=" + arg + " entry="
                + function.getEntryPoint() + " name=" + function.getName(true));
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_DECOMPILE requested=" + arg);
        }
        decompiler.dispose();
    }
}
