# FindUAS privacy-reduced transcript

This tool summarizes FindUASMac's local `telemetry.jsonl` history without publishing the sensitive
values it contains. It is intended to support the C-207 motor-off → motor-on → motor-off observation
record, not to replace the operator's live observations or the independent receiver.

The tool reads only the named local input file. It does not access a receiver, aircraft, network, USB
device, or FindUASMac application state. It never emits full UAS IDs, registration IDs, receiver
identifiers, coordinates, phone numbers, manufacturer/model strings, raw frames, account material, or
credentials.

## Usage

```sh
python3 finduas_redact_transcript.py "$HOME/Library/Application Support/FindUASMac/telemetry.jsonl" --stdout-only

# Write a sibling .redacted.md file, including a short opaque ID digest prefix
python3 finduas_redact_transcript.py "$HOME/Library/Application Support/FindUASMac/telemetry.jsonl" --digest-prefix
```

The input remains private. Inspect the generated summary before committing it. If it contains any
identifying value, do not publish it and file a repository issue instead.

The output records:

- input and distinct-target counts;
- receiver-reported RID standard;
- first/last local record timestamps;
- presence of UAS ID, registration ID, location, operator location, manufacturer/model, and ID type;
- an optional 12-character SHA-256 prefix for each distinct UAS ID, only when explicitly requested.

It does not classify the aircraft's exact air bearer. FindUASMac's BLE link to the FindUAS receiver is
not evidence that the aircraft transmits Remote ID over BLE or Wi-Fi; record that value only from the
receiver's explicit display or another independent receiver observation.

## Tests

```sh
python3 -m unittest -v test_finduas_redact_transcript.py
```
