# Legacy DJI DroneID `Detection` command

## 1. Scope

This note records a high-confidence correspondence between a public DJI midware command and the
undocumented multi-field DroneID control described by Schiller et al. at NDSS 2023. It separates
legacy proprietary OcuSync/AeroScope DroneID from ASTM/FAA/EU Broadcast Remote ID.

The paper did not publish the command tuple or payload. The numerical correspondence below is an
independent static reconstruction from fixed public DJI-derived sources and exact DJI Fly bytecode;
it must not be described as an author-disclosed command or as current WA150 support. No command was
sent to any device during this review.

The machine-index claims for this topic are C-119 through C-122.

## 2. Public research boundary

The paper analyzed proprietary 91-byte DJI DroneID RF packets carried over OcuSync 2.0 and decoded
by AeroScope-like receivers. Its hardware corpus included Mini 2/RC231, Mavic Air 2/RC231, Mavic 2
Pro/Zoom/RC1B, and a Mavic 3 reproduction statement. Explicit outdoor/flight receiver tests named
Mini 2, Mavic Air 2, and Mavic 2 Pro/Zoom. Static firmware versions listed by the paper included:

| Subject | Listed firmware |
| --- | --- |
| Mavic 2 Pro | `01.00.0770` |
| Mavic 3 | `01.00.0600` |
| Mavic Air 2 | `01.01.0920` |
| Mini 2 | `01.05.0000` |
| RC231 / RC-N1 | `04.11.0034` |

The fuzzer experiments used some earlier versions, including Mavic Air 2 `01.01.0610`, Mini 2
`01.03.0000`, and Mavic 2 Pro `01.00.0770`. The paper does not identify the exact model/firmware on
which the multi-field switch experiment ran, so it does not establish that every listed product
accepts the command.

## 3. High-confidence command correspondence

Fixed DJI-derived midware exposes `DataFlycDetection`, and exact DJI Fly bytecode initializes the
`Detection` command enum to decimal `218`. Together they identify:

| Field | Static value |
| --- | --- |
| Command set | `FLYC`, `0x03` |
| Command ID | `Detection`, `0xDA` |
| Midware logical route | `APP` device type 2 -> `FLYC` device type 3 |
| Packet kind | request, ACK required, no DUML encryption flag |

The Java builder's logical route is not proof of the paper's physical transport. The authors' USB
fuzzer could send directly through an aircraft or relay through a controller, and the paper did not
publish the source identity used for this particular experiment.

Two subcommands form the multi-field mask surface:

| Operation | Request body | Parsed response convention |
| --- | --- | --- |
| `SetSwitch` | `05 <mask:u32le>` | at least `[05, ccode]` |
| `GetSwitch` | `06` | `[06, ccode, mask:u32le]` |

The mask names are:

| Bit | Builder name |
| ---: | --- |
| 0 | `Sn` |
| 1 | `GPS` |
| 2 | `HomeGPS` |
| 3 | `DroneID` |
| 4 | `FlyPlan` |
| 5 | `UUID` |
| 6 | `APPGPS` |
| 7 | `CustomContent` |

The public API names Boolean `true` as enable. No independent public wire capture was found that
proves the physical polarity, so the bit polarity remains builder semantics rather than a live
current-product fact.

Older `fc_monitor` descriptions also place purpose/China real-name functions under top-level
`0x03/0xDA`, but their subcommands `0x01`--`0x04` and payloads are different. They must not be
substituted for the `0x05`/`0x06` multi-field switch.

## 4. What the RF experiment actually showed

The NDSS paper reports that using the apparent configure/disable surface did **not** stop DroneID
packets. The receiver continued to decode packets, while selected values were replaced with the
literal string `fake`.

Therefore this legacy surface is, at most, a field-redaction/substitution mechanism in the tested
legacy DroneID implementation. It is not evidence of a transmitter-off switch, a packet-suppression
switch, or a standards-compliant state transition.

## 5. Why it is not the Mini 5 Pro Broadcast RID switch

The paper explicitly distinguishes DJI's proprietary OcuSync DroneID from draft EN 4709 and ASTM
F3411 Bluetooth/Wi-Fi Broadcast Remote ID. Its fields—aircraft serial, aircraft GPS, home GPS,
app/operator GPS, flight plan, UUID, and custom content—belong to the legacy proprietary packet
model.

Current DJI Fly retains the generic old midware class, but that proves only library inventory. No
public primary evidence was found that WA150/Mini 5 Pro firmware registers `0x03/0xDA` subcommands
`0x05`/`0x06`, routes them to the modern RID subsystem, or maps the mask to ASTM/FAA/EU messages.
The current product-139 status owner is instead the separately recovered `0x11/0x1C`
`RidWorkingStatusPush` path.

Disposition: use this command only as legacy protocol history and a firmware-search signature. Do
not migrate it into a Mini 5 Pro sender, call it a modern RID switch, or perform a live write without
exact WA150 handler, baseline/readback, restoration, and independent RF evidence.

## 6. Sources

- Schiller et al., [Drone Security and the Mysterious Case of DJI's DroneID](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f217_paper.pdf),
  NDSS 2023, DOI `10.14722/ndss.2023.24217`.
- [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity/tree/9ff819843bee48fb140a0704ec78aff757896dea),
  author artifact repository at reviewed HEAD.
- [RUB-SysSec/DroneSecurity-Fuzzer](https://github.com/RUB-SysSec/DroneSecurity-Fuzzer/tree/1410df748b9aecd0cb81ec15282bc570c595eb26),
  whose public README still does not include the fuzzer source.
- Pinned DJI-derived
  [DataFlycDetection](https://github.com/MAVProxyUser/SKYROVER_src/blob/8186e19241c913318b140bf37c5eafba005f1e7c/uav/midware/data/model/P3/DataFlycDetection.java)
  and
  [CmdIdFlyc](https://github.com/MAVProxyUser/SKYROVER_src/blob/8186e19241c913318b140bf37c5eafba005f1e7c/uav/midware/data/config/P3/CmdIdFlyc.java).
- [Author transport clarification](https://github.com/RUB-SysSec/DroneSecurity/issues/15#issuecomment-1576552482),
  which distinguishes aircraft USB access from controller relay without identifying this switch
  experiment's exact source route.

No vendor binary, decompiled source, raw RF capture, device identity, or executable sender is
distributed with this note.
