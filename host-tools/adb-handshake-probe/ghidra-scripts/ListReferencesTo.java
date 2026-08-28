// Headless helper for the offline RC2 adbd audit.
// Usage: -postScript ListReferencesTo.java <symbol-or-address> [...]

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ListReferencesTo extends GhidraScript {
    @Override
    public void run() throws Exception {
        for (String query : getScriptArgs()) {
            boolean matched = false;
            SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
            while (symbols.hasNext()) {
                Symbol symbol = symbols.next();
                if (!symbol.getName(true).equals(query) && !symbol.getName().equals(query)) {
                    continue;
                }
                matched = true;
                printReferences(symbol.getName(true), symbol.getAddress());
            }

            if (!matched) {
                Address address = currentProgram.getAddressFactory().getDefaultAddressSpace()
                        .getAddress(query);
                if (address == null) {
                    println("NOT_FOUND " + query);
                } else {
                    printReferences(query, address);
                }
            }
        }
    }

    private void printReferences(String label, Address address) {
        println("===== " + label + " @ " + address + " =====");
        ReferenceIterator references = currentProgram.getReferenceManager().getReferencesTo(address);
        int count = 0;
        while (references.hasNext()) {
            Reference reference = references.next();
            println(reference.getFromAddress() + " -> " + reference.getToAddress() +
                    " type=" + reference.getReferenceType() +
                    " operand=" + reference.getOperandIndex());
            count++;
        }
        println("REFERENCE_COUNT " + count);
    }
}
