"""Read the fixed flight-limit parameters on the aircraft USB DUML port.

This wrapper reuses rc2_readonly_params's hard-coded read-only allow-list and
changes only the USB transport.  No parameter-write command is available.
"""

import rc2_readonly_params as probe


probe.PID = 0x0020
probe.INTERFACE = 4
probe.EP_OUT = 0x04
probe.EP_IN = 0x85
probe.SOURCE_APP = 0x0A


if __name__ == "__main__":
    probe.main()
