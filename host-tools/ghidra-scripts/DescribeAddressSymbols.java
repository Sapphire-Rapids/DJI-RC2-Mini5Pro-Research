// Print symbols and functions whose entry/target matches each requested address.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;

public class DescribeAddressSymbols extends GhidraScript {
    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            Address address = toAddr(Long.decode(arg));
            println("ADDRESS=" + address);
            Function at = currentProgram.getFunctionManager().getFunctionAt(address);
            Function containing = currentProgram.getFunctionManager().getFunctionContaining(address);
            println("  functionAt=" + (at == null ? "-" : at.getName(true)));
            println("  containing=" + (containing == null ? "-" : containing.getName(true)));
            for (Symbol symbol : currentProgram.getSymbolTable().getSymbols(address)) {
                println("  symbol=" + symbol.getName(true) + " type=" + symbol.getSymbolType()
                    + " source=" + symbol.getSource());
            }
        }
    }
}
