// List functions whose entry points fall in an address interval.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ListFunctionsRange extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("start and end-exclusive addresses required");
        }
        Address start = toAddr(Long.decode(args[0]));
        Address end = toAddr(Long.decode(args[1]));
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(start, true);
        while (it.hasNext()) {
            Function function = it.next();
            if (function.getEntryPoint().compareTo(end) >= 0) {
                break;
            }
            println(function.getEntryPoint() + "-" + function.getBody().getMaxAddress() + " " +
                function.getName(true));
        }
    }
}
