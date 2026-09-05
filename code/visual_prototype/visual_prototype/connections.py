from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Connection:
    a: object
    b: object
    distance: float
    trunk: bool = True


def _pair_affinity(a_id: int, b_id: int) -> float:
    low, high = sorted((a_id, b_id))
    value = (low * 73856093) ^ (high * 19349663)
    return (value & 0xFFFF) / 65535.0


def _orientation(a, b, c):
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _crosses(candidate, selected):
    a, b = candidate.a, candidate.b
    for edge in selected:
        c, d = edge.a, edge.b
        if len({a.node_id, b.node_id, c.node_id, d.node_id}) < 4:
            continue
        if (_orientation(a, b, c) * _orientation(a, b, d) < 0
                and _orientation(c, d, a) * _orientation(c, d, b) < 0):
            return True
    return False


def choose_connections(nodes, cfg):
    """Build a degree-limited Euclidean MST, then add sparse local branches."""
    if len(nodes) < 2:
        return []

    edges = []
    for index, first in enumerate(nodes):
        for second in nodes[index + 1:]:
            distance = math.hypot(second.x - first.x, second.y - first.y)
            edges.append(Connection(first, second, distance, True))
    edges.sort(key=lambda edge: edge.distance)

    parent = {node.node_id: node.node_id for node in nodes}
    degree = {node.node_id: 0 for node in nodes}

    def find(node_id):
        while parent[node_id] != node_id:
            parent[node_id] = parent[parent[node_id]]
            node_id = parent[node_id]
        return node_id

    trunk = []
    for edge in edges:
        a_root, b_root = find(edge.a.node_id), find(edge.b.node_id)
        if a_root == b_root:
            continue
        if (degree[edge.a.node_id] >= cfg.MAX_CONNECTIONS_PER_NODE
                or degree[edge.b.node_id] >= cfg.MAX_CONNECTIONS_PER_NODE):
            continue
        trunk.append(edge)
        parent[a_root] = b_root
        degree[edge.a.node_id] += 1
        degree[edge.b.node_id] += 1
        if len(trunk) == len(nodes) - 1:
            break

    selected = list(trunk)
    trunk_pairs = {frozenset((edge.a.node_id, edge.b.node_id)) for edge in trunk}
    for edge in edges:
        pair = frozenset((edge.a.node_id, edge.b.node_id))
        if pair in trunk_pairs or edge.distance > cfg.CONNECTION_DISTANCE * 0.72:
            continue
        if (degree[edge.a.node_id] >= cfg.MAX_CONNECTIONS_PER_NODE
                or degree[edge.b.node_id] >= cfg.MAX_CONNECTIONS_PER_NODE):
            continue
        if _pair_affinity(edge.a.node_id, edge.b.node_id) > cfg.CONNECTION_DENSITY:
            continue
        branch = Connection(edge.a, edge.b, edge.distance, False)
        if _crosses(branch, selected):
            continue
        selected.append(branch)
        degree[edge.a.node_id] += 1
        degree[edge.b.node_id] += 1
    return selected


def bezier_points(connection, now: float, cfg):
    a, b = connection.a, connection.b
    dx, dy = b.x - a.x, b.y - a.y
    length = max(connection.distance, 1.0)
    nx, ny = -dy / length, dx / length
    pair_phase = a.node_id * 1.73 + b.node_id * 2.31
    living_shift = math.sin(pair_phase + now * cfg.CURVE_MOTION) * 0.18 + 0.82
    bend = length * cfg.CURVE_AMOUNT * math.sin(pair_phase) * living_shift
    if not connection.trunk:
        bend *= 1.35
    c1 = (a.x + dx * 0.31 + nx * bend, a.y + dy * 0.31 + ny * bend)
    c2 = (a.x + dx * 0.69 - nx * bend * 0.48, a.y + dy * 0.69 - ny * bend * 0.48)
    return (a.x, a.y), c1, c2, (b.x, b.y)
