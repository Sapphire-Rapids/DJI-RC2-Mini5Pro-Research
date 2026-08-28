// List current official DJI Fly FlySafe target functions without decompiling.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ListOfficialFlySafeTargets extends GhidraScript {
    private static final String[] NEEDLES = {
        "Device::GetUnlockVersion",
        "Device::GetUnlockSupported",
        "Device::CheckUnlockVersionAndUpdateGuideRecord",
        "Device::SetupDeviceSupportKeyListeners",
        "LogicManager::CreateDevice",
        "LogicManager::RegisterDevice",
        "LogicManager::GetUnlockVersion",
        "LogicManager::GetUnlockSupported",
        "LicenseUnlockFCManager::QueryFCLicenseInfo",
        "LicenseUnlockFCManager::Setup",
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
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            if (wanted(name)) {
                println("OFFICIAL_TARGET entry=" + function.getEntryPoint()
                    + " size=" + function.getBody().getNumAddresses()
                    + " thunk=" + function.isThunk()
                    + " name=" + name);
            }
        }
    }
}
