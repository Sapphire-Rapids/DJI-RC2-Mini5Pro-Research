// List functions whose qualified name contains any supplied substring.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ListFunctionsByNeedle extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] needles = getScriptArgs();
        if (needles.length == 0) {
            throw new IllegalArgumentException("at least one name substring is required");
        }
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String qualified = function.getName(true);
            for (String needle : needles) {
                if (qualified.contains(needle)) {
                    println("MATCH entry=" + function.getEntryPoint()
                        + " size=" + function.getBody().getNumAddresses()
                        + " thunk=" + function.isThunk()
                        + " name=" + qualified);
                    break;
                }
            }
        }
    }
}
