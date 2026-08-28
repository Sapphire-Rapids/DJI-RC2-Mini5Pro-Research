// Describe whether exact addresses are ELF-visible entry points suitable for runtime lookup.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;

public class DescribeExportStatus extends GhidraScript {
    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            Address address = toAddr(Long.decode(arg));
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            Symbol primary = currentProgram.getSymbolTable().getPrimarySymbol(address);
            println("ADDRESS=" + address
                + " externalEntry=" + currentProgram.getSymbolTable().isExternalEntryPoint(address)
                + " function=" + (function == null ? "-" : function.getName(true))
                + " functionExternal=" + (function != null && function.isExternal())
                + " functionThunk=" + (function != null && function.isThunk())
                + " primary=" + (primary == null ? "-" : primary.getName(true))
                + " primarySource=" + (primary == null ? "-" : primary.getSource())
                + " primaryExternal=" + (primary != null && primary.isExternal())
                + " primaryGlobal=" + (primary != null && primary.isGlobal()));
        }
    }
}
