// Read-only instruction windows around selected generated FC metadata entries.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class PrintFCMetadataEntries extends GhidraScript {
    private static final long[][] RANGES = {
        { 0x01f24b80L, 0x01f24d40L },
        { 0x01f4b500L, 0x01f4b700L }
    };

    @Override
    protected void run() throws Exception {
        for (long[] range : RANGES) {
            for (long at = range[0]; at <= range[1]; at += 4) disassemble(toAddr(at));
            println(String.format("RANGE %08x-%08x", range[0], range[1]));
            Instruction instruction = getInstructionAt(toAddr(range[0]));
            if (instruction == null) instruction = getInstructionAfter(toAddr(range[0]));
            while (instruction != null && instruction.getAddress().getOffset() <= range[1]) {
                println(instruction.getAddress() + " " + instruction);
                instruction = instruction.getNext();
            }
        }
    }
}
