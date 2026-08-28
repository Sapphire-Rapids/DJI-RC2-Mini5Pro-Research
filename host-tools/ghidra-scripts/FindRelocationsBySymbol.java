// Offline helper: list relocations whose symbol name contains any requested needle.
// Usage: -postScript FindRelocationsBySymbol.java UavProtocolEncoder
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.reloc.Relocation;
import java.util.Iterator;

public class FindRelocationsBySymbol extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] needles = getScriptArgs();
        Iterator<Relocation> it = currentProgram.getRelocationTable().getRelocations();
        while (it.hasNext()) {
            Relocation relocation = it.next();
            String symbol = relocation.getSymbolName();
            if (symbol == null) {
                continue;
            }
            for (String needle : needles) {
                if (symbol.contains(needle)) {
                    println("at=" + relocation.getAddress() + " type=" + relocation.getType()
                        + " status=" + relocation.getStatus() + " symbol=" + symbol
                        + " values=" + java.util.Arrays.toString(relocation.getValues()));
                    break;
                }
            }
        }
    }
}
