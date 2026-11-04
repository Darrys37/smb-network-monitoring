from copy import deepcopy
import unittest
from monitoring.platform import ready,unchanged
def health():
 node={'stall_count':0,'recent_stall':False,'package_jobs_active':False,'dpkg_lock_held':False,'package_audit_clean':True,'package_status_sha256':'a'*64,'boot_id':'boot-one'}
 return {'status':'ok','schema_version':2,'nodes':{h:deepcopy(node) for h in ['mon01','srv01','cli01']}}
class PlatformTests(unittest.TestCase):
 def test_clean_platform_and_same_session(self):
  r=health();self.assertTrue(ready(r));self.assertTrue(unchanged(r,deepcopy(r)))
 def test_missing_platform_or_node_never_certifies_ready(self):
  for r in [{},{'status':'error'},None]:self.assertFalse(ready(r))
  r=health();del r['nodes']['srv01'];self.assertFalse(ready(r))
 def test_stall_package_activity_and_locks_block_fault(self):
  for field,value in [('stall_count',1),('recent_stall',True),('package_jobs_active',True),('dpkg_lock_held',True),('package_audit_clean',False)]:
   with self.subTest(field=field):
    r=health();r['nodes']['mon01'][field]=value;self.assertFalse(ready(r))
 def test_reboot_or_package_change_is_not_a_passed_demo(self):
  before=health()
  for field,value in [('boot_id','new-boot'),('package_status_sha256','b'*64)]:
   after=deepcopy(before);after['nodes']['mon01'][field]=value;self.assertFalse(unchanged(before,after))
if __name__=='__main__':unittest.main()
