// Offline/read-only search for ASCII strings and Ghidra references to them.
// Usage: -postScript FindAsciiStringRefs.java min_value max_value
// @category DJIResearch

import java.nio.charset.StandardCharsets;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class FindAsciiStringRefs extends GhidraScript {
    @Override
    protected void run() throws Exception {
        Memory memory = currentProgram.getMemory();
        AddressSetView loaded = memory.getLoadedAndInitializedAddressSet();
        for (String needle : getScriptArgs()) {
            byte[] bytes = needle.getBytes(StandardCharsets.US_ASCII);
            Address cursor = loaded.getMinAddress();
            println("BEGIN needle=" + needle);
            while (cursor != null) {
                Address hit = memory.findBytes(cursor, loaded.getMaxAddress(), bytes, null, true, monitor);
                if (hit == null) break;
                println(" HIT address=" + hit);
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(hit);
                while (refs.hasNext()) {
                    Reference ref = refs.next();
                    Function function = currentProgram.getFunctionManager()
                        .getFunctionContaining(ref.getFromAddress());
                    println("  REF from=" + ref.getFromAddress() + " type=" + ref.getReferenceType() +
                        " function=" + (function == null ? "<none>" :
                            function.getName(true) + "@" + function.getEntryPoint()));
                }
                cursor = hit.next();
                if (cursor == null || !loaded.contains(cursor)) break;
            }
            println("END needle=" + needle);
        }
    }
}
