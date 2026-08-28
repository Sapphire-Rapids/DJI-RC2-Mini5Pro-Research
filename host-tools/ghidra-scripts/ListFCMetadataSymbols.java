// Read-only symbol inventory for FlightControllerConfigManager metadata/cache flow.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ListFCMetadataSymbols extends GhidraScript {
    private static final long[] STARTS = { 0x01f1de00L, 0x01f50000L, 0x03b64400L };

    @Override
    protected void run() throws Exception {
        for (long startValue : STARTS) {
            Address start = toAddr(startValue);
            println("START " + start);
            SymbolIterator symbols = currentProgram.getSymbolTable().getSymbolIterator(start, true);
            int count = 0;
            while (symbols.hasNext() && count < 180) {
                Symbol symbol = symbols.next();
                println(" SYMBOL " + symbol.getAddress() + " " + symbol.getName(true) +
                    " type=" + symbol.getSymbolType() + " source=" + symbol.getSource());
                count++;
            }
        }
    }
}
