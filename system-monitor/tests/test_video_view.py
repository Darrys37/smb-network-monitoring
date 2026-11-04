import unittest
from video_view import diagnosis_lines,measurements,state,TCP


def result(case='R2',status='matched'):
    return {'latest_diagnostics':[{'node':'cli01' if case=='R4' else 'srv01',
        'observation':{'profile':{'target_ip':'172.30.20.20'}},
        'assessment':{'facts':{'target_ping':'success','target_tcp80':'refused','local_service_state':'inactive','http_status_code':None},
                      'diagnoses':[{'rule_id':case+'_FIXTURE','status':status}]}}],
        'correlation':{'active_problem_events':4,'emitted_groups':1,'suppressed_events':0}}


class ViewTests(unittest.TestCase):
    def test_unknown_measurement_is_not_presented_as_confirmed_failure(self):
        self.assertEqual(state(None,TCP),'Chưa đủ dữ liệu')
        self.assertNotEqual(state('refused',TCP),state('timeout',TCP))

    def test_actual_worker_status_controls_match_label(self):
        text='\n'.join(diagnosis_lines(result(status='insufficient_evidence'),'R2'))
        self.assertIn('CHƯA XÁC NHẬN KHỚP',text)
        self.assertIn('Chưa đủ căn cứ',text)

    def test_service_evidence_and_real_counts_are_visible(self):
        text='\n'.join(diagnosis_lines(result(),'R2'))
        for expected in ['refused','inactive','Chưa nhận được mã HTTP','4 cảnh báo → 1 nhóm','ĐỐI CHIẾU LUẬT R2']:
            self.assertIn(expected,text)
        self.assertNotIn('nhấn Enter',text)

    def test_multiple_matched_rules_remain_visible(self):
        r=result();r['latest_diagnostics'][0]['assessment']['diagnoses'].append({'rule_id':'R7_PARENT','status':'matched'})
        self.assertIn('R2, R7','\n'.join(diagnosis_lines(r,'R2')))
