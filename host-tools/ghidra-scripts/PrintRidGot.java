// Print a narrow set of relocation/GOT entries without modifying the program.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.reloc.Relocation;
import ghidra.program.model.symbol.Symbol;

public class PrintRidGot extends GhidraScript {
    private static final long[] ADDRESSES = {
        0x522cb28L, 0x522cb30L, 0x522cb38L,
        0x522cb78L, 0x522cb80L, 0x522cb88L,
        0x522e348L, 0x522e558L, 0x522e738L
    };

    @Override
    protected void run() throws Exception {
        for (long value : ADDRESSES) {
            Address address = toAddr(value);
            long memoryValue = getLong(address);
            Symbol symbol = getSymbolAt(address);
            java.util.List<Relocation> relocations =
                currentProgram.getRelocationTable().getRelocations(address);
            println("GOT address=" + address + " value=0x" + Long.toHexString(memoryValue) +
                " symbol=" + (symbol == null ? "<none>" : symbol.getName(true)) +
                " relocations=" + relocations);
        }
    }
}
