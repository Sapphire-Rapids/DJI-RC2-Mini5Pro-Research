// @category FindUAS
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;

public class DumpEidVtablesAndFunctions extends GhidraScript {
    private String describe(long value) {
        Address a = toAddr(value);
        Function f = getFunctionContaining(a);
        Symbol s = getSymbolAt(a);
        String out = a.toString();
        if (s != null) out += " sym=" + s.getName(true);
        if (f != null) out += " func=" + f.getName(true) + " entry=" + f.getEntryPoint();
        return out;
    }

    private void dumpTable(long base, int before, int after) throws Exception {
        println(String.format("BEGIN_TABLE %08x", base));
        for (int off = -before; off <= after; off += 8) {
            Address at = toAddr(base + off);
            long value = getLong(at);
            println(String.format("%s off=%+d value=%016x -> %s", at, off, value, describe(value)));
        }
        println(String.format("END_TABLE %08x", base));
    }

    private void decompileAddress(long value, DecompInterface decomp) {
        Address a = toAddr(value);
        Function f = getFunctionContaining(a);
        if (f == null) {
            println("NO_FUNCTION " + a);
            return;
        }
        println("BEGIN_DECOMPILE " + f.getEntryPoint() + " " + f.getName(true));
        DecompileResults results = decomp.decompileFunction(f, 120, monitor);
        if (results.decompileCompleted()) {
            println(results.getDecompiledFunction().getC());
        } else {
            println("DECOMPILE_FAILED " + results.getErrorMessage());
        }
        println("END_DECOMPILE " + f.getEntryPoint());
    }

    @Override
    public void run() throws Exception {
        long[] tables = {
            0x5284768L, 0x52847e8L,
            0x5307390L, 0x5307410L,
            0x5329e48L, 0x532e1e8L, 0x532e1f0L
        };
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        for (long table : tables) dumpTable(table, 32, 80);

        // Decompile every code pointer present in the four concrete EID std::function vtables.
        java.util.HashSet<Long> seen = new java.util.HashSet<>();
        for (int ti = 0; ti < 4; ti++) {
            long table = tables[ti];
            for (int off = -16; off <= 80; off += 8) {
                long value = getLong(toAddr(table + off));
                Function f = getFunctionContaining(toAddr(value));
                if (f != null && seen.add(f.getEntryPoint().getOffset())) {
                    decompileAddress(f.getEntryPoint().getOffset(), decomp);
                }
            }
        }
        decomp.dispose();
    }
}
