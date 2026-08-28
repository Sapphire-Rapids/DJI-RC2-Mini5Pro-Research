"""Run the fixed account-sync boolean queries on the aircraft's USB DUML port.

This wrapper reuses rc2_readonly_uid_status's allow-listed Detection reads and
changes only the USB transport.  It cannot request or print UUID values.
"""

import rc2_readonly_uid_status as probe


probe.PID = 0x0020
probe.INTERFACE = 4
probe.EP_OUT = 0x04
probe.EP_IN = 0x85
probe.SOURCE_APP = 0x0A


if __name__ == "__main__":
    probe.main()
