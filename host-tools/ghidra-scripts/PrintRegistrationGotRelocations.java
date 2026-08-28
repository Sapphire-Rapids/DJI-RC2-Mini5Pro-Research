// Resolve PLT/GOT imports used by RID named-parameter registration.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.reloc.Relocation;

public class PrintRegistrationGotRelocations extends GhidraScript {
    private static final long[] ADDRESSES = {
        0x0524f140L, 0x0524f300L,
        0x0523b6b0L, 0x0523b6d0L, 0x0523b6e8L
    };

    @Override
    protected void run() throws Exception {
        for (long value : ADDRESSES) {
            Address address = toAddr(value);
            java.util.List<Relocation> relocs =
                currentProgram.getRelocationTable().getRelocations(address);
            println("GOT=" + address + " value=0x" + Long.toHexString(getLong(address)));
            for (Relocation relocation : relocs) {
                println("  type=" + relocation.getType() + " status=" + relocation.getStatus() +
                    " symbol=" + relocation.getSymbolName() + " values=" +
                    java.util.Arrays.toString(relocation.getValues()));
            }
        }
    }
}
