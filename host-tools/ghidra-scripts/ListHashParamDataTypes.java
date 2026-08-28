// Offline/read-only inspection of imported datatype metadata for FC hash-param messages.
// @category DJIResearch

import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.Array;
import ghidra.program.model.data.Composite;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataTypeComponent;
import ghidra.program.model.data.Enum;
import java.util.Iterator;

public class ListHashParamDataTypes extends GhidraScript {
    private boolean wanted(DataType dt) {
        String text = (dt.getPathName() + " " + dt.getDisplayName()).toLowerCase();
        return text.contains("cfg_item_info_by_hash") ||
            text.contains("read_hash_param") ||
            text.contains("write_hash_param") ||
            text.contains("configdatatype") ||
            text.contains("cacheconfigkeyinfo");
    }

    @Override
    protected void run() throws Exception {
        Iterator<DataType> it = currentProgram.getDataTypeManager().getAllDataTypes();
        while (it.hasNext()) {
            DataType dt = it.next();
            if (!wanted(dt)) continue;
            println("DATATYPE path=" + dt.getPathName() + " display=" + dt.getDisplayName() +
                " class=" + dt.getClass().getName() + " len=" + dt.getLength());
            if (dt instanceof Composite) {
                Composite composite = (Composite) dt;
                for (DataTypeComponent component : composite.getComponents()) {
                    println(String.format(" COMPONENT off=0x%x len=%d ordinal=%d field=%s type=%s comment=%s",
                        component.getOffset(), component.getLength(), component.getOrdinal(),
                        component.getFieldName(), component.getDataType().getDisplayName(),
                        component.getComment()));
                }
            }
            if (dt instanceof Enum) {
                Enum e = (Enum) dt;
                for (long value : e.getValues()) {
                    println(" ENUM value=" + value + " name=" + e.getName(value));
                }
            }
            if (dt instanceof Array) {
                Array a = (Array) dt;
                println(" ARRAY count=" + a.getNumElements() + " element=" +
                    a.getDataType().getDisplayName());
            }
        }
    }
}
