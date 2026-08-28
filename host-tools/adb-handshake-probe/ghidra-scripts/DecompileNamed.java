// Headless helper used only for the offline RC2 adbd audit.
// Usage: -postScript DecompileNamed.java <function-name-substring> [...]

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class DecompileNamed extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] needles = getScriptArgs();
        if (needles.length == 0) {
            throw new IllegalArgumentException("at least one function-name substring is required");
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("failed to open program in decompiler");
        }

        try {
            for (Function function : currentProgram.getFunctionManager().getFunctions(true)) {
                String qualifiedName = function.getName(true);
                boolean selected = false;
                for (String needle : needles) {
                    if (qualifiedName.contains(needle) ||
                            function.getEntryPoint().toString().equalsIgnoreCase(needle)) {
                        selected = true;
                        break;
                    }
                }
                if (!selected) {
                    continue;
                }

                println("===== " + qualifiedName + " @ " + function.getEntryPoint() + " =====");
                DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
                if (!result.decompileCompleted()) {
                    println("DECOMPILE_FAILED: " + result.getErrorMessage());
                    continue;
                }
                println(result.getDecompiledFunction().getC());
            }
        } finally {
            decompiler.dispose();
        }
    }
}
