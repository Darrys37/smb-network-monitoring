"""Explicit dependency forest. A peer address never becomes a parent implicitly."""
import ipaddress


class Topology:
    def __init__(self, config):
        self.version = config["version"]
        self.nodes = config["nodes"]
        if not isinstance(self.nodes, dict) or not self.nodes:
            raise ValueError("Empty topology")
        self.dependent_kinds = set(config.get("dependent_kinds", ["reachability", "http_connectivity", "agent_connectivity"]))
        for name, node in self.nodes.items():
            if not name or node.get("type") not in {"host", "gateway", "service"}:
                raise ValueError("Invalid topology node")
            if node.get("address"):
                ipaddress.ip_address(node["address"])
            parents = node.get("parents", [])
            if not isinstance(parents, list) or len(parents) > 1 or any(parent not in self.nodes or parent == name for parent in parents):
                raise ValueError("Unsupported/invalid dependency; this version requires a forest")
            if parents and not node.get("dependency_basis"):
                raise ValueError("Parent relationships require an explicit dependency basis")
        for name in self.nodes:
            seen = {name}
            parent = self.parent(name)
            while parent is not None:
                if parent in seen:
                    raise ValueError("Topology cycle")
                seen.add(parent)
                parent = self.parent(parent)

    def parent(self, name):
        parents = self.nodes[name].get("parents", [])
        return parents[0] if parents else None

    def ancestors(self, name):
        values = []
        node = self.parent(name)
        while node is not None:
            values.append(node)
            node = self.parent(node)
        return values

    def path(self, child, ancestor):
        values = [child]
        while values[-1] != ancestor:
            parent = self.parent(values[-1])
            if parent is None:
                raise ValueError("Nodes do not have a dependency relationship")
            values.append(parent)
        return values
