// Print a bounded little-endian int array from current program memory.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;

public class PrintIntArrayAt extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("start address and element count required");
        }
        Address cursor = toAddr(Long.decode(args[0]));
        int count = Integer.decode(args[1]);
        Memory memory = currentProgram.getMemory();
        for (int i = 0; i < count; i++) {
            int value = memory.getInt(cursor);
            println(cursor + " int=" + value + " hex=0x" + Integer.toUnsignedString(value, 16));
            cursor = cursor.add(4);
        }
    }
}
