# C-207 motor-on standardized Remote ID observation form

## Purpose

This one-session form closes the highest-priority evidence gap: a written motor-off → motor-on →
motor-off record against the already-confirmed plaintext standardized Remote ID bearer. It records
only the presence, standard, bearer, and timing of independently observed messages. It is not a
state-change experiment and does not authorize any RID write.

## Safety and authorization

- Work only with the user's own RC 2 `07.00.0100`, Mini 5 Pro, and verified standard Remote ID
  receiver.
- FindUASMac may be used as the local receiver frontend and timestamp source, but the Mac's BLE link
  to the FindUAS receiver is not itself evidence of the aircraft's exact air bearer. Record `BLE`
  or `Wi-Fi` only when the receiver or another independent receiver display explicitly reports it;
  otherwise record `UNKNOWN`.
- Use a controlled area, keep the aircraft secured, and let the operator alone start and stop the
  motors.
- Keep motors stopped before the baseline and after the final observation; software must not start
  motors.
- Do not change any setting, write any parameter, import or toggle a license, or attach an agent.
- Do not photograph or copy the receiver screen if it contains the real Basic ID, operator ID, GPS
  coordinates, serial number, or other private identifiers.

## Recording rules

Record each transition at the moment it happens. Use one consistent local clock for the receiver,
operator, and optional onboard-status observation. Write `UNKNOWN` rather than guessing.

Allowed:

- clock timestamps and elapsed seconds;
- observed standard (`ASTM F3411` or `EN 4709`) as shown by the receiver;
- exact bearer class (`BLE` or `Wi-Fi`) as shown by the receiver;
- message/field presence (`yes`, `no`, or `UNKNOWN`);
- per-phase receiver frame counts, if available;
- a privacy-preserving digest prefix of the Basic ID, only if the user explicitly consents;
- motor command result (`started` or `stopped`) as manually observed by the operator.

Not allowed in the public form:

- full Basic ID, operator ID, serial number, or flight-control serial number;
- GPS coordinates, home-point coordinates, or location traces;
- raw frames, raw capture files, receiver screenshots containing identifiers, or private logs;
- account, license, token, key, or credential material.

If FindUASMac is used, its local `telemetry.jsonl` history may contain the full UAS ID, receiver
identifier, and precise coordinates. Do not copy or commit that file, export target details, or
quote its identifiers into this public form. Only the redacted fields above may be transcribed.
The repository's offline tool
[`../host-tools/finduas-transcript/finduas_redact_transcript.py`](../host-tools/finduas-transcript/finduas_redact_transcript.py)
can summarize that local JSONL without emitting full identifiers or coordinates, but its output is
only a supporting transcript and still requires operator motor-transition timestamps and receiver
bearer evidence.

## Session identity

| Field | Entry |
| --- | --- |
| Date | 2026-__-__ |
| Local timezone | __ |
| Aircraft / firmware | Mini 5 Pro / UNKNOWN |
| RC 2 / firmware | RC 2 / 07.00.0100 |
| DJI Fly session state | UNKNOWN |
| Receiver model / app | __ / __ |
| Receiver independently verified before | yes / no |
| Controlled area confirmed | yes / no |
| Motors manually controlled by operator | yes / no |
| No RID/FlySafe write this session | yes |

## Observation A — motors-off baseline

Start after normal aircraft/controller link and receiver warm-up. Keep motors stopped. Observe for
at least 60 seconds.

| Field | Entry |
| --- | --- |
| Start timestamp | __:__:__ |
| End timestamp | __:__:__ |
| Duration seconds | __ |
| Standardized Remote ID observed | yes / no / UNKNOWN |
| Exact bearer class | BLE / Wi-Fi / UNKNOWN |
| Basic ID message present | yes / no / UNKNOWN |
| Location message present | yes / no / UNKNOWN |
| System message present | yes / no / UNKNOWN |
| Operator ID message present | yes / no / UNKNOWN |
| Self ID message present | yes / no / UNKNOWN |
| Message Pack present | yes / no / UNKNOWN |
| Receiver frame count | __ / UNKNOWN |
| Motors remained off | yes / no |

## Transition A → B — operator motor start

| Field | Entry |
| --- | --- |
| Motor-start command timestamp | __:__:__ |
| First receiver detection timestamp | __:__:__ |
| Latency seconds | __ / UNKNOWN |
| Motor state at first detection | running / stopped / UNKNOWN |
| Any private OcuSync/DroneID observation | not recorded |

## Observation B — motors running

Observe while the motors run for at least 60 seconds. Do not move a control surface or setting other
than what is needed to keep the secured aircraft and motors in a safe state.

| Field | Entry |
| --- | --- |
| Start timestamp | __:__:__ |
| End timestamp | __:__:__ |
| Duration seconds | __ |
| Standardized Remote ID observed | yes / no / UNKNOWN |
| Exact bearer class | BLE / Wi-Fi / UNKNOWN |
| Basic ID message present | yes / no / UNKNOWN |
| Basic ID readability | readable / unreadable / UNKNOWN |
| Location message present | yes / no / UNKNOWN |
| System message present | yes / no / UNKNOWN |
| Operator ID message present | yes / no / UNKNOWN |
| Self ID message present | yes / no / UNKNOWN |
| Message Pack present | yes / no / UNKNOWN |
| Receiver frame count | __ / UNKNOWN |
| Motors remained running | yes / no |

## Transition B → C — operator motor stop

| Field | Entry |
| --- | --- |
| Motor-stop command timestamp | __:__:__ |
| Last standardized-RID detection timestamp | __:__:__ |
| Latency seconds | __ / UNKNOWN |
| Motor state at last detection | running / stopped / UNKNOWN |

## Observation C — motors-off post-state

Continue observing for at least 60 seconds after motor stop. Do not reconnect or change any setting
during this interval.

| Field | Entry |
| --- | --- |
| Start timestamp | __:__:__ |
| End timestamp | __:__:__ |
| Duration seconds | __ |
| Standardized Remote ID observed | yes / no / UNKNOWN |
| Exact bearer class | BLE / Wi-Fi / UNKNOWN |
| Basic ID message present | yes / no / UNKNOWN |
| Location message present | yes / no / UNKNOWN |
| System message present | yes / no / UNKNOWN |
| Operator ID message present | yes / no / UNKNOWN |
| Self ID message present | yes / no / UNKNOWN |
| Message Pack present | yes / no / UNKNOWN |
| Receiver frame count | __ / UNKNOWN |
| Motors remained off | yes / no |

## Optional onboard-status record

Use only a naturally pushed official status or HMS already visible to DJI Fly. Do not create a
polling request, second broker client, Binder listener, or written query.

| Field | Entry |
| --- | --- |
| Source | natural push / HMS / not available |
| A state at baseline | __ / UNKNOWN |
| B state while running | __ / UNKNOWN |
| C state after stop | __ / UNKNOWN |
| GPS/operator-location readiness | ready / not ready / UNKNOWN |

## Completion audit

The form is complete only when all four checks are true:

1. The receiver produced a valid standardized-RID positive observation during phase B.
2. The exact bearer class is recorded as `BLE` or `Wi-Fi`, not `UNKNOWN`.
3. The Basic ID presence/readability and all motor transitions are timestamped.
4. The public record contains no full identifier, coordinate, raw frame, capture, account, license,
   or credential material.

Record the result as a new `OBSERVED` claim only after this audit. An absent motor-off broadcast is
not proof that broadcasting is globally off; it only describes this secured, motor-off session.
