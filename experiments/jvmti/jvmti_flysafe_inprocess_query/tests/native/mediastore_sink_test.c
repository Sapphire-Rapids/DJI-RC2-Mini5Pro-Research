#include "mediastore_sink.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *test_name;
static unsigned checks, cases;
#define CHECK(v) do { ++checks; if (!(v)) { fprintf(stderr,"FAIL %s:%d %s\n",test_name,__LINE__,#v); exit(1); } } while (0)
#define OBJ(v) ((jobject)(uintptr_t)(v))
#define MID(v) ((jmethodID)(uintptr_t)(v))
enum { CONTEXT=1, MANAGER, LIST, NAMES, COLLECTION, INSERTED, RESOLVER, STREAM, PENDING_VALUES, FINAL_VALUES, INTEGER_ZERO, INTEGER_ONE, BYTES, VOL0=30, STR_BASE=1000 };
enum { SERVICE=1, GET_RESOLVER, VOLUMES, SIZE, GET, REMOVABLE, PRIMARY, EMULATED, STATE, VOLUME_NAME, CONTAINS, EXTERNAL_NAMES, CONTENT_URI, CONSTRUCTOR, PUT_STRING, PUT_INTEGER, VALUE_OF, INSERT, OPEN, WRITE, FLUSH, CLOSE, UPDATE, DELETE_ROW, TO_STRING };
enum { NONE, FRAME_FAIL, CLASS_FAIL, METHOD_FAIL, SERVICE_FAIL, VOLUMES_FAIL, SIZE_FAIL, GET_FAIL, STATE_FAIL, NAME_FAIL, NAMES_FAIL, CONTENT_URI_FAIL, RESOLVER_FAIL, NEW_OBJECT_FAIL, NEW_STRING_FAIL, BYTE_ARRAY_FAIL, BYTE_REGION_FAIL, PUT_FAIL, INSERT_NULL, INSERT_EXCEPTION, OPEN_NULL, OPEN_EXCEPTION, WRITE_EXCEPTION, FLUSH_EXCEPTION, CLOSE_EXCEPTION, UPDATE_ZERO, UPDATE_EXCEPTION, DELETE_ZERO, DELETE_EXCEPTION, INSERT_STRING_EXCEPTION, REGION_EXCEPTION, WRITE_CLOSE_EXCEPTION };
static struct {
    int pending, fault, frame, pushes, pops, strings, objects, volume_count, names_present;
    int removable[64], primary[64], emulated[64];
    const char *state, *name, *collection, *inserted;
    int insert_count, write_count, flush_count, close_count, update_count, delete_count;
    int put_count, pending_one, pending_zero, clear_count, new_string_calls;
    jsize bytes_length;
    unsigned char bytes[MEDIASTORE_SINK_MAX_BYTES];
    char string[256][512], events[32];
    size_t event_count;
} f;
static void event(char ch) { CHECK(f.event_count+1<sizeof(f.events)); f.events[f.event_count++]=ch; f.events[f.event_count]=0; }
static void ready(void) { CHECK(!f.pending); }
static const char *sval(jobject object) { uintptr_t n=(uintptr_t)object; CHECK(n>=STR_BASE&&n<STR_BASE+(unsigned)f.strings); return f.string[n-STR_BASE]; }
static jobject string_object(const char *text) { CHECK(f.strings<256&&strlen(text)<sizeof(f.string[0])); strcpy(f.string[f.strings],text); return OBJ(STR_BASE+f.strings++); }
static int fail(int fault) { if(f.fault!=fault)return 0; f.pending=1; return 1; }
static jboolean JNICALL excheck(JNIEnv *e) { (void)e; return f.pending?JNI_TRUE:JNI_FALSE; }
static void JNICALL exclear(JNIEnv *e) { (void)e; CHECK(f.pending); f.pending=0; ++f.clear_count; }
static jint JNICALL push(JNIEnv *e,jint cap) { (void)e; ready(); CHECK(cap>=32); ++f.pushes; if(fail(FRAME_FAIL))return JNI_ERR; f.frame=1; return JNI_OK; }
static jobject JNICALL pop(JNIEnv *e,jobject value) { (void)e; ready(); CHECK(f.frame&&value==NULL); f.frame=0; ++f.pops; return NULL; }
static void JNICALL delref(JNIEnv *e,jobject value) { (void)e; (void)value; }
static jclass JNICALL findclass(JNIEnv *e,const char *name) { (void)e; ready(); CHECK(name&&*name); if(fail(CLASS_FAIL))return NULL; return (jclass)OBJ(500); }
static jmethodID JNICALL method(JNIEnv *e,jclass cls,const char *name,const char *sig) {
    (void)e; ready(); CHECK(cls==(jclass)OBJ(500)); if(fail(METHOD_FAIL))return NULL;
    static const struct { const char *name,*sig; int id; } entries[]={
        {"getSystemService","(Ljava/lang/String;)Ljava/lang/Object;",SERVICE},
        {"getContentResolver","()Landroid/content/ContentResolver;",GET_RESOLVER},
        {"getStorageVolumes","()Ljava/util/List;",VOLUMES},{"size","()I",SIZE},{"get","(I)Ljava/lang/Object;",GET},
        {"isRemovable","()Z",REMOVABLE},{"isPrimary","()Z",PRIMARY},{"isEmulated","()Z",EMULATED},
        {"getState","()Ljava/lang/String;",STATE},{"getMediaStoreVolumeName","()Ljava/lang/String;",VOLUME_NAME},
        {"contains","(Ljava/lang/Object;)Z",CONTAINS},
        {"getExternalVolumeNames","(Landroid/content/Context;)Ljava/util/Set;",EXTERNAL_NAMES},
        {"getContentUri","(Ljava/lang/String;)Landroid/net/Uri;",CONTENT_URI},
        {"<init>","()V",CONSTRUCTOR},{"put","(Ljava/lang/String;Ljava/lang/String;)V",PUT_STRING},
        {"put","(Ljava/lang/String;Ljava/lang/Integer;)V",PUT_INTEGER},{"valueOf","(I)Ljava/lang/Integer;",VALUE_OF},
        {"insert","(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;",INSERT},
        {"openOutputStream","(Landroid/net/Uri;Ljava/lang/String;)Ljava/io/OutputStream;",OPEN},
        {"write","([B)V",WRITE},{"flush","()V",FLUSH},{"close","()V",CLOSE},
        {"update","(Landroid/net/Uri;Landroid/content/ContentValues;Ljava/lang/String;[Ljava/lang/String;)I",UPDATE},
        {"delete","(Landroid/net/Uri;Ljava/lang/String;[Ljava/lang/String;)I",DELETE_ROW},
        {"toString","()Ljava/lang/String;",TO_STRING}
    };
    for(size_t i=0;i<sizeof(entries)/sizeof(entries[0]);++i)if(!strcmp(name,entries[i].name)&&!strcmp(sig,entries[i].sig))return MID(entries[i].id);
    CHECK(0); return NULL;
}
static jstring JNICALL newstring(JNIEnv *e,const char *text) { (void)e; ready(); ++f.new_string_calls; if(f.fault==NEW_STRING_FAIL&&f.new_string_calls==3){f.pending=1;return NULL;}return (jstring)string_object(text); }
static jsize JNICALL slength(JNIEnv *e,jstring str) { (void)e; ready(); return (jsize)strlen(sval((jobject)str)); }
static void JNICALL sregion(JNIEnv *e,jstring str,jsize start,jsize count,jchar *out) { (void)e; ready(); const char *s=sval((jobject)str); CHECK(start>=0&&count>=0&&(size_t)(start+count)<=strlen(s)); if(fail(REGION_EXCEPTION))return; for(jsize i=0;i<count;++i)out[i]=(unsigned char)s[start+i]; }
static jobject JNICALL newobject(JNIEnv *e,jclass cls,jmethodID id,const jvalue *args) { (void)e; ready(); CHECK(cls==(jclass)OBJ(500)&&id==MID(CONSTRUCTOR)&&args==NULL); if(fail(NEW_OBJECT_FAIL))return NULL; CHECK(f.objects<2);return OBJ(PENDING_VALUES+f.objects++); }
static jbyteArray JNICALL newbytes(JNIEnv *e,jsize count) { (void)e; ready(); CHECK(count>0&&(unsigned)count<=MEDIASTORE_SINK_MAX_BYTES); if(fail(BYTE_ARRAY_FAIL))return NULL; f.bytes_length=count;return (jbyteArray)OBJ(BYTES); }
static void JNICALL setbytes(JNIEnv *e,jbyteArray array,jsize start,jsize count,const jbyte *data) { (void)e; ready(); CHECK(array==(jbyteArray)OBJ(BYTES)&&start==0&&count==f.bytes_length); if(fail(BYTE_REGION_FAIL))return; memcpy(f.bytes,data,(size_t)count); }
static jobject JNICALL objectcall(JNIEnv *e,jobject object,jmethodID method_id,const jvalue *a) {
    (void)e; ready(); int id=(int)(uintptr_t)method_id;
    switch(id){
    case SERVICE: CHECK(object==OBJ(CONTEXT)&&!strcmp(sval(a[0].l),"storage"));return fail(SERVICE_FAIL)?NULL:OBJ(MANAGER);
    case GET_RESOLVER: CHECK(object==OBJ(CONTEXT));return fail(RESOLVER_FAIL)?NULL:OBJ(RESOLVER);
    case VOLUMES: CHECK(object==OBJ(MANAGER));return fail(VOLUMES_FAIL)?NULL:OBJ(LIST);
    case GET: CHECK(object==OBJ(LIST)&&a[0].i>=0&&a[0].i<f.volume_count);return fail(GET_FAIL)?NULL:OBJ(VOL0+a[0].i);
    case STATE: CHECK((uintptr_t)object>=VOL0&&(uintptr_t)object<VOL0+64);return fail(STATE_FAIL)?NULL:string_object(f.state);
    case VOLUME_NAME: return fail(NAME_FAIL)?NULL:string_object(f.name);
    case TO_STRING:
        CHECK(object==OBJ(COLLECTION)||object==OBJ(INSERTED));
        if(object==OBJ(INSERTED)&&fail(INSERT_STRING_EXCEPTION))return NULL;
        return string_object(object==OBJ(COLLECTION)?f.collection:f.inserted);
    case INSERT:
        CHECK(object==OBJ(RESOLVER)&&a[0].l==OBJ(COLLECTION)&&a[1].l==OBJ(PENDING_VALUES));
        CHECK(f.put_count==3&&f.pending_one==1&&f.pending_zero==1&&f.bytes_length>0);
        CHECK(++f.insert_count==1); event('I'); if(fail(INSERT_EXCEPTION)||f.fault==INSERT_NULL)return NULL;return OBJ(INSERTED);
    case OPEN:
        CHECK(object==OBJ(RESOLVER)&&a[0].l==OBJ(INSERTED)&&!strcmp(sval(a[1].l),"w")); event('O');
        if(fail(OPEN_EXCEPTION)||f.fault==OPEN_NULL)return NULL;return OBJ(STREAM);
    default: CHECK(0);return NULL;
    }
}
static jobject JNICALL staticcall(JNIEnv *e,jclass cls,jmethodID id,const jvalue *a) {
    (void)e; ready(); CHECK(cls==(jclass)OBJ(500));
    if(id==MID(EXTERNAL_NAMES)){CHECK(a[0].l==OBJ(CONTEXT));return fail(NAMES_FAIL)?NULL:OBJ(NAMES);}
    if(id==MID(CONTENT_URI)){CHECK(!strcmp(sval(a[0].l),f.name));return fail(CONTENT_URI_FAIL)?NULL:OBJ(COLLECTION);}
    CHECK(id==MID(VALUE_OF)&&(a[0].i==0||a[0].i==1));return OBJ(a[0].i?INTEGER_ONE:INTEGER_ZERO);
}
static jboolean JNICALL boolcall(JNIEnv *e,jobject object,jmethodID id,const jvalue *a) {
    (void)e; ready();
    if(id==MID(CONTAINS)){CHECK(object==OBJ(NAMES)&&!strcmp(sval(a[0].l),f.name));return (jboolean)f.names_present;}
    uintptr_t index=(uintptr_t)object-VOL0;CHECK(index<64);
    if(id==MID(REMOVABLE))return (jboolean)f.removable[index];
    if(id==MID(PRIMARY))return (jboolean)f.primary[index];
    CHECK(id==MID(EMULATED));return (jboolean)f.emulated[index];
}
static jint JNICALL intcall(JNIEnv *e,jobject object,jmethodID id,const jvalue *a) {
    (void)e; ready();
    if(id==MID(SIZE)){CHECK(object==OBJ(LIST));if(fail(SIZE_FAIL))return 0;return f.volume_count;}
    CHECK(object==OBJ(RESOLVER)&&a[0].l==OBJ(INSERTED));
    if(id==MID(UPDATE)){
        CHECK(a[1].l==OBJ(FINAL_VALUES)&&a[2].l==NULL&&a[3].l==NULL);CHECK(f.close_count==1&&f.write_count==1&&f.flush_count==1);CHECK(++f.update_count==1);event('P');
        if(fail(UPDATE_EXCEPTION)||f.fault==UPDATE_ZERO)return 0;return 1;
    }
    CHECK(id==MID(DELETE_ROW)&&a[1].l==NULL&&a[2].l==NULL);CHECK(++f.delete_count==1);event('D');
    if(fail(DELETE_EXCEPTION)||f.fault==DELETE_ZERO)return 0;return 1;
}
static void JNICALL voidcall(JNIEnv *e,jobject object,jmethodID id,const jvalue *a) {
    (void)e; ready();
    if(id==MID(PUT_STRING)){
        CHECK(object==OBJ(PENDING_VALUES)); const char *key=sval(a[0].l),*value=sval(a[1].l);
        if(!strcmp(key,"_display_name"))CHECK(!strcmp(value,"FindUAS_A057_policy_0123456789abcdef.json"));
        else if(!strcmp(key,"mime_type"))CHECK(!strcmp(value,"application/json"));
        else {CHECK(!strcmp(key,"relative_path"));CHECK(!strcmp(value,"Download/FindUAS/Probe/"));}
        ++f.put_count;fail(PUT_FAIL);return;
    }
    if(id==MID(PUT_INTEGER)){
        CHECK(!strcmp(sval(a[0].l),"is_pending"));
        if(object==OBJ(PENDING_VALUES)){CHECK(a[1].l==OBJ(INTEGER_ONE));++f.pending_one;}
        else {CHECK(object==OBJ(FINAL_VALUES)&&a[1].l==OBJ(INTEGER_ZERO));++f.pending_zero;}
        return;
    }
    CHECK(object==OBJ(STREAM));
    if(id==MID(WRITE)){CHECK(a[0].l==OBJ(BYTES)&&++f.write_count==1);event('W');if(f.fault==WRITE_CLOSE_EXCEPTION||f.fault==DELETE_ZERO||f.fault==DELETE_EXCEPTION)f.pending=1;else fail(WRITE_EXCEPTION);return;}
    if(id==MID(FLUSH)){CHECK(++f.flush_count==1);event('F');fail(FLUSH_EXCEPTION);return;}
    CHECK(id==MID(CLOSE)&&++f.close_count==1);event('C');if(f.fault==WRITE_CLOSE_EXCEPTION)f.pending=1;else fail(CLOSE_EXCEPTION);
}
static const struct JNINativeInterface_ table={
    .ExceptionCheck=excheck,.ExceptionClear=exclear,.PushLocalFrame=push,.PopLocalFrame=pop,.DeleteLocalRef=delref,
    .FindClass=findclass,.GetMethodID=method,.GetStaticMethodID=method,.NewStringUTF=newstring,.GetStringLength=slength,.GetStringRegion=sregion,
    .NewObjectA=newobject,.NewByteArray=newbytes,.SetByteArrayRegion=setbytes,.CallObjectMethodA=objectcall,.CallStaticObjectMethodA=staticcall,
    .CallBooleanMethodA=boolcall,.CallIntMethodA=intcall,.CallVoidMethodA=voidcall
};
static JNIEnv env=&table;
static const unsigned char json[]={123,34,112,111,108,105,99,121,34,58,34,84,69,83,84,45,0xe4,0xb8,0xad,0xe6,0x96,0x87,0xf0,0x9f,0x98,0x80,34,125};
static void reset(const char *name,int fault){
    test_name=name;memset(&f,0,sizeof(f));f.fault=fault;f.volume_count=1;f.removable[0]=f.removable[1]=1;f.names_present=1;
    f.state="mounted";f.name="test-sd";f.collection="content://media/test-sd/downloads";f.inserted="content://media/test-sd/downloads/123";
}
static struct mediastore_sink_result run(int code,const char *events){
    struct mediastore_sink_result r;
    CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",json,sizeof(json),&r)==code);
    CHECK(r.code==code&&!f.pending&&f.frame==0&&f.pops==(f.pushes&&f.fault!=FRAME_FAIL));
    CHECK(!strcmp(f.events,events));CHECK(r.insert_count==f.insert_count&&r.write_count==f.write_count&&r.close_count==f.close_count&&r.publish_count==f.update_count&&r.delete_count==f.delete_count);
    CHECK(r.saved_bytes==(code==MEDIASTORE_SINK_SAVED?sizeof(json):0));
    CHECK(r.cleanup_status==(f.delete_count?(f.fault==DELETE_ZERO||f.fault==DELETE_EXCEPTION?MEDIASTORE_SINK_CLEANUP_FAILED:MEDIASTORE_SINK_CLEANUP_REMOVED):code==MEDIASTORE_SINK_URI_INVALID?MEDIASTORE_SINK_CLEANUP_UNVERIFIED_URI:MEDIASTORE_SINK_CLEANUP_NOT_NEEDED));
    ++cases;return r;
}
int main(void){
    reset("complete UTF8 output",NONE);run(MEDIASTORE_SINK_SAVED,"IOWFCP");CHECK(!memcmp(f.bytes,json,sizeof(json)));
    const struct { int fault,code;const char *name; } early[]={
        {FRAME_FAIL,4,"frame"},{CLASS_FAIL,4,"class"},{METHOD_FAIL,4,"method"},{SERVICE_FAIL,5,"service"},{VOLUMES_FAIL,5,"volumes"},{SIZE_FAIL,5,"size"},{GET_FAIL,5,"get"},{STATE_FAIL,5,"state"},{NAME_FAIL,5,"name"},{NAMES_FAIL,8,"names"},{CONTENT_URI_FAIL,8,"collection"},{RESOLVER_FAIL,9,"resolver"},{NEW_OBJECT_FAIL,9,"values"},{NEW_STRING_FAIL,9,"string"},{BYTE_ARRAY_FAIL,9,"byte array"},{BYTE_REGION_FAIL,9,"byte region"},{PUT_FAIL,9,"put"},{REGION_EXCEPTION,5,"string region"}
    };
    for(size_t i=0;i<sizeof(early)/sizeof(early[0]);++i){reset(early[i].name,early[i].fault);run(early[i].code,"");}
    reset("zero volumes",NONE);f.volume_count=0;run(6,"");
    reset("multiple eligible volumes",NONE);f.volume_count=2;run(7,"");
    reset("too many volumes",NONE);f.volume_count=65;run(5,"");
    reset("negative count",NONE);f.volume_count=-1;run(5,"");
    reset("nonremovable",NONE);f.removable[0]=0;run(6,"");
    reset("primary",NONE);f.primary[0]=1;run(6,"");
    reset("emulated",NONE);f.emulated[0]=1;run(6,"");
    reset("unmounted",NONE);f.state="unmounted";run(6,"");
    reset("one eligible among other volumes",NONE);f.volume_count=3;f.removable[0]=0;f.primary[2]=1;run(0,"IOWFCP");
    reset("unavailable names",NONE);f.names_present=0;run(8,"");
    const char *badnames[]={"external","external_primary","","TEST-SD","/test","test/sd"};
    for(size_t i=0;i<sizeof(badnames)/sizeof(badnames[0]);++i){reset("invalid volume name",NONE);f.name=badnames[i];run(8,"");}
    reset("unexpected collection",NONE);f.collection="content://media/test-sd/images";run(8,"");
    reset("insert null",INSERT_NULL);run(10,"I");reset("insert exception",INSERT_EXCEPTION);run(10,"I");
    const char *baduris[]={"content://media/test-sd/downloads","content://media/test-sd/downloads/0","content://media/test-sd/downloads/01","content://media/test-sd/downloads/1?bad","content://media/test-sd/downloads/1/2","content://media/test-sd/downloads/9223372036854775808","content://media/other/downloads/123","file:///TEST"};
    for(size_t i=0;i<sizeof(baduris)/sizeof(baduris[0]);++i){reset("untrusted URI not touched",NONE);f.inserted=baduris[i];run(11,"I");}
    reset("URI conversion exception",INSERT_STRING_EXCEPTION);run(11,"I");
    reset("open null",OPEN_NULL);run(12,"IOD");reset("open exception",OPEN_EXCEPTION);run(12,"IOD");
    reset("write exception closes then deletes",WRITE_EXCEPTION);run(13,"IOWCD");
    reset("flush exception closes then deletes",FLUSH_EXCEPTION);run(14,"IOWFCD");
    reset("close failure never publishes",CLOSE_EXCEPTION);CHECK(run(15,"IOWFCD").close_failed==1);
    reset("write and close failures still delete",WRITE_CLOSE_EXCEPTION);CHECK(run(13,"IOWCD").close_failed==1);
    reset("update zero removes own URI",UPDATE_ZERO);run(16,"IOWFCPD");
    reset("update exception removes own URI",UPDATE_EXCEPTION);run(16,"IOWFCPD");
    reset("delete zero classified",DELETE_ZERO);CHECK(run(13,"IOWCD").cleanup_status==MEDIASTORE_SINK_CLEANUP_FAILED);
    reset("delete exception consumed",DELETE_EXCEPTION);CHECK(run(13,"IOWCD").cleanup_status==MEDIASTORE_SINK_CLEANUP_FAILED);
    reset("entry exception untouched",NONE);f.pending=1;struct mediastore_sink_result r;
    CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",json,sizeof(json),&r)==3&&f.pending&&f.clear_count==0&&f.pushes==0);++cases;
    const char *badsids[]={"","a","0123456789abcdeF","0123456789abcdef0","0123456789abcdeg"};
    for(size_t i=0;i<sizeof(badsids)/sizeof(badsids[0]);++i){reset("bad SID no JNI",NONE);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),badsids[i],json,sizeof(json),&r)==1&&f.pushes==0);++cases;}
    reset("size bounds",NONE);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",json,32769,&r)==2&&f.pushes==0);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",json,0,&r)==1&&f.pushes==0);++cases;
    reset("null arguments",NONE);CHECK(mediastore_sink_write(NULL,OBJ(CONTEXT),"0123456789abcdef",json,sizeof(json),&r)==1);CHECK(mediastore_sink_write(&env,NULL,"0123456789abcdef",json,sizeof(json),&r)==1);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),NULL,json,sizeof(json),&r)==1);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",NULL,sizeof(json),&r)==1);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",json,sizeof(json),NULL)==1);CHECK(f.pushes==0);++cases;
    reset("exact max size",NONE);unsigned char *big=malloc(MEDIASTORE_SINK_MAX_BYTES);CHECK(big);memset(big,' ',MEDIASTORE_SINK_MAX_BYTES);CHECK(mediastore_sink_write(&env,OBJ(CONTEXT),"0123456789abcdef",big,MEDIASTORE_SINK_MAX_BYTES,&r)==0&&r.saved_bytes==MEDIASTORE_SINK_MAX_BYTES);CHECK(!memcmp(f.bytes,big,MEDIASTORE_SINK_MAX_BYTES));free(big);++cases;
    printf("mediastore sink: %u cases, %u checks passed\n",cases,checks);return 0;
}
