// Offline, work-only extractor for current official DJI Fly FlySafe routing.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileOfficialFlySafeCoreTargets extends GhidraScript {
    private static final String[] NEEDLES = {
        "Device::Device",
        "Device::Setup",
        "Device::GetUnlockVersion",
        "Device::GetUnlockSupported",
        "Device::CheckUnlockVersionAndUpdateGuideRecord",
        "LogicManager::CreateDevice",
        "LogicManager::RegisterDevice",
        "LogicManager::GetUnlockVersion",
        "LogicManager::GetUnlockSupported",
        "LicenseUnlockFCManager::Setup",
        "LicenseUnlockFCManager::QueryFCLicenseInfo",
        "LicenseUnlockFCManager::GetFCOp",
        "LicenseQueryV2Session::StartQueryFCLicenseInfo",
        "LicenseQueryV2Session::QueryFCLicenseInfoQueue",
        "LicenseQueryV3Session::StartQueryFCLicenseInfo",
        "LicenseQueryV3Session::QueryFCLicenseInfoQueue",
        "LicenseQueryV4Session::StartQueryFCLicenseInfo",
        "LicenseQueryV4Session::QueryFCLicenseInfoQueue",
        "PackManager::SendPack",
        "QueryLicenseUnlockVersion",
        "QueryFCLicenseInfo"
    };

    private boolean wanted(String name) {
        for (String needle : NEEDLES) {
            if (name.contains(needle)) {
                return true;
            }
        }
        return false;
    }

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
            if (!wanted(name)) {
                continue;
            }
            println("BEGIN_OFFICIAL_FLYSAFE entry=" + function.getEntryPoint()
                + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_OFFICIAL_FLYSAFE entry=" + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
