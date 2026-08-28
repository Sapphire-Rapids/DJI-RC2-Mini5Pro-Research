// Inspect helper calls used by RidImportModule::OnRIDWorkingStatusPush.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.address.AddressRangeIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.mem.MemoryBlockSourceInfo;
import ghidra.program.model.reloc.Relocation;
import ghidra.program.model.reloc.RelocationTable;
import java.util.Iterator;

public class InspectRidStatusHelpers extends GhidraScript {
    private void inspect(String encodedAddress) throws Exception {
        Address address = toAddr(encodedAddress);
        println("BEGIN_HELPER address=" + address);
        Function function = getFunctionAt(address);
        if (function == null) {
            function = getFunctionContaining(address);
        }
        println("function=" + (function == null ? "null" : function.getName(true)));

        Reference[] references = getReferencesTo(address);
        println("references=" + references.length);
        for (Reference reference : references) {
            println("xref=" + reference.getFromAddress() + " type=" + reference.getReferenceType());
        }

        Instruction instruction = getInstructionAt(address);
        int count = 0;
        while (instruction != null && count < 48) {
            println("insn=" + instruction.getAddress() + " " + instruction);
            instruction = instruction.getNext();
            count += 1;
        }

        if (function != null) {
            DecompInterface decompiler = new DecompInterface();
            decompiler.openProgram(currentProgram);
            DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
            if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            }
            else {
                println("DECOMPILE_FAILED=" + (result == null ? "null" : result.getErrorMessage()));
            }
            decompiler.dispose();
        }
        println("END_HELPER address=" + address);
    }

    private void inspectFunction(String encodedAddress) throws Exception {
        Address address = toAddr(encodedAddress);
        Function function = getFunctionContaining(address);
        println("BEGIN_CALLER address=" + address + " function=" +
            (function == null ? "null" : function.getName(true)));
        if (function != null) {
            println("caller_body=" + function.getBody() + " addresses=" +
                function.getBody().getNumAddresses());
            AddressRangeIterator ranges = function.getBody().getAddressRanges();
            while (ranges.hasNext()) {
                AddressRange range = ranges.next();
                println("caller_range=" + range.getMinAddress() + ".." + range.getMaxAddress());
            }
            Instruction instruction = currentProgram.getListing().getInstructions(function.getBody(), true).hasNext()
                ? currentProgram.getListing().getInstructions(function.getBody(), true).next()
                : null;
            while (instruction != null && function.getBody().contains(instruction.getAddress())) {
                StringBuilder references = new StringBuilder();
                for (Reference reference : instruction.getReferencesFrom()) {
                    if (references.length() > 0) {
                        references.append(",");
                    }
                    references.append(reference.getToAddress());
                    references.append(":");
                    references.append(reference.getReferenceType());
                }
                println("caller_insn=" + instruction.getAddress() + " " + instruction +
                    " refs=" + references);
                instruction = instruction.getNext();
            }
        }
        println("END_CALLER address=" + address);
    }

    private void dumpBytes(String encodedAddress, int length) throws Exception {
        Address address = toAddr(encodedAddress);
        Memory memory = currentProgram.getMemory();
        byte[] bytes = new byte[length];
        int count = memory.getBytes(address, bytes);
        StringBuilder hex = new StringBuilder();
        for (int index = 0; index < count; index += 1) {
            hex.append(String.format("%02x", bytes[index] & 0xff));
        }
        println("bytes address=" + address + " count=" + count + " hex=" + hex);
        MemoryBlock block = memory.getBlock(address);
        if (block != null) {
            println("block=" + block.getName() + " range=" + block.getStart() + ".." +
                block.getEnd() + " execute=" + block.isExecute());
            for (MemoryBlockSourceInfo sourceInfo : block.getSourceInfos()) {
                println("block_source=" + sourceInfo + " file_offset=" +
                    sourceInfo.getFileBytesOffset(address));
            }
        }
    }

    @Override
    protected void run() throws Exception {
        inspect("0517bed0");
        inspect("05175ff0");
        inspectFunction("02cec558");
        dumpBytes("0139ff20", 48);
        dumpBytes("02cec558", 768);
        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            Symbol symbol = symbols.next();
            if (symbol.getName(true).contains("to_string")) {
                println("to_string_symbol=" + symbol.getName(true) + " address=" +
                    symbol.getAddress() + " type=" + symbol.getSymbolType());
            }
        }
        for (String encodedAddress : new String[] {"0517bed0", "0534ba98", "05175ff0", "05348b28"}) {
            Address address = toAddr(encodedAddress);
            Symbol primary = currentProgram.getSymbolTable().getPrimarySymbol(address);
            println("address_symbol=" + address + " primary=" +
                (primary == null ? "null" : primary.getName(true)));
        }
        RelocationTable relocationTable = currentProgram.getRelocationTable();
        Iterator<Relocation> relocations = relocationTable.getRelocations();
        while (relocations.hasNext()) {
            Relocation relocation = relocations.next();
            long offset = relocation.getAddress().getOffset();
            if (offset == 0x0534ba98L || offset == 0x05348b28L) {
                println("relocation=" + relocation.getAddress() + " type=" + relocation.getType() +
                    " symbol=" + relocation.getSymbolName());
            }
        }
    }
}
