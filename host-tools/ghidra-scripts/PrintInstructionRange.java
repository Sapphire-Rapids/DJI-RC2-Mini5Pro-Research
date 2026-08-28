// Disassemble and print an inclusive AArch64 address range in a read-only run.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class PrintInstructionRange extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("start and end-exclusive addresses required");
        }
        long start = Long.decode(args[0]);
        long endExclusive = Long.decode(args[1]);
        for (long at = start; at < endExclusive; at += 4) {
            Address address = toAddr(at);
            disassemble(address);
            Instruction instruction = getInstructionAt(address);
            if (instruction == null) {
                println(String.format("%08x <no instruction>", at));
            } else {
                println(instruction.getAddress() + "  " + instruction.toString());
            }
        }
    }
}
