// Read-only recovery of callbacks installed by FlightControllerConfigManager::Initialize.
// @category DJIResearch

import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileConfigManagerInitCallbacks extends GhidraScript {
    private static final long[] VTABLES = { 0x051c46b0L, 0x051c47b0L };

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
                if (slot == 0x30 && target >= 0x01f10000L && target < 0x01f24000L) {
                    targets.add(target);
                }
            }
        }
        Long[] ordered = targets.toArray(new Long[0]);
        for (int i = 0; i < ordered.length; i++) {
            long target = ordered[i];
            long end = target == 0x01f20440L ? 0x01f2065fL : 0x01f20a8fL;
            Address address = toAddr(target);
            for (long at = target; at <= end; at += 4) disassemble(toAddr(at));
            Function function = getFunctionAt(address);
            if (function == null) function = createFunction(address, null);
            if (function != null) function.setBody(new AddressSet(address, toAddr(end)));
            println(String.format("BEGIN %08x-%08x %s", target, end,
                function == null ? "<none>" : function.getName(true)));
            if (function != null) {
                DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
                if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                    println(result.getDecompiledFunction().getC());
                }
                else println("FAILED " + (result == null ? "null" : result.getErrorMessage()));
            }
            println(String.format("END %08x", target));
        }
        decompiler.dispose();
    }
}
