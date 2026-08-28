// Read-only disassembly around the two RID-related FCConfig registrations in
// UAV139FCAbs::WillSetup().
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;

public class InspectUAV139RegistrationSlices extends GhidraScript {
    private static final long[][] RANGES = {
        {0x0329f900L, 0x0329fe80L},
        {0x032a6d80L, 0x032a71a0L}
    };

    @Override
    protected void run() throws Exception {
        for (long[] range : RANGES) {
            Address start = toAddr(range[0]), end = toAddr(range[1]);
            println("BEGIN_RANGE " + start + ".." + end);
            for (Address at = start; at.compareTo(end) <= 0; at = at.add(4)) {
                disassemble(at);
                Instruction ins = getInstructionAt(at);
                if (ins == null) continue;
                StringBuilder line = new StringBuilder(at + " " + ins);
                for (Reference ref : getReferencesFrom(at)) {
                    Address target = ref.getToAddress();
                    Symbol symbol = getSymbolAt(target);
                    Function function = getFunctionAt(target);
                    if (function == null) function = getFunctionContaining(target);
                    line.append(" | ref=").append(target).append("[").append(ref.getReferenceType()).append("]");
                    if (symbol != null) line.append(" sym=").append(symbol.getName(true));
                    if (function != null) line.append(" func=").append(function.getName(true));
                }
                println(line.toString());
            }
            println("END_RANGE " + start + ".." + end);
        }
    }
}
