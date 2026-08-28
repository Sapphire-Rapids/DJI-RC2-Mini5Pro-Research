// Find relocated function pointers and code references for FC config converters.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class FindConfigHandlerPointers extends GhidraScript {
    private static final long[] TARGETS = {
        0x02c42934L, 0x02c42ad4L, 0x02c4342cL, 0x02c435e0L
    };

    @Override
    protected void run() throws Exception {
        Memory memory = currentProgram.getMemory();
        for (long targetValue : TARGETS) {
            Address target = toAddr(targetValue);
            println("TARGET=" + target);
            for (Reference ref : getReferencesTo(target)) {
                println(" DIRECT_REF from=" + ref.getFromAddress() + " type=" + ref.getReferenceType());
            }
            byte[] bytes = new byte[8];
            long v = targetValue;
            for (int i = 0; i < 8; i++) bytes[i] = (byte)(v >>> (i * 8));
            int count = 0;
            Address cursor = memory.getMinAddress();
            while (cursor != null && cursor.compareTo(memory.getMaxAddress()) <= 0) {
                Address hit = memory.findBytes(cursor, memory.getMaxAddress(), bytes, null, true, monitor);
                if (hit == null) break;
                println(" POINTER=" + hit);
                for (Reference ref : getReferencesTo(hit)) {
                    println("  PTR_REF from=" + ref.getFromAddress() + " type=" + ref.getReferenceType());
                }
                if (++count >= 100) break;
                cursor = hit.add(1);
            }
        }
    }
}
