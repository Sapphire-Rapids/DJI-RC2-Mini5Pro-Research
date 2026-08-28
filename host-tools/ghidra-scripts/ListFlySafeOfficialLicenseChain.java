// List current official DJI Fly license-chain functions without decompiling.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ListFlySafeOfficialLicenseChain extends GhidraScript {
    private static final String[] NEEDLES = {
        "NetworkingManager::FetchUnlockLicenseGroups",
        "UnlockLicenseGroupsRequest",
        "FetchLicenseInfoFromServer",
        "FetchLicenseInfoFromLocal",
        "FetchCachedLicenseInfo",
        "FetchAndUploadLicenseData",
        "FetchLicenseData",
        "UploadLicense",
        "FetchLicenseGroupInfo",
        "FetchCachedGroupInfo",
        "UploadLicenseGroupData",
        "LicenseUnlockLocalManager::",
        "LicenseUnlockFCManager::QueryFCLicenseInfo",
        "LicenseUnlockFCManager::SetEnable"
    };

    private boolean wanted(String name) {
        for (String needle : NEEDLES) {
            if (name.contains(needle)) return true;
        }
        return false;
    }

    @Override
    protected void run() {
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function f = functions.next();
            String name = f.getName(true);
            if (wanted(name)) {
                println("FLYSAFE_OFFICIAL_LICENSE_TARGET entry=" + f.getEntryPoint()
                    + " size=" + f.getBody().getNumAddresses()
                    + " thunk=" + f.isThunk() + " name=" + name);
            }
        }
    }
}
