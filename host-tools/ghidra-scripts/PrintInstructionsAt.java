// Print a bounded instruction range from the current program.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;

public class PrintInstructionsAt extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("start address and instruction count required");
        }
        Address cursor = toAddr(Long.decode(args[0]));
        int count = Integer.decode(args[1]);
        Listing listing = currentProgram.getListing();
        for (int i = 0; i < count; i++) {
            Instruction insn = listing.getInstructionAt(cursor);
            if (insn == null) {
                println(cursor + " <no instruction>");
                break;
            }
            println(insn.getAddress() + "  " + insn.toString());
            cursor = insn.getNext().getAddress();
        }
    }
}
