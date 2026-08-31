#include "payload_extract.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x); exit(1); } } while(0)
static const char policy[]="{\"country_and_device_type\":\"[{\\\"country_code\\\":\\\"DEFAULT\\\",\\\"data\\\":\\\"CC\\\",\\\"block_device\\\":[]},{\\\"country_code\\\":\\\"TEST-AREA\\\",\\\"data\\\":\\\"AA\\\",\\\"block_device\\\":[]}]\"}";
static size_t checks;
static void check_call(const char *input,size_t size,int64_t product,const char *cache,size_t cache_size,int rt,int ri,int expected) {
    char *json=(char*)1;size_t length=999;struct cloud_payload_summary summary;
    int rc=cloud_payload_extract(input,size,product,cache,cache_size,rt,ri,&json,&length,&summary);
    CHECK(rc==expected);++checks;
    if(rc){CHECK(json==NULL&&length==0);return;}
    CHECK(json!=NULL&&length==strlen(json)&&length<=32768);
    CHECK(strstr(json,"\"matched_hex\":\"AA\"")!=NULL);
    CHECK(strstr(json,"\"default_hex\":\"CC\"")!=NULL);
    CHECK(strstr(json,"TEST-AREA")==NULL&&strstr(json,"country_and_device_type")==NULL);
    CHECK(summary.matching_row_count==1&&summary.default_present==1);
    CHECK(summary.matched_hex_valid==1&&summary.matched_decoded_length==1);
    free(json);
}
int main(void) {
    for(int i=0;i<100;++i)check_call(policy,sizeof(policy)-1,139,"AA",2,18,4,0);
    check_call(policy,sizeof(policy)-1,139,"AA",2,3,0,CLOUD_PAYLOAD_RECEIVER_MISMATCH);
    check_call(policy,sizeof(policy)-1,139,"BB",2,18,4,CLOUD_PAYLOAD_NO_ELIGIBLE_MATCH);
    check_call(policy,sizeof(policy)-1,-1,"AA",2,18,4,CLOUD_PAYLOAD_PRODUCT_UNOBSERVED);
    check_call(policy,sizeof(policy)-1,139,NULL,0,18,4,CLOUD_PAYLOAD_CACHE_MISSING);
    check_call(NULL,0,139,"AA",2,18,4,CLOUD_PAYLOAD_POLICY_UNAVAILABLE);
    for(size_t n=0;n<sizeof(policy)-1;++n)check_call(policy,n,139,"AA",2,18,4,CLOUD_PAYLOAD_POLICY_MALFORMED);
    char *json=(char*)1;size_t length=4;struct cloud_payload_summary summary;
    CHECK(cloud_payload_extract(policy,sizeof(policy)-1,139,"AA",2,18,4,&json,NULL,&summary)==CLOUD_PAYLOAD_ARGUMENT&&json==NULL);
    CHECK(cloud_payload_extract(policy,sizeof(policy)-1,139,"AA",2,18,4,NULL,&length,&summary)==CLOUD_PAYLOAD_ARGUMENT&&length==0);
    printf("Private payload extractor: %zu calls + argument guards passed\n",checks);
    return 0;
}
