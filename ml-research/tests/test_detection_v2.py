import unittest
from detection_audit_v2 import audit_events


class DetectionTests(unittest.TestCase):
    def test_unrelated_alert_does_not_count_as_detection_of_the_fault(self):
        intervals=[{'label':'cpu_stress','start':100,'end':200,'decision_time':180}]
        events=[{'eventid':'1','objectid':'disk','clock':'150','value':'1','severity':'3'}]
        rows,summary=audit_events(intervals,events,{'related_trigger_ids':{'cpu_stress':['cpu']}})
        self.assertFalse(rows[0]['related_detected_strict'])
        self.assertEqual(summary['cpu_stress']['runs_with_any_significant_problem_event'],1)

    def test_alert_after_model_decision_is_not_claimed_available_at_decision(self):
        intervals=[{'label':'cpu_stress','start':100,'end':200,'decision_time':180}]
        events=[{'eventid':'1','objectid':'cpu','clock':'190','value':'1','severity':'3'}]
        rows,_=audit_events(intervals,events,{'related_trigger_ids':{'cpu_stress':['cpu']}})
        self.assertTrue(rows[0]['related_detected_strict'])
        self.assertFalse(rows[0]['related_detected_by_selected_observation'])
        self.assertEqual(rows[0]['first_related_event_clock_delta_seconds'],90)

    def test_boundary_tolerance_is_separate_and_not_clipped_into_strict_detection(self):
        intervals=[{'label':'cpu_stress','start':100,'end':200,'decision_time':180}]
        events=[{'eventid':'1','objectid':'cpu','clock':'99','value':'1','severity':'3'}]
        rows,_=audit_events(intervals,events,{'related_trigger_ids':{'cpu_stress':['cpu']}})
        self.assertFalse(rows[0]['related_detected_strict'])
        self.assertTrue(rows[0]['related_detected_with_1s_boundary_tolerance'])
        self.assertEqual(rows[0]['boundary_ambiguous_event_ids'],['1'])

    def test_recovery_and_information_events_are_not_problem_detections(self):
        intervals=[{'label':'healthy','start':100,'end':200,'decision_time':180}]
        events=[{'eventid':'1','objectid':'cpu','clock':'120','value':'0','severity':'3'},
                {'eventid':'2','objectid':'cpu','clock':'130','value':'1','severity':'1'}]
        rows,summary=audit_events(intervals,events,{'related_trigger_ids':{'healthy':[]}})
        self.assertEqual(summary['healthy']['runs_with_any_significant_problem_event'],0)


if __name__=='__main__':unittest.main()
