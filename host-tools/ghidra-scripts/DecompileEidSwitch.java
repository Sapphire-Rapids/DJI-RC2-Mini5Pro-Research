// Recover the current SDK's French EID get/set packet handling.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileEidSwitch extends GhidraScript {
    private static boolean relevant(String name) {
        return name.contains("EIDSwitchGet") || name.contains("EIDSwitchSet") ||
            name.contains("GetEIDSwitch") || name.contains("SetEIDSwitch") ||
            name.contains("uav_fc_handle_eid_switch") || name.contains("eid_switch_pack");
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
            println("BEGIN_EID entry=" + function.getEntryPoint() + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_EID entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
