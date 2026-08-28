// Identify product abstraction constructors containing the two RID parameter mappings.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class FindRidProductConstructors extends GhidraScript {
    @Override
    protected void run() throws Exception {
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            if ((name.contains("UAV110FCAbs") || name.contains("UAV113FCAbs")) &&
                name.contains("CreateCharacteristics")) {
                println("PRODUCT_CTOR entry=" + function.getEntryPoint() + " name=" + name +
                    " body=" + function.getBody() +
                    " hasCcc=" + function.getBody().contains(toAddr(0x02fbb838L)) +
                    " hasC0=" + function.getBody().contains(toAddr(0x030c8cccL)));
            }
        }
    }
}
