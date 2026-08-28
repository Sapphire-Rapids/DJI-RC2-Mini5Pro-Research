// Search the current program symbol table for all supplied substrings.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class SearchSymbols extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] needles = getScriptArgs();
        SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
        while (it.hasNext()) {
            Symbol symbol = it.next();
            String name = symbol.getName(true);
            for (String needle : needles) {
                if (name.contains(needle)) {
                    println(symbol.getAddress() + " " + symbol.getSymbolType() + " " + name);
                    break;
                }
            }
        }
    }
}
