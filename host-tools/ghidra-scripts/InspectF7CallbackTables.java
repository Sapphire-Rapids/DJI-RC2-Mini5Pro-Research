import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;

public class InspectF7CallbackTables extends GhidraScript {
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        long[] bases = {0x051c4900L, 0x051c49f0L};
        for (long base : bases) {
            println(String.format("TABLE_RANGE %08x", base));
            for (long p = base; p < base + 0xf0; p += 8) {
                Address a = toAddr(p);
                long v;
                try { v = mem.getLong(a); }
                catch (Exception e) { continue; }
                Address va = toAddr(v);
                Function f = getFunctionAt(va);
                if (f == null) f = getFunctionContaining(va);
                println(String.format("%08x -> %016x%s", p, v,
                    f == null ? "" : " FUNC=" + f.getEntryPoint() + " " + f.getName(true)));
            }
        }
    }
}
