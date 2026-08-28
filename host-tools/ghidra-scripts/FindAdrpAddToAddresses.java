// Offline/read-only scan for AArch64 ADRP+ADD calculations reaching target addresses.
// Usage: -postScript FindAdrpAddToAddresses.java 0x012efee3
// @category DJIResearch

import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;

public class FindAdrpAddToAddresses extends GhidraScript {
    private static final Pattern ADRP = Pattern.compile("adrp (x[0-9]+),0x([0-9a-f]+)");
    private static final Pattern ADD = Pattern.compile("add (x[0-9]+),\\1,#0x([0-9a-f]+)");

    @Override
    protected void run() throws Exception {
        long[] targets = new long[getScriptArgs().length];
        for (int i = 0; i < targets.length; i++) targets[i] = Long.decode(getScriptArgs()[i]);
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function function = functions.next();
            Map<String, Long> pages = new HashMap<>();
            Instruction ins = currentProgram.getListing().getInstructionAt(function.getBody().getMinAddress());
            if (ins == null) ins = currentProgram.getListing().getInstructionAfter(function.getBody().getMinAddress());
            while (ins != null && function.getBody().contains(ins.getAddress())) {
                String text = ins.toString();
                Matcher adrp = ADRP.matcher(text);
                if (adrp.matches()) {
                    pages.put(adrp.group(1), Long.parseUnsignedLong(adrp.group(2), 16));
                }
                Matcher add = ADD.matcher(text);
                if (add.matches() && pages.containsKey(add.group(1))) {
                    long value = pages.get(add.group(1)) + Long.parseUnsignedLong(add.group(2), 16);
                    for (long target : targets) {
                        long delta = value - target;
                        if (delta >= -64 && delta <= 64) {
                            println(String.format("MATCH target=%08x value=%08x delta=%d ins=%s text=%s function=%s@%s",
                                target, value, delta, ins.getAddress(), text,
                                function.getName(true), function.getEntryPoint()));
                        }
                    }
                }
                ins = ins.getNext();
            }
        }
    }
}
