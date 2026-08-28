// Read-only exact-body decompilation of the FC config metadata/cache path.
// Imported dynamic symbols in the quick project initially have one-byte bodies,
// so establish bodies from the next known symbol before decompiling.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileFCMetadataFlow extends GhidraScript {
    private static final long[][] RANGES = {
        { 0x01f1dfd0L, 0x01f1e0e7L }, // Initialize
        { 0x01f1e19cL, 0x01f1e233L }, // DeviceReady
        { 0x01f1e234L, 0x01f1e2c7L }, // GetConfigKeyInfos
        { 0x01f1e500L, 0x01f1efe3L }, // ReadConfig (F8)
        { 0x01f1efe4L, 0x01f1f40fL }, // RequestConfigRange (F7)
        { 0x01f1f410L, 0x01f1faffL }, // WriteConfig (F9)
        { 0x01f217ecL, 0x01f218c7L }, // F7 success callback
        { 0x01f51370L, 0x01f515a7L }, // CCacheConfigKeyInfo::Builder::build
        { 0x01f515a8L, 0x01f51747L }, // CCacheConfigKeyInfo ctor
        { 0x03b6449cL, 0x03b64667L }  // core::FCConfigInfo ctor
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long[] range : RANGES) {
            long startValue = range[0];
            long endValue = range[1];
            Address start = toAddr(startValue);
            Address end = toAddr(endValue);
            for (long at = startValue; at <= endValue; at += 4) {
                disassemble(toAddr(at));
            }
            Function function = getFunctionAt(start);
            if (function == null) function = createFunction(start, null);
            if (function != null) function.setBody(new AddressSet(start, end));
            println(String.format("BEGIN %08x-%08x %s", startValue, endValue,
                function == null ? "<none>" : function.getName(true)));
            if (function != null) {
                DecompileResults result = decompiler.decompileFunction(function, 240, monitor);
                if (result != null && result.decompileCompleted() &&
                    result.getDecompiledFunction() != null) {
                    println(result.getDecompiledFunction().getC());
                }
                else println("FAILED " + (result == null ? "null" : result.getErrorMessage()));
            }
            println(String.format("END %08x", startValue));
        }
        decompiler.dispose();
    }
}
