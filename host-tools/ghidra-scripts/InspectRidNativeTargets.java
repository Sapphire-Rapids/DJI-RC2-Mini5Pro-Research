// Read-only inventory around the two RID-related generated registration blocks
// and the FC hash-parameter transport functions.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class InspectRidNativeTargets extends GhidraScript {
    private static final long[] SITES = {
        0x030bb838L, 0x031c8cccL,
        0x01f1e234L, 0x01f1e500L, 0x01f1f410L,
        0x02c42934L, 0x02c42ad4L, 0x02c4342cL, 0x02c435e0L
    };

    @Override
    protected void run() throws Exception {
        for (long value : SITES) {
            Address site = toAddr(value);
            Function containing = getFunctionContaining(site);
            Symbol primary = currentProgram.getSymbolTable().getPrimarySymbol(site);
            println("SITE " + site +
                " primary=" + (primary == null ? "<none>" : primary.getName(true)) +
                " containing=" + describe(containing));

            Address lo = site.subtract(Math.min(0x20000L, site.getOffset()));
            Address hi = site.add(0x20000L);
            SymbolIterator symbols = currentProgram.getSymbolTable().getSymbolIterator(lo, true);
            int emitted = 0;
            while (symbols.hasNext()) {
                Symbol symbol = symbols.next();
                if (symbol.getAddress().compareTo(hi) > 0) break;
                String name = symbol.getName(true);
                if (name.contains("Abstraction") || name.contains("Config") ||
                    name.contains("hash_param") || name.contains("HashParam") ||
                    name.contains("CCacheConfigKeyInfo")) {
                    println(" NEAR_SYMBOL " + symbol.getAddress() + " " + name +
                        " type=" + symbol.getSymbolType() + " source=" + symbol.getSource());
                    if (++emitted >= 80) break;
                }
            }
        }
    }

    private String describe(Function function) {
        if (function == null) return "<none>";
        return function.getEntryPoint() + ":" + function.getName(true) +
            ":body=" + function.getBody();
    }
}
