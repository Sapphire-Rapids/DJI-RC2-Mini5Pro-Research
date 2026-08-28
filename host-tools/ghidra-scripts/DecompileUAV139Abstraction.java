// Read-only decompilation of the wa150 / product-type-139 FC abstraction glue.
// @category DJIResearch

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;

public class DecompileUAV139Abstraction extends GhidraScript {
    private static final long[] TARGETS = {
        0x026c10d0L, // TryCreateAbstraction<...UAV139FCAbs>
        0x026c21dcL, // MixAbs ctor
        0x026c2540L, // CreateCharacteristics
        0x026c2fd0L, // WillSetup
        0x0326414cL, // UAV139FCAbs::CreateCharacteristics
        0x0329a84cL, // UAV139FCAbs::WillSetup
        0x032af24cL  // UAV139FCAbs::OnFirmwareVersionChange
    };

    @Override
    protected void run() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long target : TARGETS) {
            disassemble(toAddr(target));
            Function function = getFunctionAt(toAddr(target));
            if (function == null) function = createFunction(toAddr(target), null);
            println("BEGIN " + function.getEntryPoint() + " " + function.getName());
            DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
            if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
                println(result.getDecompiledFunction().getC());
            } else {
                println("DECOMPILE_FAILED " + result.getErrorMessage());
            }
            println("INSTRUCTIONS");
            Instruction instruction = getInstructionAt(function.getEntryPoint());
            while (instruction != null && function.getBody().contains(instruction.getAddress())) {
                println(instruction.getAddress() + " " + instruction);
                instruction = instruction.getNext();
            }
            println("END " + function.getEntryPoint());
        }
        decompiler.dispose();
    }
}
