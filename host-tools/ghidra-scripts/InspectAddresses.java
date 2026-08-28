// Print bounded bytes, pointer values, symbols, and relocations at exact addresses.
// Offline read-only helper for the RID 0x11/0x4b audit.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.reloc.Relocation;
import ghidra.program.model.symbol.Symbol;

public class InspectAddresses extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0 || (args.length & 1) != 0) {
            throw new IllegalArgumentException("usage: <address> <byte-count> [address byte-count ...]");
        }
        Memory memory = currentProgram.getMemory();
        for (int pair = 0; pair < args.length; pair += 2) {
            Address address = toAddr(Long.decode(args[pair]));
            int length = Integer.decode(args[pair + 1]);
            byte[] bytes = new byte[length];
            int read = memory.getBytes(address, bytes);
            StringBuilder hex = new StringBuilder();
            StringBuilder ascii = new StringBuilder();
            for (int index = 0; index < read; index++) {
                int value = bytes[index] & 0xff;
                hex.append(String.format("%02x", value));
                ascii.append(value >= 0x20 && value <= 0x7e ? (char)value : '.');
            }
            Symbol symbol = currentProgram.getSymbolTable().getPrimarySymbol(address);
            println("ADDRESS=" + address + " bytes=" + read + " hex=" + hex +
                " ascii=" + ascii + " symbol=" + (symbol == null ? "-" : symbol.getName(true)));
            if (length >= 8) {
                println("  pointer=0x" + Long.toUnsignedString(memory.getLong(address), 16));
            }
            java.util.List<Relocation> relocs =
                currentProgram.getRelocationTable().getRelocations(address);
            for (Relocation relocation : relocs) {
                println("  relocation type=" + relocation.getType() + " status=" +
                    relocation.getStatus() + " symbol=" + relocation.getSymbolName() +
                    " values=" + java.util.Arrays.toString(relocation.getValues()));
            }
        }
    }
}
