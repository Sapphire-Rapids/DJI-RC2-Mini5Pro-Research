#ifndef FINDUAS_EID_RAW_GET_V2_ROUTE_SNAPSHOT_H
#define FINDUAS_EID_RAW_GET_V2_ROUTE_SNAPSHOT_H

#include <jni.h>
#include <stdbool.h>
#include <stdint.h>

enum RouteStatus {
    ROUTE_STATUS_RESOLVED = 0,
    ROUTE_STATUS_UNRESOLVED = 1,
};

typedef struct RouteSnapshot {
    jint product_id;
    jint device_id;
    jint sender_index;
    jint receiver_type;
    jint receiver_index;
    int64_t connection_epoch;
    bool product_139_identity_proven;
    bool france_eid_capability_proven;
    bool host_route_proven;
} RouteSnapshot;

enum RouteStatus route_snapshot_resolve(RouteSnapshot *snapshot);
bool route_snapshot_epoch_unchanged(const RouteSnapshot *snapshot);

#endif
