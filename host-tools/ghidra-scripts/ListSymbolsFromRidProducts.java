// List dynamic/imported symbols from RID-relevant product CreateCharacteristics entries.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ListSymbolsFromRidProducts extends GhidraScript {
    private static final long[] STARTS = { 0x03046164L, 0x030f8b30L };

    @Override
    protected void run() throws Exception {
        for (long startValue : STARTS) {
            Address start = toAddr(startValue);
            println("START " + start);
            SymbolIterator symbols = currentProgram.getSymbolTable().getSymbolIterator(start, true);
            int count = 0;
            while (symbols.hasNext() && count < 80) {
                Symbol symbol = symbols.next();
                println(" SYMBOL " + symbol.getAddress() + " " + symbol.getName(true) +
                    " type=" + symbol.getSymbolType() + " source=" + symbol.getSource());
                count++;
            }
        }
    }
}
