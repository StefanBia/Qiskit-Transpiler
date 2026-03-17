import random
from pprint import pprint

from QiskitTranspiler.transpiler.passes.layout.VF2 import VF2, Graph, find_subgraph_match
from QiskitTranspiler.transpiler.passes.layout.DAG import DAG
from QiskitTranspiler.transpiler.passes.layout.floyd_w import FloydWarshall
from qiskit import QuantumCircuit
import matplotlib.pyplot as plt
import networkx as nx 
from QiskitTranspiler.transpiler.passes.layout.sabre import sabre
from qiskit.transpiler import CouplingMap
from qiskit.providers.fake_provider import GenericBackendV2


class Layout:
    @staticmethod
    def draw_graph(graph):
        G = nx.Graph()
        # Add nodes with labels
        for node in graph.adj:
            G.add_node(str(node))  # networkx needs hashable nodes
        # Add edges
        for node, neighbors in graph.adj.items():
            for n in neighbors:
                G.add_edge(str(node), str(n))
        
        pos = nx.circular_layout(G)  # circular layout for qubits
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1000, font_size=12, font_weight='bold')
        plt.show()

    @staticmethod
    def run_layout(qc, backend):
        is_isomorphic, mapping = Layout.initial_isomorphism(qc, backend)
        if is_isomorphic:
            return mapping
        
        mapping = Layout.get_initial_mapping(Layout.circuit_to_DAG(qc), backend, qc)

        # We convert the initial mapping to a backend representation so we can apply floyd warshall on it
        nr_qubits = 0
        for qubit, mapped_qubit in mapping.items():
            nr_qubits  += 1

        coupling_list = []
        # Create inverse mapping for O(1) lookups: {physical_qubit: virtual_qubit}
        inverse_mapping = {v: k for k, v in mapping.items()}
        for x, y in backend.coupling_map:
            if x in inverse_mapping and y in inverse_mapping:
                coupling_list.append([inverse_mapping[x], inverse_mapping[y]])

        coupling_map = CouplingMap(couplinglist=coupling_list)
        backend_mapped_qubits = GenericBackendV2(
            num_qubits=nr_qubits,
            basis_gates=[], 
            coupling_map=coupling_map
        )

        fw_complex = FloydWarshall(backend_mapped_qubits)
        
        dag = Layout.circuit_to_DAG(qc)
        
        dist_matrix = fw_complex.dist

        # The front layer is the set of gates with no predecessors, stored as a list of node ids.
        front_layer = [node for node in dag.nodes if not dag.get_predecessors(node)]

        #----------------- With all input data, we can start SABRE
        sabre(front_layer=front_layer, coupling_map=backend.coupling_map, mapping=mapping, distrance_matrix=dist_matrix, dag=dag, fw=fw_complex)
        return mapping
    
    @staticmethod
    def initial_isomorphism(qc, backend):
        G1 = Graph()
        G2 = Graph()

        for i in range (backend.num_qubits):
            G2.add_node(i)
        
        for x, y in backend.coupling_map:
            G2.add_edge(x, y)
        # Add all qubits as nodes
        for q in qc.qubits:
            idx, _ = qc.find_bit(q)
            G1.add_node(idx)

        # Add edges for every 2-qubit gate
        for instrunction in qc.data:
            qargs = instrunction.qubits
            if len(qargs) == 2:  # two-qubit gate
                q0, q1 = qargs
                idx0, _ = qc.find_bit(q0)
                idx1, _ = qc.find_bit(q1)
                G1.add_edge(idx0, idx1)
        
        return find_subgraph_match(G1, G2)
    
    @staticmethod
    def circuit_to_DAG(circuit : QuantumCircuit) -> DAG:
        dag = DAG()
        last_gate_on_qubit = {}
        id_counter_two_qubit = 0
        id_counter_one_qubit = 0
        for instrunction in circuit.data:
            qargs = instrunction.qubits
            if len(qargs) == 2:  # two-qubit gate
                q0, q1 = qargs
                idx0, _ = circuit.find_bit(q0)
                idx1, _ = circuit.find_bit(q1)
                gate_id = f"g{id_counter_two_qubit}"
                id_counter_two_qubit += 1
                dag.add_node(gate_id, data=instrunction.operation, qubits=[idx0, idx1])
                
                # Add edges from last gates on these qubits to this gate
                if idx0 in last_gate_on_qubit:
                    dag.add_edge(last_gate_on_qubit[idx0], gate_id)
                if idx1 in last_gate_on_qubit:
                    dag.add_edge(last_gate_on_qubit[idx1], gate_id)
                
                # Update last gate on these qubits
                last_gate_on_qubit[idx0] = gate_id
                last_gate_on_qubit[idx1] = gate_id
            if len(qargs) == 1:  # single-qubit gate
                q0 = qargs[0]
                idx0, _ = circuit.find_bit(q0)
                gate_id = f"o{id_counter_one_qubit}"
                id_counter_one_qubit += 1
                dag.add_node(gate_id, data=instrunction.operation, qubits=[idx0])
                
                # Add edge from last gate on this qubit to this gate
                if idx0 in last_gate_on_qubit:
                    dag.add_edge(last_gate_on_qubit[idx0], gate_id)
                
                # Update last gate on this qubit
                last_gate_on_qubit[idx0] = gate_id
        
        return dag

    @staticmethod
    def get_initial_mapping(dag: DAG, backend, qc: QuantumCircuit):
        # Randomly assign first qubit, then use BFS to assign the rest based on connectivity
        # Mapping is of type {virtual_qubit: physical_qubit}
        # Ensures 1:1 mapping - no virtual qubits map to the same physical qubit
        random_initial_qubit = random.randint(0, backend.num_qubits - 1)
        mapping = {}
        mapping[0] = random_initial_qubit

        total_nodes_visited = 0
        visited = set()
        queue = [random_initial_qubit]  # Start BFS from the first qubit

        while queue and total_nodes_visited < qc.num_qubits:
            current_qubit = queue.pop(0)
            visited.add(current_qubit)
            mapping[total_nodes_visited] = current_qubit
            total_nodes_visited += 1

            # Find neighbors of the current qubit in the coupling map
            for edge in backend.coupling_map:
                if current_qubit in edge:
                    neighbor = edge[1] if edge[0] == current_qubit else edge[0]
                    if neighbor not in visited and neighbor not in queue:
                        queue.append(neighbor)

        # Validate 1:1 mapping constraint
        physical_qubits = list(mapping.values())
        assert len(physical_qubits) == len(set(physical_qubits)), "1:1 mapping constraint violated: duplicate physical qubits"
        
        return mapping
