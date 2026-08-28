// Inspect the narrow set of call targets used by RID named-parameter registration.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;

public class InspectRegistrationHelpers extends GhidraScript {
    private static final long[] TARGETS = {
        0x05082c20L, 0x05082fa0L, 0x02d0129cL, 0x02d013dcL,
        0x0505b770L, 0x0505b700L, 0x0505b740L,
        0x02a3c200L, 0x02a58a98L, 0x028d78ccL, 0x028d794cL
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long value : TARGETS) {
            Address address = toAddr(value);
            Function function = getFunctionAt(address);
            Symbol symbol = getSymbolAt(address);
            println("HELPER address=" + address + " symbol=" +
                (symbol == null ? "<none>" : symbol.getName(true)) + " function=" +
                (function == null ? "<none>" : function.getName(true)));
            if (function == null) {
                continue;
            }
            DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
        }
        decompiler.dispose();
    }
}
