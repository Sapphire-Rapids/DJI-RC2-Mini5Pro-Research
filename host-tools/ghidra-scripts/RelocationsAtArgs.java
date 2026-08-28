// Offline helper: print relocations at exact addresses supplied as arguments.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.reloc.Relocation;

public class RelocationsAtArgs extends GhidraScript {
    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            Address address = toAddr(Long.decode(arg));
            println("ADDRESS=" + address + " pointer=0x" + Long.toHexString(getLong(address)));
            for (Relocation relocation : currentProgram.getRelocationTable().getRelocations(address)) {
                println("  type=" + relocation.getType() + " status=" + relocation.getStatus()
                    + " symbol=" + relocation.getSymbolName() + " values="
                    + java.util.Arrays.toString(relocation.getValues()));
            }
        }
    }
}
