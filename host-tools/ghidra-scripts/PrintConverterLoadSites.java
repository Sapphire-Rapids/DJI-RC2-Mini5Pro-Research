// Print exact instructions/references that load config converter function pointers.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;

public class PrintConverterLoadSites extends GhidraScript {
    private static final long[][] RANGES = {
        {0x030bb828L, 0x030bba60L},
        {0x031c8cb0L, 0x031c8f20L}
    };
    @Override
    protected void run() throws Exception {
        for (long[] range : RANGES) {
            Address start = toAddr(range[0]);
            Address end = toAddr(range[1]);
            disassemble(start);
            println("RANGE " + start + " " + end);
            byte[] raw = new byte[32];
            currentProgram.getMemory().getBytes(start, raw);
            StringBuilder hex = new StringBuilder();
            for (byte value : raw) hex.append(String.format("%02x", value & 0xff));
            println("BYTES " + hex.toString());
            Instruction ins = getInstructionAt(start);
            if (ins == null) ins = getInstructionAfter(start);
            while (ins != null && ins.getAddress().compareTo(end) <= 0) {
                println(ins.getAddress() + " " + ins.toString());
                for (Reference ref : ins.getReferencesFrom()) {
                    println(" REF to=" + ref.getToAddress() + " type=" + ref.getReferenceType());
                }
                ins = ins.getNext();
            }
        }
    }
}
