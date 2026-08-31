#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int allocations, fail_at, live_allocations;
static unsigned checks, calls;
#define CHECK(x) do { ++checks; if (!(x)) { fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#x); exit(1); } } while (0)
static void *test_malloc(size_t size) {
    if (++allocations == fail_at) return NULL;
    void *p = malloc(size); if (p) ++live_allocations; return p;
}
static void *test_calloc(size_t n,size_t size) {
    if (++allocations == fail_at) return NULL;
    void *p = calloc(n,size); if (p) ++live_allocations; return p;
}
static void test_free(void *p) { if (p) { CHECK(live_allocations > 0); --live_allocations; } free(p); }
#define malloc test_malloc
#define calloc test_calloc
#define free test_free
#include "global_payload_extract.c"
#undef malloc
#undef calloc
#undef free

static const char input[] = "{\"TEST-unknown\":\"TEST-PRIVATE-OUTER\",\"country_and_device_type\":\"[{\\\"country_code\\\":\\\"DEFAULT\\\",\\\"data\\\":\\\"AA\\\",\\\"block_device\\\":[139]},{\\\"country_code\\\":\\\"TEST-AREA\\\",\\\"data\\\":\\\"BB\\\",\\\"block_device\\\":[],\\\"TEST-ignore\\\":\\\"TEST-PRIVATE-INNER\\\"}]\"}";

static void run(const char *data,size_t length,int64_t product,int expected) {
    char *out = (char *)1;size_t out_length = 99;struct global_payload_summary summary;
    CHECK((int)global_payload_extract(data,length,product,&out,&out_length,&summary)==expected);++calls;
    if (expected) { CHECK(out==NULL&&out_length==0&&summary.json_length==0&&live_allocations==0);return; }
    CHECK(out&&out_length==strlen(out)&&out_length<=GLOBAL_PAYLOAD_JSON_LIMIT);
    CHECK(summary.policy_rc==0&&summary.row_count==2&&summary.nonempty_row_count==2&&summary.distinct_nonempty_count==2);
    CHECK(summary.default_row_count==1&&summary.first_default_present==1&&summary.first_default_nonempty==1&&summary.first_default_row_index==0);
    CHECK(summary.blocked_row_count==1&&summary.duplicate_country_row_count==0&&summary.invalid_hex_row_index==-1);
    CHECK(strstr(out,"\"schema\":\"finduas-rid-policy-set/v1\"")&&strstr(out,"\"country_code\":\"TEST-AREA\""));
    CHECK(strstr(out,"\"country_code\":\"DEFAULT\",\"data_hex\":\"AA\",\"blocked_for_product\":true")!=NULL);
    CHECK(!strstr(out,"country_and_device_type")&&!strstr(out,"TEST-PRIVATE")&&!strstr(out,"TEST-ignore")&&!strstr(out,"actual_area")&&!strstr(out,"matched"));
    CHECK(summary.json_length==(int)out_length&&live_allocations==1);test_free(out);CHECK(live_allocations==0);
}

int main(void) {
    for(int i=0;i<20;++i)run(input,sizeof(input)-1,139,GLOBAL_PAYLOAD_OK);
    for(size_t i=0;i<sizeof(input)-1;++i)run(input,i,139,GLOBAL_PAYLOAD_POLICY_MALFORMED);
    run(NULL,0,139,GLOBAL_PAYLOAD_POLICY_UNAVAILABLE);
    run(NULL,1,139,GLOBAL_PAYLOAD_ARGUMENT);
    run(input,65537,139,GLOBAL_PAYLOAD_POLICY_LIMIT);
    run(input,sizeof(input)-1,-1,GLOBAL_PAYLOAD_PRODUCT_UNOBSERVED);
    run(input,sizeof(input)-1,65536,GLOBAL_PAYLOAD_ARGUMENT);
    for(int fail=1;fail<=4;++fail) { allocations=0;fail_at=fail;run(input,sizeof(input)-1,139,GLOBAL_PAYLOAD_ALLOCATION); }
    fail_at=0;
    char *out=(char *)1;size_t length=99;struct global_payload_summary summary;
    CHECK(global_payload_extract(input,sizeof(input)-1,139,&out,NULL,&summary)==GLOBAL_PAYLOAD_ARGUMENT&&out==NULL);
    CHECK(global_payload_extract(input,sizeof(input)-1,139,NULL,&length,&summary)==GLOBAL_PAYLOAD_ARGUMENT&&length==0);
    out=(char *)1;length=99;
    CHECK(global_payload_extract(input,sizeof(input)-1,139,&out,&length,NULL)==GLOBAL_PAYLOAD_ARGUMENT&&out==NULL&&length==0);
    CHECK(live_allocations==0);
    printf("global payload extractor: %u calls, %u checks passed\n",calls,checks);return 0;
}
