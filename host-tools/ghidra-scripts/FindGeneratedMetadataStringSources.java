// Read-only scan of the generated getFCConfigsKeyMap body. Reconstruct ADRP/ADD
// addresses and report printable source strings relevant to RID/CCC.
// @category DJIResearch

import java.util.HashMap;
import java.util.Map;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Instruction;

public class FindGeneratedMetadataStringSources extends GhidraScript {
    private static final long START = 0x01f24af0L;
    private static final long END = 0x01f5136fL;
    private static final Pattern ADRP = Pattern.compile("adrp (x[0-9]+),0x([0-9a-f]+)");
    private static final Pattern ADD = Pattern.compile("add (x[0-9]+),\\1,#0x([0-9a-f]+)");
    private static final Pattern LOAD = Pattern.compile("(?:ldur|ldr|ldp) (?:q[0-9]+|x[0-9]+|w[0-9]+)(?:,(?:q[0-9]+|x[0-9]+|w[0-9]+))?,\\[(x[0-9]+)(?:, #(-?0x[0-9a-f]+))?\\].*");

    @Override
    protected void run() throws Exception {
        for (long at = START; at <= END; at += 4) disassemble(toAddr(at));
        Map<String, Long> pages = new HashMap<>();
        Map<String, Long> addresses = new HashMap<>();
        TreeSet<String> emitted = new TreeSet<>();
        Instruction instruction = getInstructionAt(toAddr(START));
        if (instruction == null) instruction = getInstructionAfter(toAddr(START));
        while (instruction != null && instruction.getAddress().getOffset() <= END) {
            String text = instruction.toString();
            Matcher adrp = ADRP.matcher(text);
            if (adrp.matches()) {
                pages.put(adrp.group(1), Long.parseUnsignedLong(adrp.group(2), 16));
                addresses.put(adrp.group(1), Long.parseUnsignedLong(adrp.group(2), 16));
            }
            Matcher add = ADD.matcher(text);
            if (add.matches() && pages.containsKey(add.group(1))) {
                long address = pages.get(add.group(1)) + Long.parseUnsignedLong(add.group(2), 16);
                addresses.put(add.group(1), address);
                inspectWindow(emitted, instruction, address, "ADD");
            }
            Matcher load = LOAD.matcher(text);
            if (load.matches() && addresses.containsKey(load.group(1))) {
                long offset = 0;
                if (load.group(2) != null) {
                    String value = load.group(2);
                    boolean negative = value.startsWith("-");
                    value = value.replace("-", "").replace("0x", "");
                    offset = Long.parseUnsignedLong(value, 16) * (negative ? -1 : 1);
                }
                inspectWindow(emitted, instruction, addresses.get(load.group(1)) + offset, "LOAD");
            }
            instruction = instruction.getNext();
        }
    }

    private void inspectWindow(TreeSet<String> emitted, Instruction instruction, long address, String kind) {
        String window = readBytesAsPrintable(address - 32, 256).toLowerCase();
        if (window.contains("ccc_") || window.contains("eu_ce") ||
            window.contains("c0_rid") || window.contains("broadcast_signal") ||
            window.contains("remote")) {
            String key = instruction.getAddress() + ":" + address + ":" + kind;
            if (emitted.add(key)) {
                println(String.format("MATCH kind=%s ins=%s addr=%08x window=%s", kind,
                    instruction.getAddress(), address, window));
            }
        }
    }

    private String readBytesAsPrintable(long address, int maximum) {
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

    private String readAscii(long address, int maximum) {
        StringBuilder out = new StringBuilder();
        try {
            for (int i = 0; i < maximum; i++) {
                int value = getByte(toAddr(address + i)) & 0xff;
                if (value == 0) break;
                if (value < 0x20 || value > 0x7e) break;
                out.append((char)value);
            }
        }
        catch (Exception ignored) { }
        return out.toString();
    }
}
