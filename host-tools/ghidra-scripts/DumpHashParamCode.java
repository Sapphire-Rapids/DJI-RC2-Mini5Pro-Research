// Narrow disassembly around candidate FC hash-parameter builders.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class DumpHashParamCode extends GhidraScript {
    private static final long[][] RANGES = {
        {0x01e1e450L, 0x01e1e700L},
        {0x01e1ef80L, 0x01e1f210L},
        {0x01e1f500L, 0x01e1f7b0L},
        {0x01e1fc40L, 0x01e1fee0L},
        {0x02d2a700L, 0x02d2b860L}
    };

    @Override
    protected void run() throws Exception {
        for (long[] range : RANGES) {
            Address start = toAddr(range[0]);
            Address end = toAddr(range[1]);
            println("BEGIN_RANGE " + start + ".." + end);
            disassemble(start);
            Instruction ins = getInstructionAt(start);
            while (ins != null && ins.getAddress().compareTo(end) <= 0) {
                println(ins.getAddress() + "  " + ins.toString());
                ins = ins.getNext();
            }
            println("END_RANGE " + start + ".." + end);
        }
    }
}
