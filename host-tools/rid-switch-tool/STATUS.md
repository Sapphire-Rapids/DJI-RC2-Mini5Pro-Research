# Status

Classification: `STATIC` source with synthetic tests; `NOT ADMITTED` as a device write.

The source publishes the fixed F7/F8/F9 codec, the positive-control gate, the
baseline snapshot, the single forward write, a bounded immediate restore attempt,
and strict F8 readbacks. Lost forward ACKs enter restoration; a lost restore ACK
still permits one final state read. Failure to read the original bytes leaves
restoration explicitly unverified. Writes are limited to one-byte Boolean values
whose canonical metadata bounds permit both 0 and 1. A zero-range flag remains
readable but cannot trigger a forward or restore write. A requested bridge failure
retains partial reads, exits nonzero and blocks every write.
Passing the offline tests does not establish that a connected Mini 5 Pro
accepts the route, applies the parameter, or changes Remote ID RF behaviour.

No live write result is claimed here. Repairs do not readmit the closed
`rid_ctrl_enable_0` or `EU_CE_enable_c0_rid_0` / `EU_CE_enable_c0_rid` candidates on
Mini 5 Pro `01.00.0600`, and do not authorize repeating known failed routes.
A forward F9 is only sent after a same-session
positive control and a genuine `rid_ctrl_enable_0` Boolean baseline, and the baseline
is immediately submitted for restoration. Motor-on RF observation is operator-initiated and must use
the independent receiver.
