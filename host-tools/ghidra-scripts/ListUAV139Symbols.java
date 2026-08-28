// Read-only inventory of concrete UAV139 and shared UAV77 abstraction symbols.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ListUAV139Symbols extends GhidraScript {
    @Override
    protected void run() throws Exception {
        SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
        while (it.hasNext()) {
            Symbol symbol = it.next();
            String name = symbol.getName(true);
            if (name.contains("UAV139FCAbs") ||
                name.contains("UAV77FlightControllerAbstraction")) {
                println(symbol.getAddress() + " " + symbol.getSymbolType() + " " + name);
            }
        }
    }
}
