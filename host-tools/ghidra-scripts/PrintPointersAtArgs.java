// Print pointer-sized values at exact addresses supplied on the command line.
// Offline, work-only helper for auditing relocated vtables/data pointers.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class PrintPointersAtArgs extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException("usage: <start-address> <count> [start-address count ...]");
        }
        if ((args.length & 1) != 0) {
            throw new IllegalArgumentException("arguments must be address/count pairs");
        }
        for (int pair = 0; pair < args.length; pair += 2) {
            long start = Long.decode(args[pair]);
            int count = Integer.decode(args[pair + 1]);
            for (int index = 0; index < count; index++) {
                Address slot = toAddr(start + index * 8L);
                long value = getLong(slot);
                println("POINTER slot=" + slot + " value=0x" + Long.toHexString(value));
            }
        }
    }
}
