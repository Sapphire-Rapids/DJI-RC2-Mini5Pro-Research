// Print only control-flow/call lines from decompilation for compact offline review.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class SummarizeOfficialFlySafeByAddress extends GhidraScript {
    private boolean useful(String line) {
        String s = line.trim();
        return s.startsWith("case ") || s.startsWith("switch")
            || s.startsWith("if (") || s.startsWith("else")
            || s.startsWith("return") || s.contains("ErrorCode")
            || s.contains("FetchLicense") || s.contains("UploadLicense")
            || s.contains("SetEnable") || s.contains("QueryFCLicense")
            || s.contains("ParseOnboard") || s.contains("ParseJson")
            || s.contains("LicenseData") || s.contains("license_unlock_key")
            || s.contains("NetworkingManager") || s.contains("LicenseUnlock")
            || s.contains("GetAccount") || s.contains("GetUser")
            || s.contains("Base64Decode") || s.contains("ParseFrom")
            || s.contains("operator[]") || s.contains("int_value")
            || s.contains("number_value") || s.contains("bool_value")
            || s.contains("string_value");
    }

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Could not open program in decompiler");
        }
        for (String arg : getScriptArgs()) {
            Address address = toAddr(Long.decode(arg));
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                println("NO_FUNCTION address=" + address);
                continue;
            }
            println("BEGIN_SUMMARY entry=" + address + " name=" + function.getName(true));
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                for (String line : result.getDecompiledFunction().getC().split("\\R")) {
                    if (useful(line)) println(line);
                }
            } else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_SUMMARY entry=" + address);
        }
        decompiler.dispose();
    }
}
