// Offline helper: find instructions whose rendered text contains all requested needles.
// Usage: -postScript FindInstructionText.java strb '#0x1a0'
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class FindInstructionText extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] needles = getScriptArgs();
        InstructionIterator it = currentProgram.getListing().getInstructions(true);
        while (it.hasNext()) {
            Instruction instruction = it.next();
            String rendered = instruction.toString();
            boolean match = true;
            for (String needle : needles) {
                if (!rendered.contains(needle)) {
                    match = false;
                    break;
                }
            }
            if (!match) {
                continue;
            }
            Function function = currentProgram.getFunctionManager()
                .getFunctionContaining(instruction.getAddress());
            println("at=" + instruction.getAddress() + " text=" + rendered + " function="
                + (function == null ? "<none>" : function.getName(true) + "@" + function.getEntryPoint()));
        }
    }
}
