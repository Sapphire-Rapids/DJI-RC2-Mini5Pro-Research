// Targeted, read-only inspection of DJI FC hash-parameter request constructors.
// @category DJIResearch

import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class AnalyzeHashParamTransport extends GhidraScript {
    private static final String[] NEEDLES = {
        "get_cfg_item_info_by_hash",
        "read_hash_param",
        "write_hash_param",
        "reset_cfg_item_by_hash"
    };

    private boolean wanted(String name) {
        for (String needle : NEEDLES) {
            if (name.contains(needle)) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void run() throws Exception {
        List<Symbol> targets = new ArrayList<>();
        SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
        while (it.hasNext()) {
            Symbol symbol = it.next();
            String fullName = symbol.getName(true);
            if (wanted(fullName)) {
                targets.add(symbol);
            }
        }

        println("TARGET_COUNT=" + targets.size());
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        for (Symbol symbol : targets) {
            Address address = symbol.getAddress();
            println("BEGIN_SYMBOL address=" + address + " name=" + symbol.getName(true) +
                " type=" + symbol.getSymbolType() + " source=" + symbol.getSource());
            int refCount = 0;
            for (Reference ref : getReferencesTo(address)) {
                println("REF from=" + ref.getFromAddress() + " type=" + ref.getReferenceType());
                if (++refCount >= 40) {
                    println("REF_TRUNCATED");
                    break;
                }
            }

            disassemble(address);
            Function function = getFunctionAt(address);
            if (function == null) {
                function = createFunction(address, null);
            }
            if (function != null) {
                println("FUNCTION entry=" + function.getEntryPoint() + " name=" + function.getName(true) +
                    " body=" + function.getBody());
                DecompileResults result = decompiler.decompileFunction(function, 90, monitor);
                if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                    println(result.getDecompiledFunction().getC());
                }
                else {
                    println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
                }
            }
            else {
                println("NO_FUNCTION");
            }
            println("END_SYMBOL address=" + address);
        }
        decompiler.dispose();
    }
}
