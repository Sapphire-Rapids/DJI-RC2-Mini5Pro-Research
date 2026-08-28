// Offline helper: decompile exact function names supplied on the command line.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class DecompileNamedFunctions extends GhidraScript {
    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Could not open program in decompiler");
        }

        for (String requested : getScriptArgs()) {
            Function found = null;
            for (Function function : currentProgram.getFunctionManager().getFunctions(true)) {
                if (requested.equals(function.getName())) {
                    found = function;
                    break;
                }
            }
            if (found == null) {
                println("NO_FUNCTION name=" + requested);
                continue;
            }
            println("BEGIN_DECOMPILE name=" + requested + " entry=" + found.getEntryPoint());
            DecompileResults result = decompiler.decompileFunction(found, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_DECOMPILE name=" + requested);
        }
        decompiler.dispose();
    }
}
