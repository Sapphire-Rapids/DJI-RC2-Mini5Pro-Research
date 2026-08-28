// Read-only effective-address scan of UAV139/UAV77 FC abstraction bodies for
// RID/EID/CCC-related literals. This reconstructs common AArch64 ADRP+ADD and
// ADRP+load address formation and does not modify the program.
// @category DJIResearch

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Instruction;

public class ScanUAV139RidSources extends GhidraScript {
    private static final long[][] RANGES = {
        {0x0326414cL, 0x0329a84bL},
        {0x0329a84cL, 0x032af24bL},
        {0x032af24cL, 0x032b161fL},
        {0x02d81d00L, 0x02d92fe7L},
        {0x02d92fe8L, 0x02d93393L}
    };
    private static final Pattern ADRP = Pattern.compile("adrp (x[0-9]+),0x([0-9a-f]+)");
    private static final Pattern ADD = Pattern.compile("add (x[0-9]+),\\1,#0x([0-9a-f]+)");
    private static final Pattern LOAD = Pattern.compile("(?:ldur|ldr|ldp) (?:q[0-9]+|x[0-9]+|w[0-9]+)(?:,(?:q[0-9]+|x[0-9]+|w[0-9]+))?,\\[(x[0-9]+)(?:, #(-?0x[0-9a-f]+))?\\].*");

    @Override
    protected void run() throws Exception {
        for (long[] range : RANGES) {
            long start = range[0], end = range[1];
            String label = labelFor(start);
            println("BEGIN_RANGE " + label + " " + toAddr(start) + ".." + toAddr(end));
            for (long at = start; at <= end; at += 4) disassemble(toAddr(at));
            Map<String, Long> pages = new HashMap<>();
            Map<String, Long> addresses = new HashMap<>();
            Set<String> emitted = new HashSet<>();
            Instruction ins = getInstructionAt(toAddr(start));
            if (ins == null) ins = getInstructionAfter(toAddr(start));
            while (ins != null && ins.getAddress().getOffset() <= end) {
                String text = ins.toString();
                Matcher adrp = ADRP.matcher(text);
                if (adrp.matches()) {
                    long page = Long.parseUnsignedLong(adrp.group(2), 16);
                    pages.put(adrp.group(1), page);
                    addresses.put(adrp.group(1), page);
                }
                Matcher add = ADD.matcher(text);
                if (add.matches() && pages.containsKey(add.group(1))) {
                    long addr = pages.get(add.group(1)) + Long.parseUnsignedLong(add.group(2), 16);
                    addresses.put(add.group(1), addr);
                    inspect(emitted, label, ins, addr, "ADD");
                }
                Matcher load = LOAD.matcher(text);
                if (load.matches() && addresses.containsKey(load.group(1))) {
                    long off = parseOffset(load.group(2));
                    inspect(emitted, label, ins, addresses.get(load.group(1)) + off, "LOAD");
                }
                ins = ins.getNext();
            }
            println("END_RANGE " + label);
        }
    }

    private String labelFor(long start) {
        if (start == 0x0326414cL) return "UAV139.CreateCharacteristics";
        if (start == 0x0329a84cL) return "UAV139.WillSetup";
        if (start == 0x032af24cL) return "UAV139.OnFirmwareVersionChange";
        if (start == 0x02d81d00L) return "UAV77.CreateCharacteristics";
        return "UAV77.WillSetup";
    }

    private long parseOffset(String raw) {
        if (raw == null) return 0;
        boolean negative = raw.startsWith("-");
        String value = raw.replace("-", "").replace("0x", "");
        long parsed = Long.parseUnsignedLong(value, 16);
        return negative ? -parsed : parsed;
    }

    private void inspect(Set<String> emitted, String label, Instruction ins, long address, String kind) {
        String ascii = readPrintableWindow(address - 48, 384);
        String lower = ascii.toLowerCase();
        if (lower.contains("rid") || lower.contains("remote") || lower.contains("eid") ||
            lower.contains("ccc_") || lower.contains("eu_ce") ||
            lower.contains("broadcast_signal") || lower.contains("operator")) {
            String key = ins.getAddress() + ":" + address + ":" + kind;
            if (emitted.add(key)) {
                println(String.format("MATCH range=%s kind=%s ins=%s addr=%08x window=%s",
                    label, kind, ins.getAddress(), address, ascii));
            }
        }
    }

    private String readPrintableWindow(long address, int maximum) {
        StringBuilder out = new StringBuilder();
        try {
            for (int i = 0; i < maximum; i++) {
                int value = getByte(toAddr(address + i)) & 0xff;
                out.append((value >= 0x20 && value <= 0x7e) ? (char)value : '.');
            }
        }
        catch (Exception ignored) { }
        return out.toString();
    }
}
