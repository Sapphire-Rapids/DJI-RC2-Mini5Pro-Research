// Read-only xref inventory for cache metadata builder/constructor PLT stubs.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class FindFCMetadataBuilderCalls extends GhidraScript {
    private static final long[] TARGETS = { 0x051625d0L, 0x05162690L, 0x051626a0L };

    @Override
    protected void run() throws Exception {
        for (long targetValue : TARGETS) {
            Address target = toAddr(targetValue);
            println("TARGET " + target);
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(target);
            int count = 0;
            while (refs.hasNext()) {
                Reference ref = refs.next();
                Address from = ref.getFromAddress();
                Function owner = getFunctionContaining(from);
                Instruction instruction = getInstructionAt(from);
                println(" REF " + from + " " + ref.getReferenceType() + " ins=" + instruction +
                    " owner=" + (owner == null ? "<none>" : owner.getEntryPoint() + ":" + owner.getName(true)));
                count++;
            }
            println("COUNT " + count);
        }
    }
}
