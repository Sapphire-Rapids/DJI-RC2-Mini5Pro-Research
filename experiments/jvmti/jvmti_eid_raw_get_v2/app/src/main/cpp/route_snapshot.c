#include "route_snapshot.h"

#include <string.h>

/*
 * Deliberately permanent in this offline carrier.  There is no build flag or
 * caller-supplied option that can turn guessed route values into a live route.
 */
enum RouteStatus route_snapshot_resolve(RouteSnapshot *snapshot) {
    if (snapshot != NULL) {
        memset(snapshot, 0, sizeof(*snapshot));
    }
    return ROUTE_STATUS_UNRESOLVED;
}

bool route_snapshot_epoch_unchanged(const RouteSnapshot *snapshot) {
    (void)snapshot;
    return false;
}
