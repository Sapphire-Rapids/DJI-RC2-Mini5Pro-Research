// Read-only symbol mining for higher-level FC config metadata flow.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class MineFCConfigFlowSymbols extends GhidraScript {
    private static final String[] NEEDLES = {
        "CCacheConfigKeyInfo",
        "FlightControllerConfigManager",
        "FlightControllerAbstraction",
        "FCConfigInfo",
        "FCConfigHelper",
        "ConfigKeyInfo"
    };

    private boolean wanted(String name) {
        for (String needle : NEEDLES) if (name.contains(needle)) return true;
        return false;
    }

    @Override
    protected void run() throws Exception {
        SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
        while (it.hasNext()) {
            Symbol symbol = it.next();
            String name = symbol.getName(true);
            if (wanted(name)) {
                println(symbol.getAddress() + " " + symbol.getSymbolType() + " " + name);
            }
        }
    }
}
