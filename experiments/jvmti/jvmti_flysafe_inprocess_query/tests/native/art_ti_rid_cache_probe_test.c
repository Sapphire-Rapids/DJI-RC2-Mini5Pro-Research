#define FINDUAS_RID_HOST_TEST 1
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <sys/types.h>
#include "../../src/native/art_ti_rid_cache_probe.c"

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %s:%d %s\n",test_name,__LINE__,#x); exit(1); } } while (0)
static const char *test_name;
static char logs[3][2048];
static int log_count, live_allocs, calls, disposals, opened, closed;
static int fault, pending, owner_changes;
static unsigned char payload[128];
static jsize payload_size;
static JNIEnv jni_env;
static jvmtiEnv ti_env;
static const char *class_sigs[] = {
    "Luav/jni/JNIKeyValue;", "Luav/sdk/keyvalue/key/UAVFlightControllerKey;",
    "Luav/sdk/keyvalue/key/UAVKeyInfo;", "Luav/sdk/keyvalue/key/UAVKeyInfoBase;"
};
static void *allocate(size_t n) { void *p=calloc(1,n); CHECK(p); ++live_allocs; return p; }
static char *copy(const char *s) { char *p=allocate(strlen(s)+1); strcpy(p,s); return p; }
int __android_log_print(int priority,const char *tag,const char *fmt,...) {
    CHECK(priority==ANDROID_LOG_INFO && strcmp(tag,RID_TAG)==0 && log_count<3);
    va_list ap;va_start(ap,fmt);vsnprintf(logs[log_count++],sizeof(logs[0]),fmt,ap);va_end(ap);return 0;
}
static jboolean JNICALL exception_check(JNIEnv *env) { (void)env;return pending?JNI_TRUE:JNI_FALSE; }
static void JNICALL exception_clear(JNIEnv *env) { (void)env;pending=0; }
static void JNICALL del_ref(JNIEnv *env,jobject obj) { (void)env;(void)obj; }
static jboolean JNICALL same(JNIEnv *env,jobject a,jobject b) { (void)env;return a==b?JNI_TRUE:JNI_FALSE; }
static jvmtiError JNICALL deallocate(jvmtiEnv *env,unsigned char *p) { (void)env;CHECK(live_allocs>0);--live_allocs;free(p);return 0; }
static jvmtiError JNICALL dispose(jvmtiEnv *env) { (void)env;CHECK(live_allocs==0);CHECK(++disposals==1);return fault==20?JVMTI_ERROR_INTERNAL:0; }
static jint JNICALL get_env(JavaVM *vm,void **out,jint version) {
    (void)vm;
    if (version==JNI_VERSION_1_6) { *out=fault==1?NULL:&jni_env;return fault==1?JNI_EDETACHED:JNI_OK; }
    CHECK(version==ART_TI_VERSION);*out=fault==2?NULL:&ti_env;return fault==2?JNI_EVERSION:JNI_OK;
}
static jvmtiError JNICALL classes(jvmtiEnv *env,jint *count,jclass **out) {
    (void)env;if(fault==3)return JVMTI_ERROR_INTERNAL;
    *count=fault==4?5:4;*out=allocate(sizeof(jclass)*(size_t)*count);
    for(int i=0;i<*count;++i)(*out)[i]=(jclass)(uintptr_t)(i%4+1);return 0;
}
static jvmtiError JNICALL signature(jvmtiEnv *env,jclass cls,char **sig,char **generic) {
    (void)env;(void)generic;*sig=copy(class_sigs[(uintptr_t)cls-1]);return 0;
}
static jvmtiError JNICALL status(jvmtiEnv *env,jclass cls,jint *out) {
    (void)env;(void)cls;*out=fault==5?JVMTI_CLASS_STATUS_PREPARED:JVMTI_CLASS_STATUS_INITIALIZED;return 0;
}
static jvmtiError JNICALL loader(jvmtiEnv *env,jclass cls,jobject *out) {
    (void)env;*out=(jobject)(uintptr_t)(fault==6?500+(uintptr_t)cls:500);return 0;
}
static jvmtiError JNICALL fields(jvmtiEnv *env,jclass cls,jint *count,jfieldID **out) {
    (void)env;CHECK(cls==(jclass)2||cls==(jclass)4);*count=cls==(jclass)2?1:9;*out=allocate((size_t)*count*sizeof(jfieldID));
    for(int i=0;i<*count;++i)(*out)[i]=(jfieldID)(uintptr_t)(cls==(jclass)2?100:i+1);return 0;
}
static jvmtiError JNICALL field_name(jvmtiEnv *env,jclass cls,jfieldID id,char **name,char **sig,char **generic) {
    (void)env;(void)cls;(void)generic;uintptr_t x=(uintptr_t)id;
    if(x==100){*name=copy(fault==7?"wrong":"o8");*sig=copy("Luav/sdk/keyvalue/key/UAVKeyInfo;");return 0;}
    const char *names[]={"a","b","i","j","d","e","f","g","h"};
    CHECK(x>=1&&x<=9);*name=copy(names[x-1]);*sig=copy(x<=2?"I":x<=4?"Ljava/lang/String;":"Z");return 0;
}
static jvmtiError JNICALL field_mods(jvmtiEnv *env,jclass cls,jfieldID id,jint *mods) {
    (void)env;(void)cls;*mods=id==(jfieldID)100?ACC_STATIC:0;return 0;
}
static jvmtiError JNICALL methods(jvmtiEnv *env,jclass cls,jint *count,jmethodID **out) {
    (void)env;CHECK(cls==(jclass)1);*count=1;*out=allocate(sizeof(jmethodID));(*out)[0]=(jmethodID)200;return 0;
}
static jvmtiError JNICALL method_name(jvmtiEnv *env,jmethodID id,char **name,char **sig,char **generic) {
    (void)env;(void)generic;CHECK(id==(jmethodID)200);*name=copy("native_get_sync");*sig=copy("(IIIIILjava/lang/String;)[B");return 0;
}
static jvmtiError JNICALL method_mods(jvmtiEnv *env,jmethodID id,jint *mods) {
    (void)env;(void)id;*mods=fault==8?ACC_STATIC:ACC_STATIC|ACC_NATIVE;return 0;
}
static jobject JNICALL static_object(JNIEnv *env,jclass cls,jfieldID id) {
    (void)env;CHECK(cls==(jclass)2&&id==(jfieldID)100);return fault==9?NULL:(jobject)600;
}
static jclass JNICALL object_class(JNIEnv *env,jobject obj) { (void)env;CHECK(obj==(jobject)600);return (jclass)(uintptr_t)(fault==10?4:3); }
static jint JNICALL int_field(JNIEnv *env,jobject obj,jfieldID id) {
    (void)env;CHECK(obj==(jobject)600);CHECK(id==(jfieldID)1||id==(jfieldID)2);return id==(jfieldID)1?(fault==11?3:4):65534;
}
static jobject JNICALL object_field(JNIEnv *env,jobject obj,jfieldID id) {
    (void)env;CHECK(obj==(jobject)600);CHECK(id==(jfieldID)3||id==(jfieldID)4);return (jobject)(uintptr_t)((uintptr_t)id+598);
}
static jboolean JNICALL bool_field(JNIEnv *env,jobject obj,jfieldID id) {
    (void)env;CHECK(obj==(jobject)600);return (id==(jfieldID)5||id==(jfieldID)7||(fault==12&&id==(jfieldID)6))?JNI_TRUE:JNI_FALSE;
}
static jsize JNICALL string_length(JNIEnv *env,jstring str) { (void)env;CHECK(str==(jstring)601||str==(jstring)602);return 20; }
static void JNICALL string_region(JNIEnv *env,jstring str,jsize start,jsize len,jchar *out) {
    (void)env;CHECK(str==(jstring)601||str==(jstring)602);CHECK(start==0&&len==20);
    const char *v="RidWorkingStatusPush";for(int i=0;i<len;++i)out[i]=(jchar)v[i];if(fault==13)out[0]='X';
}
static jobject JNICALL invoke(JNIEnv *env,jclass cls,jmethodID method,const jvalue *args) {
    (void)env;CHECK(cls==(jclass)1&&method==(jmethodID)200);CHECK(++calls==1);
    CHECK(args[0].i==0&&args[1].i==4&&args[2].i==0&&args[3].i==65534&&args[4].i==65534&&args[5].l==(jobject)602);
    if(fault==15){pending=1;return NULL;}return fault==16?NULL:(jobject)603;
}
static jsize JNICALL array_length(JNIEnv *env,jarray a) { (void)env;CHECK(a==(jarray)603);return payload_size; }
static void JNICALL byte_region(JNIEnv *env,jbyteArray a,jsize start,jsize len,jbyte *out) {
    (void)env;CHECK(a==(jbyteArray)603);CHECK(len==8&&(start==0||start==payload_size-8));CHECK(start>=0&&start+len<=payload_size);
    memcpy(out,payload+start,(size_t)len);if(fault==19)pending=1;
}
static int native_owner_open(struct owner_guard *guard) { guard->handle=(void*)1;++opened;return fault!=14; }
static int native_owner_same(const struct owner_guard *guard) { CHECK(guard->handle);return !owner_changes; }
static void native_owner_close(struct owner_guard *guard) { if(guard->handle){++closed;guard->handle=NULL;} }
static const struct JNINativeInterface_ jni_functions={
    .ExceptionCheck=exception_check,.ExceptionClear=exception_clear,.DeleteLocalRef=del_ref,.IsSameObject=same,
    .GetStaticObjectField=static_object,.GetObjectClass=object_class,.GetIntField=int_field,.GetObjectField=object_field,
    .GetBooleanField=bool_field,.GetStringLength=string_length,.GetStringRegion=string_region,
    .CallStaticObjectMethodA=invoke,.GetArrayLength=array_length,.GetByteArrayRegion=byte_region
};
static const struct jvmtiInterface_1_ ti_functions={
    .Deallocate=deallocate,.DisposeEnvironment=dispose,.GetLoadedClasses=classes,.GetClassSignature=signature,
    .GetClassStatus=status,.GetClassLoader=loader,.GetClassFields=fields,.GetFieldName=field_name,.GetFieldModifiers=field_mods,
    .GetClassMethods=methods,.GetMethodName=method_name,.GetMethodModifiers=method_mods
};
static const struct JNIInvokeInterface_ vm_functions={.GetEnv=get_env};
static JavaVM vm=&vm_functions;
static void reset(int f) {
    atomic_flag_clear(&entered);memset(logs,0,sizeof(logs));log_count=live_allocs=calls=disposals=opened=closed=pending=owner_changes=0;
    fault=f;jni_env=&jni_functions;ti_env=&ti_functions;memset(payload,0,sizeof(payload));payload_size=18;
    payload[0]=1;payload[1]=1;payload[3]=1;payload[4]=2;payload[8]='X';payload[9]='X';payload[14]=7;
}
static void run_case(int f,const char *name,int expected_stage,int expected_query) {
    test_name=name;reset(f);char sid[]="0123456789abcdef";
    if(f==17)payload_size=15;if(f==18)payload[0]=2;if(f==21)owner_changes=1;
    if(f==22)payload[4]=3;if(f==23){payload_size=16;payload[4]=0;payload[12]=0xff;payload[13]=0xff;payload[14]=0xff;payload[15]=0xff;}
    CHECK(Agent_OnAttach(&vm,sid,NULL)==JNI_OK);CHECK(log_count==2&&live_allocs==0&&pending==0);
    CHECK(calls==expected_query);CHECK(opened==closed);CHECK(disposals==(f==1||f==2?0:1));
    char target[40];snprintf(target,sizeof(target)," stage=%d ",expected_stage);CHECK(strstr(logs[1],target));
    CHECK(strstr(logs[1],expected_stage?" ready=0 ":" ready=1 "));
    if(expected_stage||f==16){CHECK(strstr(logs[1],"value_present=0 rid_support=-1 rid_normal=-1 eid_support=-1 eid_normal=-1 fail_reason=0"));}
    else {CHECK(strstr(logs[1],"value_present=1 rid_support=1 rid_normal=1 eid_support=1 eid_normal=0"));}
    CHECK(!strstr(logs[1],"area")&&!strstr(logs[1],"XX"));
    CHECK(Agent_OnAttach(&vm,sid,NULL)==JNI_OK);CHECK(log_count==2&&calls==expected_query);
    if(f==23)CHECK(strstr(logs[1],"fail_reason=4294967295"));
}
int main(void) {
    run_case(0,"cache value",0,1);run_case(1,"JNI unavailable",1,0);run_case(2,"ART TI unavailable",2,0);
    run_case(3,"class enumeration failed",3,0);run_case(4,"duplicate class",4,0);run_case(5,"not initialized",4,0);
    run_case(6,"loader conflict",4,0);run_case(7,"field missing",5,0);run_case(8,"not native method",5,0);
    run_case(9,"null key",6,0);run_case(10,"wrong key class",6,0);run_case(11,"wrong component",6,0);
    run_case(12,"write-capable key",6,0);run_case(13,"wrong key name",6,0);run_case(14,"owner unavailable",7,0);
    run_case(15,"native exception",8,1);run_case(16,"empty cache",0,1);run_case(17,"short bytes",9,1);
    run_case(18,"invalid Boolean",9,1);run_case(19,"array read exception",9,1);run_case(20,"dispose failure",13,1);
    run_case(21,"owner changed",10,1);run_case(22,"length mismatch",9,1);run_case(23,"unsigned reason",0,1);
    test_name="invalid options";reset(0);char invalid[]="bad";CHECK(Agent_OnAttach(&vm,invalid,NULL)==JNI_ERR);CHECK(log_count==0&&calls==0);
    puts("RID cache probe: 25 host cases passed");return 0;
}
