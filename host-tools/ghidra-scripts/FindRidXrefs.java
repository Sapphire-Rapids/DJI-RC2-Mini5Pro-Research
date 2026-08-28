// Ghidra headless helper for a narrow, read-only RID cross-reference audit.
// @category DJIResearch

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.DataType;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class FindRidXrefs extends GhidraScript {
    private static final String[] TARGETS = {
        "IsEuCeEnableC0Rid",
        "CccBroadcastSignalQuality",
        "EIDSwitch",
        "RidWorkingStatusPush",
        "RemoteIDHelper",
        "OIDIdentifier",
        "ComplianceSerialNumber"
    };

    @Override
    protected void run() throws Exception {
        println("PROGRAM=" + currentProgram.getName());
        println("LANG=" + currentProgram.getLanguageID());

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        Set<Address> emitted = new HashSet<>();

        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext() && !monitor.isCancelled()) {
            Function function = functions.next();
            String name = function.getName(true);
            if (matches(name)) {
                emitFunction("FUNCTION_NAME", function, decompiler, emitted);
            }
        }

        for (Data data : currentProgram.getListing().getDefinedData(true)) {
            if (monitor.isCancelled()) {
                break;
            }
            Object value = data.getValue();
            String rendered = value == null ? data.getDefaultValueRepresentation() : value.toString();
            if (!matches(rendered)) {
                continue;
            }
            DataType type = data.getDataType();
            println("STRING address=" + data.getAddress() + " type=" + type.getName() + " value=" + rendered);
            ReferenceIterator references = currentProgram.getReferenceManager().getReferencesTo(data.getAddress());
            int count = 0;
            while (references.hasNext()) {
                Reference reference = references.next();
                count++;
                Address from = reference.getFromAddress();
                Function function = currentProgram.getFunctionManager().getFunctionContaining(from);
                println("XREF from=" + from + " type=" + reference.getReferenceType() +
                    " function=" + (function == null ? "<none>" : function.getName(true)));
                if (function != null) {
                    emitFunction("STRING_XREF", function, decompiler, emitted);
                }
            }
            println("XREF_COUNT=" + count);
        }

        decompiler.dispose();
        println("TARGETS=" + Arrays.toString(TARGETS));
    }

    private boolean matches(String text) {
        if (text == null) {
            return false;
        }
        for (String target : TARGETS) {
            if (text.contains(target)) {
                return true;
            }
        }
        return false;
    }

    private void emitFunction(String reason, Function function, DecompInterface decompiler,
            Set<Address> emitted) {
        if (!emitted.add(function.getEntryPoint())) {
            return;
        }
        println("BEGIN_FUNCTION reason=" + reason + " entry=" + function.getEntryPoint() +
            " name=" + function.getName(true));
        DecompileResults result = decompiler.decompileFunction(function, 90, monitor);
        if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
            println(result.getDecompiledFunction().getC());
        }
        else {
            println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
        }
        println("END_FUNCTION entry=" + function.getEntryPoint());
    }
}
