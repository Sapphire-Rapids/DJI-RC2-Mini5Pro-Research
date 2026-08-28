// Read-only symbol/address inventory for current DJI FC config parameter helpers.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class MineParamSymbols extends GhidraScript {
    private static final String[] NEEDLES = {
        "FlightControllerConfigManager10ReadConfig",
        "FlightControllerConfigManager11WriteConfig",
        "FlightControllerConfigManager11ResetConfig",
        "FlightControllerConfigManager17GetConfigKeyInfos",
        "FCConfigHelper7Execute",
        "SetConfigValueHandlerINS0_7BoolMsg",
        "GetConfigValueHandlerINS0_7BoolMsg",
        "SetConfigValueHandlerINS0_6IntMsg",
        "GetConfigValueHandlerINS0_6IntMsg",
        "CCacheConfigKeyInfoC2"
    };

    private boolean wanted(String name) {
        for (String needle : NEEDLES) {
            if (name.contains(needle)) return true;
        }
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
