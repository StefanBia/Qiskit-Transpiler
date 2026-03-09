
from typing import Any, Dict, List, Set, Tuple


class DAG:
    
    def __init__(self):
        self.nodes: Dict[Any, Any] = {}
        self.edges: Dict[Any, List[Any]] = {}
        self.qubits: Dict[Any, List[Any]] = {}
    
    def add_node(self, node_id: Any, data: Any = None, qubits: List[Any] = None) -> None:
        self.nodes[node_id] = data
        self.qubits[node_id] = qubits if qubits is not None else []
        if node_id not in self.edges:
            self.edges[node_id] = []
    
    def add_edge(self, source: Any, target: Any) -> None:

        if source not in self.nodes or target not in self.nodes:
            raise ValueError("Both source and target nodes must exist")
        
        # Check if adding this edge would create a cycle
        if self._would_create_cycle(source, target):
            raise ValueError("Adding this edge would create a cycle")
        
        self.edges[source].append(target)
    
    def _would_create_cycle(self, source: Any, target: Any) -> bool:
        return self._can_reach(target, source)
    
    def _can_reach(self, start: Any, goal: Any) -> bool:
        visited: Set[Any] = set()
        stack = [start]
        
        while stack:
            current = stack.pop()
            if current == goal:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.edges.get(current, []))
        
        return False
    
    def get_nodes(self) -> List[Any]:
        return list(self.nodes.keys())
    
    def get_edges(self) -> List[Tuple[Any, Any]]:
        edges = []
        for source, targets in self.edges.items():
            for target in targets:
                edges.append((source, target))
        return edges
    
    def get_successors(self, node_id: Any) -> List[Any]:
        return self.edges.get(node_id, [])
    
    def get_predecessors(self, node_id: Any) -> List[Any]:
        predecessors = []
        for source, targets in self.edges.items():
            if node_id in targets:
                predecessors.append(source)
        return predecessors
    

