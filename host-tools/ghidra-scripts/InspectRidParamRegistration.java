// Narrow read-only disassembly of the two RID-related FC config registrations.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;

public class InspectRidParamRegistration extends GhidraScript {
    private static final long[][] RANGES = {
        {0x02fbb700L, 0x02fbba80L},
        {0x030c8b80L, 0x030c8f80L}
    };

    @Override
    protected void run() throws Exception {
        for (long[] range : RANGES) {
            Address start = toAddr(range[0]);
            Address end = toAddr(range[1]);
            println("BEGIN_RANGE " + start + ".." + end);
            disassemble(start);
            for (Address at = start; at.compareTo(end) <= 0; at = at.add(4)) {
                Instruction ins = getInstructionAt(at);
                if (ins == null) {
                    disassemble(at);
                    ins = getInstructionAt(at);
                }
                if (ins == null) {
                    continue;
                }
                StringBuilder line = new StringBuilder(at + "  " + ins.toString());
                for (Reference ref : getReferencesFrom(at)) {
                    Address target = ref.getToAddress();
                    Symbol symbol = getSymbolAt(target);
                    Function function = getFunctionAt(target);
                    if (function == null) {
                        function = getFunctionContaining(target);
                    }
                    line.append(" | ref=").append(target)
                        .append("[").append(ref.getReferenceType()).append("]");
                    if (symbol != null) {
                        line.append(" sym=").append(symbol.getName(true));
                    }
                    if (function != null) {
                        line.append(" func=").append(function.getName(true));
                    }
                }
                println(line.toString());
            }
            println("END_RANGE " + start + ".." + end);
        }
    }
}
