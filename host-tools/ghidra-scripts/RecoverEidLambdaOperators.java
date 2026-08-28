// @category FindUAS
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;

public class RecoverEidLambdaOperators extends GhidraScript {
    private void recover(long value, String name, DecompInterface decomp) throws Exception {
        Address entry = toAddr(value);
        Function f = getFunctionAt(entry);
        if (f == null) {
            f = createFunction(entry, name);
        }
        if (f == null) {
            println("CREATE_FAILED " + entry + " " + name);
            return;
        }
        if (f.getName().startsWith("FUN_")) f.setName(name, ghidra.program.model.symbol.SourceType.USER_DEFINED);
        println("BEGIN_FUNCTION " + entry + " " + f.getName(true));
        Instruction ins = getInstructionAt(entry);
        int count = 0;
        while (ins != null && f.getBody().contains(ins.getAddress()) && count++ < 160) {
            println(ins.getAddress() + " " + ins.toString());
            ins = ins.getNext();
        }
        DecompileResults results = decomp.decompileFunction(f, 120, monitor);
        if (results.decompileCompleted()) println(results.getDecompiledFunction().getC());
        else println("DECOMPILE_FAILED " + results.getErrorMessage());
        println("END_FUNCTION " + entry);
    }

    @Override
    public void run() throws Exception {
        long[] addrs = {
            0x02da093cL, 0x02da0c38L,
            0x04e132f4L, 0x04e135f0L,
            0x02da8940L, 0x02da90f4L,
            0x04e15618L,
            0x05182960L, 0x05182970L, 0x05182980L,
            0x05170990L, 0x0517a670L, 0x0517a680L,
            0x05170630L, 0x05170640L, 0x0517030cL,
            0x05169bf0L, 0x05173130L, 0x05173390L, 0x05173800L, 0x05175da0L,
            0x051720a0L, 0x0515dc70L, 0x0515dc80L
        };
        String[] names = {
            "eid_abstraction_get_converter_operator",
            "eid_abstraction_set_checker_operator",
            "eid_keyhandler_get_converter_operator",
            "eid_keyhandler_set_checker_operator",
            "eid_common_empty_destructor_thunk",
            "eid_abstraction_set_destructor_thunk",
            "eid_keyhandler_set_destructor_thunk",
            "eid_req_ctor_plt", "eid_base_send_get_plt", "eid_base_send_set_plt",
            "eid_characteristics_route_lookup_plt", "eid_route_type_ptr_plt", "eid_route_index_ptr_plt",
            "eid_req_receiver_changed_plt", "eid_base_send_provider_plt", "eid_base_ctor_plt",
            "eid_named_port_send_plt", "eid_mix_primary_ctor_plt", "eid_uav139_secondary_ctor_plt",
            "eid_fc_abstraction_ctor_plt", "eid_component_abstraction_ctor_plt",
            "eid_set_runtime_sender_seq_plt", "eid_packet_status_singleton_plt",
            "eid_global_sender_index_plt"
        };
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        for (int i = 0; i < addrs.length; i++) recover(addrs[i], names[i], decomp);
        decomp.dispose();
    }
}
