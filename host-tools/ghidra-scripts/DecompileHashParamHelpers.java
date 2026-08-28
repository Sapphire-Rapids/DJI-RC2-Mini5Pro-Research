// Decompile the SDK helper that batches modern FC hash-parameter reads.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileHashParamHelpers extends GhidraScript {
    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            if (!name.contains("MergeKeyGetHelperBaseINS_4core23action_read_hash_pa_ram")) {
                continue;
            }
            println("BEGIN_MERGE_HASH entry=" + function.getEntryPoint() + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_MERGE_HASH entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
