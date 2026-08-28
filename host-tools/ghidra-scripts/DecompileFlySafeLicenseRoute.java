// Work-only helper for tracing the read-only FlySafe license inventory path.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileFlySafeLicenseRoute extends GhidraScript {
    private static final String[] NEEDLES = {
        "QueryLicenseFromFC",
        "query_license_from_fc",
        "JNI_QueryLicenseFromFC",
        "FlysafeLicenseGroupMsg",
        "RequestLicenseInfoList",
        "request_license_info_list"
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Could not open program in decompiler");
        }

        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            boolean matches = false;
            for (String needle : NEEDLES) {
                if (name.contains(needle)) {
                    matches = true;
                    break;
                }
            }
            if (!matches) {
                continue;
            }

            println("BEGIN_FLYSAFE_LICENSE_ROUTE entry=" + function.getEntryPoint()
                + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 240, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_FLYSAFE_LICENSE_ROUTE entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
