// @category FindUAS
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.reloc.Relocation;
import ghidra.program.model.symbol.Symbol;

public class DescribeEidTargets extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        for (String raw : args) {
            Address a = toAddr(Long.decode(raw));
            Function at = getFunctionAt(a);
            Function containing = getFunctionContaining(a);
            Symbol[] syms = currentProgram.getSymbolTable().getSymbols(a);
            println("TARGET " + a + " functionAt=" + (at == null ? "<none>" : at.getName(true)) +
                " containing=" + (containing == null ? "<none>" : containing.getName(true)));
            for (Symbol s : syms) println("  SYMBOL " + s.getSymbolType() + " " + s.getName(true));
            java.util.List<Relocation> relocs = currentProgram.getRelocationTable().getRelocations(a);
            for (Relocation relocation : relocs) println("  RELOC " + relocation.getSymbolName() + " " + relocation);
            if (currentProgram.getMemory().contains(a)) {
                try { println("  QWORD 0x" + Long.toHexString(getLong(a))); } catch (Exception ignored) {}
            }
        }
    }
}
