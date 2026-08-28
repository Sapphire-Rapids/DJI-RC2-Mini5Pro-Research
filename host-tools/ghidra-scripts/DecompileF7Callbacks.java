// Targeted decompilation of the two std::function callback vtables constructed
// immediately around the FC 0x03/0xF7 request in ReadConfig.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileF7Callbacks extends GhidraScript {
    private static final long[] TARGETS = {
        0x01f215d0L, 0x01f21610L, 0x01f21668L, 0x01f216f8L,
        0x01f2176cL, 0x01f217a0L, 0x01f217ecL, 0x01f218c8L, 0x01f218e4L,
        0x01f218f0L, 0x01f21930L, 0x01f21988L, 0x01f21a18L,
        0x01f21a8cL, 0x01f21ac0L, 0x01f21b0cL, 0x01f21b58L, 0x01f21b74L
    };

    public void run() throws Exception {
        DecompInterface d = new DecompInterface();
        d.openProgram(currentProgram);
        for (long value : TARGETS) {
            Address a = toAddr(value);
            Function f = getFunctionAt(a);
            if (f == null) {
                disassemble(a);
                f = createFunction(a, null);
            }
            println(String.format("BEGIN %08x %s", value, f == null ? "<no-function>" : f.getName(true)));
            if (f != null) {
                DecompileResults r = d.decompileFunction(f, 120, monitor);
                if (r != null && r.decompileCompleted() && r.getDecompiledFunction() != null)
                    println(r.getDecompiledFunction().getC());
                else println("FAILED " + (r == null ? "null" : r.getErrorMessage()));
            }
            println(String.format("END %08x", value));
        }
        d.dispose();
    }
}
