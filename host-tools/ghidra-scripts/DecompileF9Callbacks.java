// Read-only recovery of FlightControllerConfigManager::WriteConfig F9 callbacks.
// The two std::function objects use vptrs 0x051c4a30 and 0x051c4ab0.
// @category DJIResearch

import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileF9Callbacks extends GhidraScript {
    private static final long[] VTABLES = { 0x051c4a30L, 0x051c4ab0L };

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
        for (long target : targets) {
            Address address = toAddr(target);
            Function function = getFunctionAt(address);
            if (function == null) {
                disassemble(address);
                function = createFunction(address, null);
            }
            // Ghidra imported these local callback addresses as one-byte placeholder
            // functions. Extend only the two call-operator bodies using the next
            // vtable target as a hard upper bound.
            if (function != null && target == 0x01f21d9cL) {
                for (long at = target; at <= 0x01f21e0bL; at += 4) disassemble(toAddr(at));
                function.setBody(new AddressSet(address, toAddr(0x01f21e0bL)));
            }
            else if (function != null && target == 0x01f22050L) {
                for (long at = target; at <= 0x01f22087L; at += 4) disassemble(toAddr(at));
                function.setBody(new AddressSet(address, toAddr(0x01f22087L)));
            }
            println(String.format("BEGIN %08x %s", target,
                function == null ? "<none>" : function.getName(true)));
            if (function != null) {
                DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
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
