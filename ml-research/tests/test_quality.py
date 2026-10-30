from pathlib import Path
import tempfile
import unittest
from mlv2.core import register,review
from mlv2.quality import audit


class QualityTests(unittest.TestCase):
    def test_changed_review_evidence_cannot_count_as_valid(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as name:
            data=Path(name)/'data'
            register(data,'s','r',['healthy'])
            log=Path(name)/'log';log.write_text('independent check')
            result=review(data,'s','r','valid',['healthy'],[log])
            archived=data/'review-evidence'/result['references'][0]['sha256']
            archived.write_text('tampered')
            summary=audit(data,Path(name)/'quality')
            self.assertEqual(summary['valid_runs'],0)
            self.assertEqual(summary['validity_counts'],{'invalid_provenance':1})

    def test_multiple_reviews_need_explicit_selection(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as name:
            data=Path(name)/'data';register(data,'s','r',['healthy'])
            log=Path(name)/'log';log.write_text('check')
            review(data,'s','r','valid',['healthy'],[log])
            review(data,'s','r','uncertain',['healthy'],[log])
            summary=audit(data,Path(name)/'quality')
            self.assertEqual(summary['valid_runs'],0)
            self.assertEqual(summary['validity_counts'],{'ambiguous_review':1})


if __name__=='__main__':unittest.main(verbosity=2)
