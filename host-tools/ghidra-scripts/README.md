# Ghidra analysis scripts

This directory contains 82 independently written Java scripts for targeted symbol, reference,
instruction, relocation, and decompiler analysis. They require an already imported local program;
no vendor binary or Ghidra project is included.

## Status and dependencies

- `STATIC`: source-only host analysis helpers. They have no USB, Bluetooth, network, shell, process,
  or Android device-control path.
- `NOT ADMITTED`: a script finding a name, address, cross-reference, or decompiler shape does not
  establish a live Mini 5 Pro route or Remote ID behavior.
- Run them inside Ghidra's Java scripting environment. Standalone `javac` is insufficient because
  the scripts depend on `ghidra.app.*`, `ghidra.program.*`, and the active `currentProgram`.
- The target binary and Ghidra project must be supplied separately and must not be committed here.

Add this directory to Ghidra's Script Manager search paths, or use it as a headless `-scriptPath`.
For inspection runs, prefer a local disposable project and `-readOnly`, for example:

```sh
"$GHIDRA_HOME/support/analyzeHeadless" PROJECT_DIR PROJECT_NAME \
  -process PROGRAM_NAME \
  -scriptPath "$PWD" \
  -postScript DecompileAtAddresses.java 0xADDRESS \
  -readOnly
```

The placeholders above are intentional. Do not add machine-local paths, vendor inputs, project
databases, or redirected decompiler output to this repository.

## Scripts that mutate the local analysis database

Exactly 28 scripts call a Ghidra mutation API such as `disassemble`, `createFunction`,
`Function.setBody`, or `Function.setName`. They can change the currently loaded analysis database
and can persist those changes if the project is saved. They still do not touch the analyzed device
or contact any device:

```text
AnalyzeHashParamTransport.java
CreateAndDecompileAtAddresses.java
DecompileConfigManagerInitCallbacks.java
DecompileF7Callbacks.java
DecompileF7Metadata.java
DecompileF8Callbacks.java
DecompileF9Callbacks.java
DecompileFCMetadataFlow.java
DecompileFlySafeLicenseTask.java
DecompileParamHelpers.java
DecompileRangesAtArgs.java
DecompileRid4BCallbacks.java
DecompileRid4BStateMachine.java
DecompileRidHandlers.java
DecompileRidRegistrationTargeted.java
DecompileUAV139Abstraction.java
DecompileUAV139WillSetup.java
DumpHashParamCode.java
FindFCParamStringLoads.java
FindGeneratedMetadataStringSources.java
InspectFCConfigRegistrationHelpers.java
InspectRidParamRegistration.java
InspectUAV139RegistrationSlices.java
PrintConverterLoadSites.java
PrintFCMetadataEntries.java
PrintInstructionRange.java
RecoverEidLambdaOperators.java
ScanUAV139RidSources.java
```

Use `-readOnly` when you want those transient changes available to the script/decompiler without
saving them to the project. The other 54 scripts only query the existing program model and print
results.

## Checks

At import time the source inventory was checked for:

- 82 unique `.java` filenames and matching public class names;
- exactly the 28 mutation-API users listed above;
- absence of machine-local absolute paths, credentials, direct filesystem-output code, and device
  or network APIs.

No Ghidra installation is bundled in this repository, so Ghidra compilation/execution is an
external-environment check. Script output can contain copied vendor decompilation and must not be
committed; retain only independently written, privacy-reviewed factual summaries.
