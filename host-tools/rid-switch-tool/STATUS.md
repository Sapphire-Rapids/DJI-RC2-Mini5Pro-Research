# Status

Classification: `STATIC` source with synthetic tests; `NOT ADMITTED` as a device write.

The source publishes the fixed F7/F8/F9 codec, the positive-control gate, the
baseline snapshot, the single forward write, the immediate restore, and the strict
F8 readbacks. Passing the offline tests does not establish that a connected Mini 5 Pro
accepts the route, applies the parameter, or changes Remote ID RF behaviour.

No live write result is claimed here. A forward F9 is only sent after a same-session
positive control and a genuine `rid_ctrl_enable_0` Boolean baseline, and the baseline
is restored immediately. Motor-on RF observation is operator-initiated and must use
the independent receiver.
