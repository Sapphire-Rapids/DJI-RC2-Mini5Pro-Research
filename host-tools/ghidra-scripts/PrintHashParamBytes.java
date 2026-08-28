// Compare loaded bytes to raw opcode candidates.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class PrintHashParamBytes extends GhidraScript {
    private static final long[] ADDRESSES = {
        0x01e1e55cL, 0x01e1f074L, 0x01e1f608L, 0x01e1fd4cL,
        0x02d2a808L, 0x02d2ae98L, 0x02d2b230L, 0x02d2b6acL
    };

    @Override
    protected void run() throws Exception {
        for (long value : ADDRESSES) {
            Address address = toAddr(value);
            byte[] bytes = new byte[16];
            currentProgram.getMemory().getBytes(address, bytes);
            StringBuilder hex = new StringBuilder();
            for (byte b : bytes) {
                hex.append(String.format("%02x", b & 0xff));
            }
            println(address + " bytes=" + hex);
        }
    }
}
