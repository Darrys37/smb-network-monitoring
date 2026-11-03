from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from monitoring.correlation import correlate
from monitoring.store import Store
from monitoring.topology import Topology


def topology():
    return Topology({"version": "unit-test-forest", "nodes": {
        "gateway": {"type": "gateway", "parents": []},
        "server": {"type": "host", "parents": ["gateway"], "dependency_basis": "test routed path"},
        "service": {"type": "service", "parents": ["server"], "dependency_basis": "service hosted on server"},
        "other": {"type": "host", "parents": []}}})


def event(identity, node="server", kind="http_connectivity", clock=1000, state="problem", key=None, **extra):
    return {"source": "test", "event_id": str(identity), "node": node, "kind": kind, "clock": clock,
            "state": state, "key": key or str(identity), **extra}


class CorrelationTests(unittest.TestCase):
    def setUp(self):
        self.graph = topology()
        self.states = {"gateway": {"status": "down", "observed_at": 1010, "down_since": 1000}}

    def test_one_confirmed_root_suppresses_one_hundred_dependent_alerts(self):
        items = [event(1, "gateway", "reachability")] + [event(i + 2, clock=1001 + i % 8) for i in range(100)]
        result = correlate(items, self.graph, self.states, 1010)
        self.assertEqual((result["emitted_groups"], result["suppressed_events"], result["raw_unique_events"]), (1, 100, 101))
        self.assertEqual(result["peak_window_event_count"], 101)

    def test_unknown_or_stale_parent_does_not_suppress(self):
        for states in ({}, {"gateway": {"status": "down", "observed_at": 100, "down_since": 100}}):
            result = correlate([event(1, "gateway", "reachability"), event(2)], self.graph, states, 1010)
            self.assertEqual(result["suppressed_events"], 0)
            self.assertEqual(result["emitted_groups"], 2)

    def test_independent_cpu_fault_survives_a_parent_outage(self):
        result = correlate([event(1, "gateway", "reachability"), event(2), event(3, kind="cpu"), event(4, node="other", kind="dns")], self.graph, self.states, 1010)
        self.assertEqual(result["emitted_groups"], 3)
        self.assertEqual(result["suppressed_events"], 1)

    def test_confirmed_local_service_fault_survives_even_with_connectivity_kind(self):
        result = correlate([event(1, "gateway", "reachability"), event(2, independent_fault=True)], self.graph, self.states, 1010)
        self.assertEqual(result["emitted_groups"], 2)

    def test_same_episode_http_symptom_joins_locally_confirmed_service_fault(self):
        items=[event(1,clock=1000),event(2,kind='http_service',clock=1003,independent_fault=True)]
        result=correlate(items,self.graph,{},1010)
        self.assertEqual(result['emitted_groups'],1)
        self.assertEqual(result['groups'][0]['cause_group'],'http_service')
        items[0]['clock']=900
        self.assertEqual(correlate(items,self.graph,{},1010)['emitted_groups'],2)

    def test_parent_recovery_resurfaces_a_still_active_child(self):
        items = [event(2), event(1, "gateway", "reachability", key="gateway"), event(10, "gateway", "reachability", clock=1005, state="recovery", key="gateway")]
        result = correlate(items, self.graph, {"gateway": {"status": "up", "observed_at": 1010, "down_since": None}}, 1010)
        self.assertEqual(result["active_problem_events"], 1)
        self.assertEqual(result["groups"][0]["root_node"], "server")

    def test_old_child_incident_is_not_blame_shifted_to_a_new_parent_outage(self):
        result = correlate([event(1, clock=900), event(2, "gateway", "reachability")], self.graph, self.states, 1010)
        self.assertEqual(result["emitted_groups"], 2)

    def test_dedup_and_delivery_order_are_deterministic(self):
        items = [event(1, "gateway", "reachability"), event(2)]
        self.assertEqual(correlate(items, self.graph, self.states, 1010), correlate([items[1], items[0], items[1]], self.graph, self.states, 1010))

    def test_conflicting_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            correlate([event(1), event(1, node="other")], self.graph, self.states, 1010)

    def test_numeric_event_id_breaks_same_second_recovery_ties(self):
        result = correlate([event(10, key="same", state="recovery"), event(2, key="same")], self.graph, {}, 1010)
        self.assertEqual(result["active_problem_events"], 0)

    def test_invalid_topology_cannot_suppress(self):
        with self.assertRaises(ValueError):
            Topology({"version": "bad", "nodes": {"a": {"type": "host", "parents": ["b"], "dependency_basis": "bad"}, "b": {"type": "host", "parents": ["a"], "dependency_basis": "bad"}}})

    def test_durable_dedup_restart_and_atomic_cursor_on_failure(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "state.sqlite"
            store = Store(path)
            self.assertEqual(store.ingest([event(1), event(1)], 1010, stream="zabbix", cursor="1"), 1)
            restarted = Store(path)
            self.assertEqual(restarted.cursor("zabbix"), "1")
            with self.assertRaises(ValueError):
                restarted.ingest([event(2), event(1, node="other")], 1011, stream="zabbix", cursor="2")
            self.assertEqual(restarted.cursor("zabbix"), "1")
            self.assertEqual(restarted.counts()["events"], 1)

    def test_repeated_down_observations_keep_original_failure_time(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            store = Store(Path(folder) / "state.sqlite")
            store.set_node_state("gateway", "down", 1000, {})
            store.set_node_state("gateway", "down", 1010, {})
            self.assertEqual(store.node_states()["gateway"]["down_since"], 1000)
            store.set_node_state("gateway", "up", 1020, {})
            self.assertIsNone(store.node_states()["gateway"]["down_since"])


if __name__ == "__main__":
    unittest.main()
