class FloydWarshall:
    
    def __init__(self, backend):

        self.backend = backend
        self.num_qubits = backend.num_qubits
        self.dist = None
        self.next_hop = None
        self._compute()
    
    def _compute(self):
        num_qubits = self.num_qubits
        
        self.dist = [[float('inf') for _ in range(num_qubits)] for _ in range(num_qubits)]
        self.next_hop = [[None for _ in range(num_qubits)] for _ in range(num_qubits)]
        
        for i in range(num_qubits):
            self.dist[i][i] = 0
            self.next_hop[i][i] = i
        
        for x, y in self.backend.coupling_map:
            self.dist[x][y] = 1
            self.dist[y][x] = 1
            self.next_hop[x][y] = y
            self.next_hop[y][x] = x
        
        for k in range(num_qubits):
            for i in range(num_qubits):
                if self.dist[i][k] == float('inf'):
                    continue
                for j in range(num_qubits):
                    if self.dist[k][j] == float('inf'):
                        continue
                    through_k = self.dist[i][k] + self.dist[k][j]
                    if through_k < self.dist[i][j]:
                        self.dist[i][j] = through_k
                        self.next_hop[i][j] = self.next_hop[i][k]
    
    def get_path(self, source, destination):

        if self.dist[source][destination] == float('inf'):
            return None
        
        path = [source]
        current = source
        
        while current != destination:
            next_node = self.next_hop[current][destination]
            if next_node is None:
                return None
            path.append(next_node)
            current = next_node
        
        return path
