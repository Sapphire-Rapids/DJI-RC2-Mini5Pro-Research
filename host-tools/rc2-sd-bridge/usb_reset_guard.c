#include <libusb.h>
#include <stdio.h>

/* Static libmtp calls this definition instead of the libusb device reset.
 * On macOS the real function can re-enumerate the entire composite device. */
int LIBUSB_CALL libusb_reset_device(libusb_device_handle *device)
{
    (void)device;
    fputs("USB_RESET_BLOCKED_BY_HOST_POLICY\n", stderr);
    return LIBUSB_ERROR_NOT_SUPPORTED;
}
