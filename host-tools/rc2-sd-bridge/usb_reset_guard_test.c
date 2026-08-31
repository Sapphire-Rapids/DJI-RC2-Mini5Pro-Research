#include <libusb.h>
#include <stdio.h>

/* Build without libusb: any call through to the real library fails to link. */
int main(void)
{
    if (libusb_reset_device(NULL) != LIBUSB_ERROR_NOT_SUPPORTED) {
        fputs("RESET_GUARD_SELF_TEST_FAILED\n", stderr);
        return 1;
    }
    puts("RESET_GUARD_SELF_TEST_OK usb_initialized=false");
    return 0;
}
