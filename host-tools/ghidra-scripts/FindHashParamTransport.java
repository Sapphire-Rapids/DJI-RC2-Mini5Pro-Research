// Locate and decompile only the modern flight-controller hash-parameter transport.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class FindHashParamTransport extends GhidraScript {
    private static boolean relevant(String name) {
        return name.contains("get_get_cfg_item_info_by_hash") ||
            name.contains("read_hash_param") ||
            name.contains("write_hash_param");
    }

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            if (!relevant(name)) {
                continue;
            }
            println("BEGIN_HASH_PARAM entry=" + function.getEntryPoint() + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 90, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_HASH_PARAM entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
