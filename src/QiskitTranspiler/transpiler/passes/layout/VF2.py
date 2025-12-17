__all__ = ['Graph', 'find_subgraph_match']

class Graph:
    def __init__(self):
        self.adj = {}
        self.labels = {}

    def add_node(self, u, label=None):
        if u not in self.adj:
            self.adj[u] = set()
        self.labels[u] = label

    def add_edge(self, u, v):
        self.adj[u].add(v)
        self.adj[v].add(u)

    def neighbors(self, u):
        return self.adj[u]

class _VF2State:
    def __init__(self, G1, G2):
        self.G1 = G1
        self.G2 = G2
        self.M = {}
        self.M_inv = {}
        # T1/T2 contain nodes not in M/M_inv that are neighbors of nodes in M/M_inv
        self.T1 = set()    
        self.T2 = set()


class VF2:
    @staticmethod
    def match(G1, G2):
        """Public method to check if G1 is a subgraph of G2."""
        state = _VF2State(G1, G2)
        return VF2.vf2_match(state)

    @staticmethod
    def next_candidates(state):
        # Rule 1: If terminal sets are not empty, pick one u from T1 and all v from T2
        if state.T1 and state.T2:
            u = min(state.T1)
            for v in state.T2:
                yield u, v
        # Rule 2: If terminal sets are empty, pick u from G1 nodes not in M
        else:
            u = None
            for node in state.G1.adj:
                if node not in state.M:
                    u = node
                    break
            if u is not None:
                for v in state.G2.adj:
                    if v not in state.M_inv:
                        yield u, v

    @staticmethod
    def feasible(state, u, v):
        #V already mapped
        if v in state.M_inv: return False

        #Syntactic Check: Labels must match
        if state.G1.labels.get(u) != state.G2.labels.get(v): return False

        # Structural Check: neighbors of u already in M must map to neighbors of v
        for u_n in state.G1.neighbors(u):
            if u_n in state.M:
                if state.M[u_n] not in state.G2.neighbors(v):
                    return False

        # Subgraph Isomorphism Degree Check
        if len(state.G1.neighbors(u)) > len(state.G2.neighbors(v)):
            return False

        # Look-ahead: R_term
        t1_count = sum(1 for n in state.G1.neighbors(u) if n in state.T1)
        t2_count = sum(1 for n in state.G2.neighbors(v) if n in state.T2)
        if t1_count > t2_count: return False

        return True

    @staticmethod
    def add_pair(state, u, v):
        state.M[u] = v
        state.M_inv[v] = u
        
        # Save old terminal sets to restore them easily during backtrack
        old_T1 = set(state.T1)
        old_T2 = set(state.T2)

        # Update T1: Add neighbors of u not in M
        for n in state.G1.neighbors(u):
            if n not in state.M:
                state.T1.add(n)
        if u in state.T1: state.T1.remove(u)

        # Update T2: Add neighbors of v not in M_inv
        for n in state.G2.neighbors(v):
            if n not in state.M_inv:
                state.T2.add(n)
        if v in state.T2: state.T2.remove(v)

        return old_T1, old_T2

    @staticmethod
    def remove_pair(state, u, v, old_T1, old_T2):
        del state.M[u]
        del state.M_inv[v]
        state.T1 = old_T1
        state.T2 = old_T2

    @staticmethod
    def vf2_match(state):
        if len(state.M) == len(state.G1.adj):
            return True, dict(state.M)

        for u, v in VF2.next_candidates(state):
            if VF2.feasible(state, u, v):
                old_T1, old_T2 = VF2.add_pair(state, u, v)
                found, mapping = VF2.vf2_match(state)
                if found: return True, mapping
                VF2.remove_pair(state, u, v, old_T1, old_T2)

        return False, None


def find_subgraph_match(G1, G2):
    """
    Finds if G1 is a subgraph of G2 using the VF2 algorithm.
    Returns: (bool, mapping_dict or None)
    """
    state = _VF2State(G1, G2)
    return VF2.vf2_match(state)