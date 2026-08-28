// Targeted, read-only decompilation of current DJI FC config helper functions.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class DecompileParamHelpers extends GhidraScript {
    private static final String[] NEEDLES = {
        "FlightControllerConfigManager10ReadConfig",
        "FlightControllerConfigManager11WriteConfig",
        "FCConfigHelper7Execute",
        "SetConfigValueHandlerINS0_7BoolMsg",
        "SetConfigValueHandlerINS0_6IntMsg"
    };

    private boolean wanted(String name) {
        for (String needle : NEEDLES) if (name.contains(needle)) return true;
        return false;
    }

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
        while (it.hasNext()) {
            Symbol symbol = it.next();
            String name = symbol.getName(true);
            if (!wanted(name)) continue;
            Function function = getFunctionAt(symbol.getAddress());
            println("BEGIN " + symbol.getAddress() + " " + name);
            if (function == null) {
                disassemble(symbol.getAddress());
                function = createFunction(symbol.getAddress(), null);
            }
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("FAILED " + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END " + symbol.getAddress());
        }
        decompiler.dispose();
    }
}
