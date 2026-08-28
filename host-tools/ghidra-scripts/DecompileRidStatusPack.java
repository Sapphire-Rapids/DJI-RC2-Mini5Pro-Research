// Recover the observer registration constants for RidWorkingStatusPush.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileRidStatusPack extends GhidraScript {
    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            if (!name.contains("adsb_push_rid_working_status_pack")) {
                continue;
            }
            if (!(name.contains("PackObserverHelper") || name.contains("RegisterPackObserver") ||
                  name.contains("ObserverPushPack"))) {
                continue;
            }
            println("BEGIN_RID_STATUS_PACK entry=" + function.getEntryPoint() + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_RID_STATUS_PACK entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
