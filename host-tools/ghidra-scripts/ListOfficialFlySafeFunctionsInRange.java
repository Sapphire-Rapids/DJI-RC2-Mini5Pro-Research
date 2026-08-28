// List all functions whose entry points fall in an inclusive address range.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ListOfficialFlySafeFunctionsInRange extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("start and end hex addresses are required");
        }
        Address start = toAddr(Long.decode(args[0]));
        Address end = toAddr(Long.decode(args[1]));
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(start, true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            if (function.getEntryPoint().compareTo(end) > 0) {
                break;
            }
            println("RANGE_FUNCTION entry=" + function.getEntryPoint()
                + " size=" + function.getBody().getNumAddresses()
                + " name=" + function.getName(true));
        }
    }
}
