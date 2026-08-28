// Read-only decompilation of the concrete wa150 UAV139 setup function.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class DecompileUAV139WillSetup extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Function function = getFunctionAt(toAddr(0x0329a84cL));
        if (function == null) {
            disassemble(toAddr(0x0329a84cL));
            function = createFunction(toAddr(0x0329a84cL), null);
        }
        println("BEGIN " + function.getEntryPoint() + " " + function.getName(true));
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        DecompileResults result = decompiler.decompileFunction(function, 600, monitor);
        if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
            println(result.getDecompiledFunction().getC());
        }
        else {
            println("DECOMPILE_FAILED " + result.getErrorMessage());
        }
        decompiler.dispose();
        println("END " + function.getEntryPoint());
    }
}
