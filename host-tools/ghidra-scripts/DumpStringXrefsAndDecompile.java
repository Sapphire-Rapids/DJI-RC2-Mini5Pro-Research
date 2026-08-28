// Work-only Ghidra helper for locating exact string references in a native library.
// @category Analysis

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class DumpStringXrefsAndDecompile extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] needles = getScriptArgs();
        if (needles.length == 0) {
            throw new IllegalArgumentException("Pass one or more exact or partial string needles");
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Could not open program in decompiler");
        }

        Set<Address> emittedFunctions = new HashSet<>();
        DataIterator dataIterator = currentProgram.getListing().getDefinedData(true);
        while (dataIterator.hasNext() && !monitor.isCancelled()) {
            Data data = dataIterator.next();
            if (!data.hasStringValue()) {
                continue;
            }
            Object rawValue = data.getValue();
            if (!(rawValue instanceof String)) {
                continue;
            }
            String value = (String) rawValue;
            List<String> matchedNeedles = new ArrayList<>();
            for (String needle : needles) {
                if (value.contains(needle)) {
                    matchedNeedles.add(needle);
                }
            }
            if (matchedNeedles.isEmpty()) {
                continue;
            }

            println("\n=== STRING " + data.getAddress() + " " + matchedNeedles + " ===");
            println(value);
            ReferenceIterator references = currentProgram.getReferenceManager()
                .getReferencesTo(data.getAddress());
            boolean foundReference = false;
            while (references.hasNext()) {
                foundReference = true;
                Reference reference = references.next();
                Address from = reference.getFromAddress();
                Function function = currentProgram.getFunctionManager().getFunctionContaining(from);
                println("XREF " + from + " type=" + reference.getReferenceType()
                    + " function=" + (function == null ? "<none>" : function.getName())
                    + " entry=" + (function == null ? "<none>" : function.getEntryPoint()));

                if (function == null || !emittedFunctions.add(function.getEntryPoint())) {
                    continue;
                }
                DecompileResults results = decompiler.decompileFunction(function, 180, monitor);
                println("--- DECOMPILE " + function.getName() + " @ "
                    + function.getEntryPoint() + " ---");
                if (!results.decompileCompleted() || results.getDecompiledFunction() == null) {
                    println("<decompile failed: " + results.getErrorMessage() + ">");
                } else {
                    println(results.getDecompiledFunction().getC());
                }
            }
            if (!foundReference) {
                println("XREF <none>");
            }
        }

        decompiler.dispose();
    }
}
