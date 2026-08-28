// Inspect pointer-sized entries and their resolved functions in the current FlySafe image.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;

public class InspectOfficialFlySafeDataPointers extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0) {
            throw new IllegalArgumentException("at least one hex address is required");
        }
        Memory memory = currentProgram.getMemory();
        for (String arg : args) {
            Address slot = toAddr(Long.decode(arg));
            long raw = memory.getLong(slot);
            Address target = toAddr(raw);
            Function at = currentProgram.getFunctionManager().getFunctionAt(target);
            Function containing = currentProgram.getFunctionManager().getFunctionContaining(target);
            println("POINTER slot=" + slot
                + " raw=0x" + Long.toUnsignedString(raw, 16)
                + " target=" + target
                + " at=" + (at == null ? "-" : at.getName(true))
                + " containing=" + (containing == null ? "-" : containing.getName(true)));
        }
    }
}
