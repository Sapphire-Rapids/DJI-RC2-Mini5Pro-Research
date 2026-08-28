// Read-only inspection of helper/thunk targets used by generated FC config registration.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;

public class InspectFCConfigRegistrationHelpers extends GhidraScript {
    private static final long[] TARGETS = {
        0x05182c20L, 0x05182fa0L, 0x02e0129cL, 0x02e013dcL, 0x02e0151cL,
        0x051625d0L, 0x05162690L, 0x051626a0L,
        0x051733a0L, 0x051701a0L, 0x05171070L, 0x051724c0L, 0x05170410L
    };
    private static final long[] GOTS = {
        0x0534f140L, 0x0534f300L, 0x0533ee18L, 0x0533ee78L, 0x0533ee80L,
        0x05346d80L, 0x05347500L, 0x05345c00L, 0x05346368L, 0x05346d90L,
        0x05345d38L
    };

    @Override
    protected void run() throws Exception {
        for (long gotValue : GOTS) {
            long pointer = getLong(toAddr(gotValue));
            Symbol pointerSymbol = getSymbolAt(toAddr(pointer));
            println(String.format("GOT %08x -> %08x %s", gotValue, pointer,
                pointerSymbol == null ? "<none>" : pointerSymbol.getName(true)));
        }
        for (long value : TARGETS) {
            Address address = toAddr(value);
            Function function = getFunctionAt(address);
            Symbol symbol = getSymbolAt(address);
            println("TARGET " + address + " symbol=" +
                (symbol == null ? "<none>" : symbol.getName(true)) + " function=" +
                (function == null ? "<none>" : function.getName(true)) + " thunk=" +
                (function == null || function.getThunkedFunction(true) == null ? "<none>" :
                    function.getThunkedFunction(true).getEntryPoint() + ":" +
                    function.getThunkedFunction(true).getName(true)));
            Address cursor = address;
            for (int i = 0; i < 8; i++) {
                Instruction instruction = getInstructionAt(cursor);
                if (instruction == null) {
                    disassemble(cursor);
                    instruction = getInstructionAt(cursor);
                }
                if (instruction == null) break;
                println(" INS " + cursor + " " + instruction);
                for (Reference ref : instruction.getReferencesFrom()) {
                    println("  REF " + ref.getReferenceType() + " -> " + ref.getToAddress());
                    try {
                        if (currentProgram.getMemory().contains(ref.getToAddress())) {
                            long pointer = getLong(ref.getToAddress());
                            Symbol pointerSymbol = getSymbolAt(toAddr(pointer));
                            println(String.format("   DEREF %016x %s", pointer,
                                pointerSymbol == null ? "<none>" : pointerSymbol.getName(true)));
                        }
                    }
                    catch (MemoryAccessException ignored) { }
                }
                cursor = instruction.getMaxAddress().next();
            }
        }
    }
}
