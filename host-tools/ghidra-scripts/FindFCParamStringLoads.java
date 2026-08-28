// Read-only scan for ADRP/ADD materialization of the two RID-relevant FC parameter strings.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;

public class FindFCParamStringLoads extends GhidraScript {
    private static final long START = 0x01f24af0L;
    private static final long END = 0x01f5136fL;

    @Override
    protected void run() throws Exception {
        for (long at = START; at <= END; at += 4) disassemble(toAddr(at));
        Instruction instruction = getInstructionAt(toAddr(START));
        if (instruction == null) instruction = getInstructionAfter(toAddr(START));
        while (instruction != null && instruction.getAddress().getOffset() <= END) {
            String rendered = instruction.toString();
            if (rendered.contains("0x12ee000") || rendered.contains("0x13ce000")) {
                Function owner = getFunctionContaining(instruction.getAddress());
                println("MATCH " + instruction.getAddress() + " " + rendered + " owner=" +
                    (owner == null ? "<none>" : owner.getEntryPoint() + ":" + owner.getName(true)));
                Instruction cursor = instruction;
                for (int i = 0; i < 12 && cursor != null; i++) {
                    println(" INS " + cursor.getAddress() + " " + cursor);
                    cursor = cursor.getNext();
                }
            }
            instruction = instruction.getNext();
        }
    }
}
