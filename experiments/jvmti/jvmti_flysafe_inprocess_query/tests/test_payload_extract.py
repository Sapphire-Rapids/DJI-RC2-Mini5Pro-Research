import ctypes
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"build/payload-extract-host"
BUILD.mkdir(parents=True,exist_ok=True)
class Summary(ctypes.Structure):
    _fields_=[(n,ctypes.c_int) for n in (
        'policy_rc','matching_row_count','default_present','default_nonempty',
        'matched_hex_valid','default_hex_valid','matched_hex_length','matched_decoded_length',
        'default_hex_length','default_decoded_length','json_length','row_count',
        'effective_row_count','duplicate_row_count','default_row_count','blocked_row_count','candidate_count')]

def namespace(rows, **other):
    return json.dumps({'country_and_device_type':json.dumps(rows,ensure_ascii=False),**other},ensure_ascii=False).encode()
def row(country,data,blocked=()):return {'country_code':country,'data':data,'block_device':list(blocked)}

class PayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(ROOT/'src/native/payload_extract.c'),'-o',str(BUILD/'payload_extract_host.dylib')],check=True)
        cls.lib=ctypes.CDLL(str(BUILD/'payload_extract_host.dylib'));cls.fun=cls.lib.cloud_payload_extract
        cls.fun.argtypes=[ctypes.c_char_p,ctypes.c_size_t,ctypes.c_int64,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(Summary)]
        cls.fun.restype=ctypes.c_int;cls.free=ctypes.CDLL(None).free;cls.free.argtypes=[ctypes.c_void_p]
    def run_extract(self,ns,cache=b'AA',product=139,receiver=(18,4)):
        out=ctypes.c_void_p(1);length=ctypes.c_size_t(99);summary=Summary()
        rc=self.fun(ns,len(ns) if ns is not None else 0,product,cache,len(cache) if cache is not None else 0,*receiver,ctypes.byref(out),ctypes.byref(length),ctypes.byref(summary))
        if rc:
            self.assertFalse(out.value);self.assertEqual(length.value,0);return rc,None,summary
        self.assertTrue(out.value);self.assertLessEqual(length.value,32768)
        data=ctypes.string_at(out,length.value);self.free(out)
        self.assertNotIn(b'country_code',data);self.assertNotIn(b'TEST-AREA',data);self.assertNotIn(b'country_and_device_type',data)
        doc=json.loads(data);self.assertEqual(summary.json_length,len(data));return rc,doc,summary
    def test_match_and_default(self):
        rc,d,s=self.run_extract(namespace([row('DEFAULT','CC'),row('TEST-AREA','AA')]))
        self.assertEqual(rc,0);self.assertEqual(d['matched_hex'],'AA');self.assertEqual(d['default_hex'],'CC');self.assertEqual(s.matching_row_count,1);self.assertEqual(s.matched_decoded_length,1)
    def test_fallback_blocked(self):
        rc,d,s=self.run_extract(namespace([row('DEFAULT','AA'),row('TEST-AREA','BB',[139])]))
        self.assertEqual(rc,0);self.assertEqual(s.blocked_row_count,1);self.assertEqual(d['default_hex'],'AA')
    def test_blocked_nondefault_not_eligible(self):
        rc,_,_=self.run_extract(namespace([row('DEFAULT','CC'),row('TEST-AREA','AA',[139])]))
        self.assertEqual(rc,8)
    def test_duplicate_nonfirst_not_eligible(self):
        self.assertEqual(self.run_extract(namespace([row('TEST-AREA','BB'),row('TEST-AREA','AA')]))[0],8)
    def test_duplicate_raw_count(self):
        rc,d,s=self.run_extract(namespace([row('DEFAULT','CC'),row('TEST-AREA','AA'),row('TEST-AREA','AA'),row('TEST-OTHER','AA',[139])]))
        self.assertEqual(rc,0);self.assertEqual(s.matching_row_count,3);self.assertEqual(d['matching_row_count'],3);self.assertEqual(s.duplicate_row_count,1)
    def test_first_default(self):
        rc,d,s=self.run_extract(namespace([row('DEFAULT','CC'),row('DEFAULT','DD'),row('TEST-AREA','AA')]))
        self.assertEqual(rc,0);self.assertEqual(d['default_hex'],'CC');self.assertEqual(s.default_row_count,2)
    def test_missing_default(self):
        rc,d,s=self.run_extract(namespace([row('TEST-AREA','AA')]))
        self.assertEqual(rc,0);self.assertIsNone(d['default_hex']);self.assertEqual(s.default_present,0);self.assertEqual(s.default_hex_length,-1)
    def test_empty_default(self):
        rc,d,s=self.run_extract(namespace([row('DEFAULT',''),row('TEST-AREA','AA')]))
        self.assertEqual(rc,0);self.assertEqual(d['default_hex'],'');self.assertEqual((s.default_present,s.default_nonempty,s.default_hex_valid,s.default_decoded_length),(1,0,1,0))
    def test_wrong_receiver(self):
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','AA')]),receiver=(3,0))[0],7)
    def test_empty_cache(self):
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','AA')]),cache=None)[0],6)
    def test_no_match(self):
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','BB')]))[0],8)
    def test_matched_hex_invalid(self):
        for bad in ('A','A G','GG','🙂','AA\n'):
            rc,_,s=self.run_extract(namespace([row('DEFAULT',bad)]),cache=bad.encode())
            self.assertEqual(rc,9);self.assertEqual(s.matched_hex_valid,0);self.assertEqual(s.matched_hex_length,len(bad.encode()))
    def test_default_hex_invalid(self):
        rc,_,s=self.run_extract(namespace([row('DEFAULT','arbitrary secret text'),row('TEST-AREA','AA')]))
        self.assertEqual(rc,10);self.assertEqual(s.default_hex_valid,0);self.assertEqual(s.matched_hex_valid,1)
    def test_utf8_comments_not_exported(self):
        r=row('TEST-AREA','Aa01');r['note']='中文🙂';rc,d,_=self.run_extract(namespace([r],note='説明'),cache=b'Aa01')
        self.assertEqual(rc,0);self.assertEqual(d['matched_hex'],'Aa01');self.assertNotIn('note',d)
    def test_json_escape_hex(self):
        ns=b'{"country_and_device_type":"[{\\\"country_code\\\":\\\"DEFAULT\\\",\\\"data\\\":\\\"\\\\u0041A\\\",\\\"block_device\\\":[]}]"}'
        self.assertEqual(self.run_extract(ns)[0],0)
    def test_strict_case_match(self):
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','aa')]))[0],8)
    def test_malformed_inputs(self):
        for ns in (b'{',b'[]',b'{"country_and_device_type":{}}',b'{"country_and_device_type":"[{}]"}'):
            self.assertEqual(self.run_extract(ns)[0],3)
    def test_namespace_absent(self):
        for ns in (None,b'{}',b'{"country_and_device_type":null}',b'{"country_and_device_type":"null"}',b'{"country_and_device_type":""}'):
            self.assertEqual(self.run_extract(ns)[0],2)
    def test_product_missing(self):
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','AA')]),product=-1)[0],5)
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','AA')]),product=65536)[0],1)
    def test_output_limit(self):
        payload='AB'*17000;rc,_,s=self.run_extract(namespace([row('TEST-AREA',payload)]),cache=payload.encode())
        self.assertEqual(rc,11);self.assertEqual(s.matched_hex_length,34000);self.assertEqual(s.matched_decoded_length,17000)
    def test_input_limit(self):
        self.assertEqual(self.run_extract(b' '*65537)[0],4)
    def test_no_empty_candidate(self):
        self.assertEqual(self.run_extract(namespace([row('DEFAULT','')]),cache=b'')[0],8)

if __name__=='__main__':unittest.main()
