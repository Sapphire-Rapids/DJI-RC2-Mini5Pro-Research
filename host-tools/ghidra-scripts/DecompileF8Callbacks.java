// Read-only recovery of FlightControllerConfigManager::ReadConfig F8 callbacks.
// The two std::function objects use vptrs 0x051c4830 and 0x051c48b0.
// @category DJIResearch

import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileF8Callbacks extends GhidraScript {
    private static final long[] VTABLES = { 0x051c4830L, 0x051c48b0L };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        Set<Long> targets = new LinkedHashSet<>();
        for (long table : VTABLES) {
            println(String.format("VTABLE %08x", table));
            for (long slot = 0; slot <= 0x48; slot += 8) {
                long target = getLong(toAddr(table + slot));
                println(String.format(" SLOT +%02x -> %08x", slot, target));
                if (target >= 0x01f20000L && target < 0x01f24000L) targets.add(target);
            }
        }
        Long[] ordered = targets.toArray(new Long[0]);
        for (int i = 0; i < ordered.length; i++) {
            long target = ordered[i];
            Address address = toAddr(target);
            Function function = getFunctionAt(address);
            if (function == null) {
                disassemble(address);
                function = createFunction(address, null);
            }
            if (function != null && i + 1 < ordered.length) {
                long next = ordered[i + 1];
                if (next > target && next - target <= 0x800) {
                    for (long at = target; at < next; at += 4) disassemble(toAddr(at));
                    function.setBody(new AddressSet(address, toAddr(next - 1)));
                }
            }
            println(String.format("BEGIN %08x %s", target,
                function == null ? "<none>" : function.getName(true)));
            if (function != null) {
                DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
                if (result != null && result.decompileCompleted() &&
                    result.getDecompiledFunction() != null) {
                    println(result.getDecompiledFunction().getC());
                }
                else println("FAILED " + (result == null ? "null" : result.getErrorMessage()));
            }
            println(String.format("END %08x", target));
        }
        decompiler.dispose();
    }
}
