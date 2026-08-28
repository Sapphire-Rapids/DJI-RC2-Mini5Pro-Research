// Decompile exact start/end-exclusive address pairs in an offline read-only run.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;

public class DecompileRangesAtArgs extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0 || (args.length & 1) != 0) {
            throw new IllegalArgumentException("usage: <start> <end-exclusive> [start end-exclusive ...]");
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("could not open program");
        }
        for (int pair = 0; pair < args.length; pair += 2) {
            long start = Long.decode(args[pair]);
            long endExclusive = Long.decode(args[pair + 1]);
            Address entry = toAddr(start);
            for (long at = start; at < endExclusive; at += 4) {
                disassemble(toAddr(at));
            }
            Function function = getFunctionAt(entry);
            if (function == null) {
                function = createFunction(entry, "offline_range_" + Long.toHexString(start));
            }
            if (function == null) {
                println(String.format("NO_FUNCTION %08x", start));
                continue;
            }
            function.setBody(new AddressSet(entry, toAddr(endExclusive - 1)));
            println(String.format("BEGIN_RANGE %08x-%08x %s", start, endExclusive - 1,
                function.getName(true)));
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println(String.format("END_RANGE %08x", start));
        }
        decompiler.dispose();
    }
}
