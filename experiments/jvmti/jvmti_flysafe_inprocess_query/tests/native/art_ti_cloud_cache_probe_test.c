#define FINDUAS_CLOUD_HOST_TEST 1
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <sys/types.h>
#include "../../src/native/art_ti_cloud_cache_probe.c"

static const char *test_name;
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %s:%d %s\n",test_name,__LINE__,#x); exit(1); } } while (0)
static char logs[3][2048];
static int log_count, live_allocs, cloud_calls, product_calls, decode_calls, disposals;
static int opened, closed, locked, pending, fault, same_calls;
static unsigned char cloud[128], product[4];
static jsize cloud_size, product_size;
static jchar policy[2048]; static jsize policy_units;
static JNIEnv jni_env; static jvmtiEnv ti_env;
static const char *class_sigs[] = {
    "Luav/jni/JNIKeyValue;", "Luav/sdk/keyvalue/key/UAVProductKey;",
    "Luav/sdk/keyvalue/key/UAVKeyInfo;", "Luav/sdk/keyvalue/key/UAVKeyInfoBase;",
    "Luav/component/CloudControl/CloudControlNamespaces;", "Lcom/tencent/mmkv/MMKV;"
};
static void *allocate(size_t n) { void *p=calloc(1,n); CHECK(p); ++live_allocs; return p; }
static char *copy(const char *s) { char *p=allocate(strlen(s)+1); strcpy(p,s); return p; }
int __android_log_print(int priority,const char *tag,const char *fmt,...) {
    CHECK(priority==ANDROID_LOG_INFO && strcmp(tag,CLOUD_TAG)==0 && log_count<3);
    va_list ap;va_start(ap,fmt);vsnprintf(logs[log_count++],sizeof(logs[0]),fmt,ap);va_end(ap);return 0;
}
static jboolean JNICALL exception_check(JNIEnv *env) { (void)env;return pending?JNI_TRUE:JNI_FALSE; }
static void JNICALL exception_clear(JNIEnv *env) { (void)env;pending=0; }
static void JNICALL del_ref(JNIEnv *env,jobject obj) { (void)env;(void)obj; }
static jboolean JNICALL same(JNIEnv *env,jobject a,jobject b) { (void)env;return a==b?JNI_TRUE:JNI_FALSE; }
static jvmtiError JNICALL deallocate(jvmtiEnv *env,unsigned char *p) { (void)env;CHECK(live_allocs>0);--live_allocs;free(p);return 0; }
static jvmtiError JNICALL dispose(jvmtiEnv *env) { (void)env;CHECK(live_allocs==0);CHECK(++disposals==1);return fault==20?JVMTI_ERROR_INTERNAL:0; }
static jint JNICALL get_env(JavaVM *vm,void **out,jint version) {
    (void)vm;if(version==JNI_VERSION_1_6){*out=fault==1?NULL:&jni_env;return fault==1?JNI_EDETACHED:JNI_OK;}
    CHECK(version==ART_TI_VERSION);*out=fault==2?NULL:&ti_env;return fault==2?JNI_EVERSION:JNI_OK;
}
static jvmtiError JNICALL classes(jvmtiEnv *env,jint *count,jclass **out) {
    (void)env;if(fault==3)return JVMTI_ERROR_INTERNAL;*count=fault==4?7:6;*out=allocate(sizeof(jclass)*(size_t)*count);
    for(int i=0;i<*count;++i)(*out)[i]=(jclass)(uintptr_t)(i%6+1);return 0;
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
    (void)env;uintptr_t n=(uintptr_t)cls;CHECK(n==2||n==4||n==5||n==6);*count=n==4?9:2;
    *out=allocate((size_t)*count*sizeof(jfieldID));
    for(int i=0;i<*count;++i)(*out)[i]=(jfieldID)(uintptr_t)(n==2?100+i:n==4?i+1:n==5?110+i:120+i);return 0;
}
static jvmtiError JNICALL field_name(jvmtiEnv *env,jclass cls,jfieldID id,char **name,char **sig,char **generic) {
    (void)env;(void)cls;(void)generic;uintptr_t x=(uintptr_t)id;
    if(x==100||x==101){*name=copy(fault==7?"wrong":x==100?"U":"o");*sig=copy("Luav/sdk/keyvalue/key/UAVKeyInfo;");}
    else if(x==110){*name=copy("r");*sig=copy("Luav/component/CloudControl/CloudControlNamespaces;");}
    else if(x==111){*name=copy("namespace");*sig=copy("Ljava/lang/String;");}
    else if(x==120){*name=copy("rootDir");*sig=copy("Ljava/lang/String;");}
    else if(x==121){*name=copy("nativeHandle");*sig=copy("J");}
    else {const char *names[]={"a","b","i","j","d","e","f","g","h"};CHECK(x>=1&&x<=9);*name=copy(names[x-1]);*sig=copy(x<=2?"I":x<=4?"Ljava/lang/String;":"Z");}
    return 0;
}
static jvmtiError JNICALL field_mods(jvmtiEnv *env,jclass cls,jfieldID id,jint *mods) {
    (void)env;(void)cls;uintptr_t n=(uintptr_t)id;*mods=(n==100||n==101||n==110||n==120)?ACC_STATIC:0;return 0;
}
static jvmtiError JNICALL methods(jvmtiEnv *env,jclass cls,jint *count,jmethodID **out) {
    (void)env;CHECK(cls==(jclass)1||cls==(jclass)6);*count=cls==(jclass)1?1:3;*out=allocate((size_t)*count*sizeof(jmethodID));
    for(int i=0;i<*count;++i)(*out)[i]=(jmethodID)(uintptr_t)(cls==(jclass)1?200:201+i);return 0;
}
static jvmtiError JNICALL method_name(jvmtiEnv *env,jmethodID id,char **name,char **sig,char **generic) {
    (void)env;(void)generic;uintptr_t x=(uintptr_t)id;CHECK(x>=200&&x<=203);
    const char *names[]={"native_get_sync","defaultMMKV","getValueActualSize","decodeString"};
    const char *sigs[]={"(IIIIILjava/lang/String;)[B","()Lcom/tencent/mmkv/MMKV;","(Ljava/lang/String;)I","(Ljava/lang/String;)Ljava/lang/String;"};
    *name=copy(names[x-200]);*sig=copy(sigs[x-200]);return 0;
}
static jvmtiError JNICALL method_mods(jvmtiEnv *env,jmethodID id,jint *mods) {
    (void)env;*mods=id==(jmethodID)200?(fault==8?ACC_STATIC:ACC_STATIC|ACC_NATIVE):id==(jmethodID)201?ACC_STATIC:0;return 0;
}
static jobject JNICALL static_object(JNIEnv *env,jclass cls,jfieldID id) {
    (void)env;
    if(cls==(jclass)2){CHECK(id==(jfieldID)100||id==(jfieldID)101);return fault==9?NULL:id==(jfieldID)100?(jobject)600:(jobject)610;}
    if(cls==(jclass)5){CHECK(id==(jfieldID)110);return fault==24?NULL:(jobject)700;}
    CHECK(cls==(jclass)6&&id==(jfieldID)120);return fault==25?NULL:(jobject)702;
}
static jclass JNICALL object_class(JNIEnv *env,jobject obj) { (void)env;CHECK(obj==(jobject)600||obj==(jobject)610);return (jclass)(uintptr_t)(fault==10?4:3); }
static jint JNICALL int_field(JNIEnv *env,jobject obj,jfieldID id) { (void)env;CHECK(obj==(jobject)600||obj==(jobject)610);CHECK(id==(jfieldID)1||id==(jfieldID)2);return fault==11?4:65534; }
static jlong JNICALL long_field(JNIEnv *env,jobject obj,jfieldID id) { (void)env;CHECK(locked&&obj==(jobject)705&&id==(jfieldID)121);return fault==32?78:77; }
static jobject JNICALL object_field(JNIEnv *env,jobject obj,jfieldID id) {
    (void)env;if(obj==(jobject)700){CHECK(id==(jfieldID)111);return (jobject)701;}
    CHECK((obj==(jobject)600||obj==(jobject)610)&&(id==(jfieldID)3||id==(jfieldID)4));return obj==(jobject)600?(jobject)1000:(jobject)1001;
}
static jboolean JNICALL bool_field(JNIEnv *env,jobject obj,jfieldID id) {
    (void)env;CHECK(obj==(jobject)600||obj==(jobject)610);int x=(int)(uintptr_t)id;
    return ((obj==(jobject)600&&x==6)||(obj==(jobject)610&&(x==5||x==7))||(fault==12&&x==8))?JNI_TRUE:JNI_FALSE;
}
static const char *string_value(jstring str) {
    if(str==(jstring)1000)return fault==13?"WrongControlDat":"CloudControlData";
    if(str==(jstring)1001)return "ProductType";
    if(str==(jstring)701)return "TEST_RID_NAMESPACE";
    if(str==(jstring)702)return "TEST_ROOT";
    CHECK(0);return "";
}
static jsize JNICALL string_length(JNIEnv *env,jstring str) { (void)env;return str==(jstring)704?policy_units:(jsize)strlen(string_value(str)); }
static void JNICALL string_region(JNIEnv *env,jstring str,jsize start,jsize len,jchar *out) {
    (void)env;CHECK(!locked || str!=(jstring)704);
    if(str==(jstring)704){CHECK(start>=0&&len>=0&&start+len<=policy_units);memcpy(out,policy+start,(size_t)len*sizeof(jchar));}
    else {const char *s=string_value(str);CHECK(start>=0&&len>=0&&(size_t)(start+len)<=strlen(s));for(int i=0;i<len;++i)out[i]=(unsigned char)s[start+i];}
}
static jstring JNICALL new_string(JNIEnv *env,const jchar *s,jsize size) {
    (void)env;const char *expected="cloud_control_mmkv_prefix_TEST_RID_NAMESPACE";CHECK((size_t)size==strlen(expected));for(int i=0;i<size;++i)CHECK(s[i]==(unsigned char)expected[i]);return (jstring)703;
}
static jobject JNICALL invoke_static(JNIEnv *env,jclass cls,jmethodID id,const jvalue *args) {
    (void)env;if(id==(jmethodID)201){CHECK(locked&&cls==(jclass)6&&args==NULL);return (jobject)705;}
    CHECK(!locked&&cls==(jclass)1&&id==(jmethodID)200);CHECK(args[0].i==0&&args[1].i==65534&&args[2].i==0&&args[3].i==65534&&args[4].i==65534);
    if(args[5].l==(jobject)1000){CHECK(++cloud_calls==1);if(fault==15){pending=1;return NULL;}return fault==16?NULL:(jobject)706;}
    CHECK(args[5].l==(jobject)1001);CHECK(++product_calls==1);return fault==23?NULL:(jobject)707;
}
static jint JNICALL invoke_int(JNIEnv *env,jobject obj,jmethodID id,const jvalue *args) { (void)env;CHECK(locked&&obj==(jobject)705&&id==(jmethodID)202&&args[0].l==(jobject)703);return fault==33?65537:policy_units; }
static jobject JNICALL invoke_object(JNIEnv *env,jobject obj,jmethodID id,const jvalue *args) {
    (void)env;CHECK(locked&&obj==(jobject)705&&id==(jmethodID)203&&args[0].l==(jobject)703);CHECK(++decode_calls==1);if(fault==34)pending=1;return fault==35?NULL:(jobject)704;
}
static jsize JNICALL array_length(JNIEnv *env,jarray a) { (void)env;CHECK(a==(jarray)706||a==(jarray)707);return a==(jarray)706?cloud_size:product_size; }
static void JNICALL byte_region(JNIEnv *env,jbyteArray a,jsize start,jsize len,jbyte *out) {
    (void)env;CHECK(!locked);CHECK(a==(jbyteArray)706||a==(jbyteArray)707);jsize n=a==(jbyteArray)706?cloud_size:product_size;CHECK(start>=0&&len>=0&&start+len<=n);memcpy(out,(a==(jbyteArray)706?cloud:product)+start,(size_t)len);if(fault==19)pending=1;
}
static int native_owner_open(struct owner_guard *guard) { guard->handle=(void*)2;return fault!=14; }
static int native_owner_same(const struct owner_guard *guard) { CHECK(guard->handle&&!locked);++same_calls;return fault!=21; }
static void native_owner_close(struct owner_guard *guard) { guard->handle=NULL; }
static int mmkv_open(struct mmkv_guard *guard) {
    CHECK(!locked);++opened;guard->handle=(void*)1;guard->instance=77;locked=1;
    switch(fault){case 26:return 1;case 27:return 3;case 28:return 5;case 29:return 6;case 30:return 7;case 31:return 8;case 39:return 10;default:return 0;}
}
static void mmkv_release(struct mmkv_guard *guard) { if(guard->handle){CHECK(locked);++closed;locked=0;guard->handle=NULL;} }
static const struct JNINativeInterface_ jni_functions={
    .ExceptionCheck=exception_check,.ExceptionClear=exception_clear,.DeleteLocalRef=del_ref,.IsSameObject=same,
    .GetStaticObjectField=static_object,.GetObjectClass=object_class,.GetIntField=int_field,.GetLongField=long_field,.GetObjectField=object_field,
    .GetBooleanField=bool_field,.GetStringLength=string_length,.GetStringRegion=string_region,.NewString=new_string,
    .CallStaticObjectMethodA=invoke_static,.CallIntMethodA=invoke_int,.CallObjectMethodA=invoke_object,.GetArrayLength=array_length,.GetByteArrayRegion=byte_region
};
static const struct jvmtiInterface_1_ ti_functions={
    .Deallocate=deallocate,.DisposeEnvironment=dispose,.GetLoadedClasses=classes,.GetClassSignature=signature,
    .GetClassStatus=status,.GetClassLoader=loader,.GetClassFields=fields,.GetFieldName=field_name,.GetFieldModifiers=field_mods,
    .GetClassMethods=methods,.GetMethodName=method_name,.GetMethodModifiers=method_mods
};
static const struct JNIInvokeInterface_ vm_functions={.GetEnv=get_env};static JavaVM vm=&vm_functions;
static void reset(int f) {
    atomic_flag_clear(&entered);memset(logs,0,sizeof(logs));log_count=live_allocs=cloud_calls=product_calls=decode_calls=disposals=opened=closed=locked=pending=same_calls=0;fault=f;jni_env=&jni_functions;ti_env=&ti_functions;
    memset(cloud,0,sizeof(cloud));cloud_size=14;cloud[0]=18;cloud[4]=4;cloud[8]=2;cloud[12]='A';cloud[13]='A';product[0]=139;product[1]=product[2]=product[3]=0;product_size=4;
    const char *json="{\"country_and_device_type\":\"[{\\\"country_code\\\":\\\"DEFAULT\\\",\\\"data\\\":\\\"AA\\\",\\\"block_device\\\":[]},{\\\"country_code\\\":\\\"TEST-CN\\\",\\\"data\\\":\\\"BB\\\",\\\"block_device\\\":[139]}]\"}";
    policy_units=(jsize)strlen(json);for(int i=0;i<policy_units;++i)policy[i]=(unsigned char)json[i];
}
static void run_case(int f,const char *name,int expected_stage,int c,int p,int m) {
    test_name=name;reset(f);char sid[]="0123456789abcdef";
    if(f==17)cloud_size=11;if(f==18)cloud[1]=1;if(f==22)product_size=3;if(f==36)policy[0]='[';if(f==38)policy[1]=0xdc00;
    if(f==37){policy_units--;const char *extra=",\"note\":\"";for(size_t i=0;i<strlen(extra);++i)policy[policy_units++]=(unsigned char)extra[i];policy[policy_units++]=0x4e2d;policy[policy_units++]=0x6587;policy[policy_units++]=0xd83d;policy[policy_units++]=0xde00;policy[policy_units++]='"';policy[policy_units++]='}';}
    CHECK(Agent_OnAttach(&vm,sid,NULL)==JNI_OK);CHECK(log_count==2&&live_allocs==0&&pending==0&&!locked);CHECK(opened==closed);CHECK(cloud_calls==c&&product_calls==p&&decode_calls==m);CHECK(disposals==(f==1||f==2?0:1));
    char target[40];snprintf(target,sizeof(target)," stage=%d ",expected_stage);CHECK(strstr(logs[1],target));CHECK(strstr(logs[1],expected_stage?" ready=0 ":" ready=1 "));
    if(f==0||f==37)CHECK(strstr(logs[1],"json_rc=0 entry_count=2 duplicate_count=0 candidate_count=1 match_count=1 default_match=1 product_blocked_count=1"));
    CHECK(!strstr(logs[1],"TEST_RID")&&!strstr(logs[1],"DEFAULT")&&!strstr(logs[1],"AA")&&!strstr(logs[1],"country"));
    CHECK(Agent_OnAttach(&vm,sid,NULL)==JNI_OK);CHECK(log_count==2&&cloud_calls==c&&product_calls==p&&decode_calls==m);
}
int main(void) {
    run_case(0,"cache correlation",0,1,1,1);run_case(1,"JNI unavailable",1,0,0,0);run_case(2,"ART TI unavailable",2,0,0,0);
    run_case(3,"enumeration failure",3,0,0,0);run_case(4,"duplicate class",4,0,0,0);run_case(5,"uninitialized",4,0,0,0);run_case(6,"loader mismatch",4,0,0,0);
    run_case(7,"missing field",5,0,0,0);run_case(8,"method mismatch",5,0,0,0);run_case(9,"null key",5,0,0,0);run_case(10,"key class",5,0,0,0);run_case(11,"component",5,0,0,0);run_case(12,"key flags",5,0,0,0);run_case(13,"key name",5,0,0,0);
    run_case(14,"SDK owner unavailable",10,0,0,0);run_case(15,"native cache exception",8,1,0,1);run_case(16,"cloud cache absent",0,1,1,1);run_case(17,"short cloud",8,1,0,1);run_case(18,"bad receiver",8,1,0,1);run_case(19,"array exception",8,1,0,1);run_case(20,"dispose error",13,1,1,1);run_case(21,"owner changed",10,0,0,1);run_case(22,"bad product",8,1,1,1);run_case(23,"product absent",0,1,1,1);
    run_case(24,"namespace absent",6,0,0,0);run_case(25,"MMKV not initialized",6,0,0,0);run_case(26,"MMKV library absent",7,0,0,0);run_case(27,"global busy",7,0,0,0);run_case(28,"instance absent",7,0,0,0);run_case(29,"instance busy",7,0,0,0);run_case(30,"instance reload",7,0,0,0);run_case(31,"multi process",7,0,0,0);run_case(32,"wrapper handle mismatch",8,0,0,0);run_case(33,"MMKV value size",8,0,0,0);run_case(34,"MMKV decode exception",8,0,0,1);run_case(35,"stored namespace absent",0,1,1,1);run_case(36,"malformed JSON",9,1,1,1);run_case(37,"UTF16 to UTF8",0,1,1,1);run_case(38,"invalid UTF16",9,0,0,1);run_case(39,"registry read",7,0,0,0);
    test_name="invalid options";reset(0);char invalid[]="bad";CHECK(Agent_OnAttach(&vm,invalid,NULL)==JNI_ERR);CHECK(log_count==0&&cloud_calls==0);puts("Cloud cache probe: 40 host cases passed");return 0;
}
