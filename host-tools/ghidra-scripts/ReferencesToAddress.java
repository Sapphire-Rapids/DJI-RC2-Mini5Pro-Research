// Offline helper: list all code/data references to requested addresses.
// Usage: -postScript ReferencesToAddress.java 0x3c04938
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class ReferencesToAddress extends GhidraScript {
    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            long offset = Long.decode(arg);
            Address target = currentProgram.getAddressFactory()
                .getDefaultAddressSpace().getAddress(offset);
            println("BEGIN_REFERENCES target=" + target);
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(target);
            while (refs.hasNext()) {
                Reference ref = refs.next();
                Function function = currentProgram.getFunctionManager()
                    .getFunctionContaining(ref.getFromAddress());
                println("from=" + ref.getFromAddress() + " type=" + ref.getReferenceType()
                    + " function=" + (function == null ? "<none>"
                        : function.getName(true) + "@" + function.getEntryPoint()));
            }
            println("END_REFERENCES target=" + target);
        }
    }
}
