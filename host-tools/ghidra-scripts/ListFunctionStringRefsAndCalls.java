// Print direct ASCII string references and call targets for exact function entries.
// Offline/read-only helper for the global RID control-surface audit.
// @category DJIResearch

import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class ListFunctionStringRefsAndCalls extends GhidraScript {
    private String readAscii(Address start, int maxLength) {
        Memory memory = currentProgram.getMemory();
        if (!memory.contains(start)) return null;
        byte[] bytes = new byte[maxLength];
        int length = 0;
        try {
            for (; length < maxLength; length++) {
                int value = memory.getByte(start.add(length)) & 0xff;
                if (value == 0) break;
                if (value < 0x20 || value > 0x7e) return null;
                bytes[length] = (byte)value;
            }
        } catch (Exception error) {
            return null;
        }
        if (length < 3 || length == maxLength) return null;
        return new String(bytes, 0, length, StandardCharsets.US_ASCII);
    }

    @Override
    protected void run() throws Exception {
        for (String arg : getScriptArgs()) {
            Address requested = toAddr(Long.decode(arg));
            Function function = getFunctionAt(requested);
            if (function == null) function = getFunctionContaining(requested);
            if (function == null) {
                println("NO_FUNCTION address=" + requested);
                continue;
            }

            println("BEGIN_FUNCTION entry=" + function.getEntryPoint() +
                " name=" + function.getName(true));
            Set<String> emittedStrings = new LinkedHashSet<>();
            Set<String> emittedCalls = new LinkedHashSet<>();
            Instruction instruction = getInstructionAt(function.getEntryPoint());
            while (instruction != null && function.getBody().contains(instruction.getAddress())) {
                for (Reference reference : instruction.getReferencesFrom()) {
                    Address target = reference.getToAddress();
                    if (reference.getReferenceType().isCall()) {
                        Function callee = getFunctionAt(target);
                        String line = "CALL from=" + instruction.getAddress() +
                            " target=" + target + " name=" +
                            (callee == null ? "<none>" : callee.getName(true));
                        if (emittedCalls.add(line)) println(line);
                    }
                    if (target != null && target.isMemoryAddress()) {
                        String value = readAscii(target, 512);
                        if (value != null) {
                            String line = "STRING from=" + instruction.getAddress() +
                                " target=" + target + " value=" + value;
                            if (emittedStrings.add(line)) println(line);
                        }
                    }
                }
                instruction = instruction.getNext();
            }
            println("END_FUNCTION entry=" + function.getEntryPoint());
        }
    }
}
