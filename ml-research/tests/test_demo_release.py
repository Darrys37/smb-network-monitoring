import tempfile,unittest
from pathlib import Path
from candidate_v2 import write_database
from mlv2.core import read,save_new,sha
from mlv2.features import FEATURES,CATEGORICAL,NUMERIC
from run_demo_v2 import validate_release


class DemoReleaseTests(unittest.TestCase):
    def test_demo_refuses_unreviewed_changed_or_wrong_scope_artifacts_before_injection(self):
        root=Path(__file__).resolve().parent
        profile=read(root.parent/'config/srv01.json')
        with tempfile.TemporaryDirectory(dir=root) as directory:
            path=Path(directory);candidate=path/'candidate.sqlite';release=path/'release.json'
            write_database(candidate,[{'rule_id':'leaf','conditions':[],'label':'healthy','training_runs':6,'leaf_class_fraction':1.}],[],
                {'profile':profile,'features':FEATURES,'categorical':CATEGORICAL,'numeric':NUMERIC})
            save_new(release,{'status':'INITIAL_VM_ML_RELEASE_VERIFIED','candidate_db':str(candidate),'candidate_sha256':sha(candidate)})
            self.assertEqual(validate_release(release,profile),candidate)
            with self.assertRaisesRegex(ValueError,'profile'):
                validate_release(release,{**profile,'target_ip':'192.168.56.99'})
            changed=path/'changed.json';save_new(changed,{'status':'INITIAL_VM_ML_RELEASE_VERIFIED','candidate_db':str(candidate),'candidate_sha256':'invalid'})
            with self.assertRaisesRegex(ValueError,'artifact changed'):validate_release(changed,profile)
            unreviewed=path/'unreviewed.json';save_new(unreviewed,{'status':'pending'})
            with self.assertRaisesRegex(ValueError,'final review'):validate_release(unreviewed,profile)


if __name__=='__main__':unittest.main()
