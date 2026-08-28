// Decompile only RID capability/status handlers fed by the 0x11/0x1c push.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileRidStatusHandlers extends GhidraScript {
    private static boolean relevant(String name) {
        return name.contains("KeyIsCloudRIDSupportedPush") ||
            name.contains("KeyIsJapaneseRidSupportedPush") ||
            name.contains("KeyIsEURidSupported") ||
            name.contains("KeyIsFREidSupported") ||
            name.contains("KeyIsUSRiddSupportedPush") ||
            name.contains("OnRIDWorkingStatusPush");
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
            println("BEGIN_RID_STATUS_HANDLER entry=" + function.getEntryPoint() + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_RID_STATUS_HANDLER entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
