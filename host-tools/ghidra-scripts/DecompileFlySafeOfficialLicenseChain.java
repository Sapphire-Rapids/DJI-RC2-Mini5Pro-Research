// Offline, work-only extractor for the current official DJI Fly license chain.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileFlySafeOfficialLicenseChain extends GhidraScript {
    private static final String[] NEEDLES = {
        "NetworkingManager::FetchUnlockLicenseGroups",
        "UnlockLicenseGroupsRequest",
        "FetchLicenseInfoFromServer",
        "FetchLicenseInfoFromLocal",
        "FetchCachedLicenseInfo",
        "FetchAndUploadLicenseData",
        "FetchLicenseData",
        "UploadLicense",
        "LicenseUnlockLocalManager",
        "LicenseUnlockFCManager::QueryFCLicenseInfo",
        "LicenseUnlockFCManager::SetEnable",
        "QueryFCLicenseInfo",
        "SetEnable",
        "FetchLicenseGroupInfo",
        "FetchCachedGroupInfo",
        "UploadLicenseGroupData"
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
            println("BEGIN_FLYSAFE_OFFICIAL_LICENSE_CHAIN entry="
                + function.getEntryPoint() + " size="
                + function.getBody().getNumAddresses() + " name=" + name);
            DecompileResults result = decompiler.decompileFunction(function, 300, monitor);
            if (result != null && result.decompileCompleted()
                    && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED="
                    + (result == null ? "null" : result.getErrorMessage()));
            }
            println("END_FLYSAFE_OFFICIAL_LICENSE_CHAIN entry="
                + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
