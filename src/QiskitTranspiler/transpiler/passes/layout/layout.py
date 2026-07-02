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

"""
layout.py

Layout and routing pass.

Assigns logical qubits to physical qubits on the target backend and
inserts SWAP gates where needed to satisfy hardware connectivity
constraints.

Two-stage strategy:
    1. Attempt a direct embedding via VF2 subgraph isomorphism between
       the circuit's interaction graph and the backend's coupling map.
    2. If no direct match is found, compute a noise-aware initial
       mapping (BFS-based error scoring over readout and two-qubit
       gate errors) and route with the SABRE algorithm, inserting
       SWAP gates to satisfy adjacency constraints.

Returns the physical circuit along with the resulting logical-to-
physical qubit mapping.
"""


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
        """Run the layout and routing pass on the given circuit for the specified backend.
           Main entry point for the layout pass. Returns the routed circuit and the final mapping."""

        is_isomorphic, mapping = Layout.initial_isomorphism(qc, backend)
        if is_isomorphic:
            return qc, mapping  # No layout needed, return original circuit and mapping
        
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
        swaps, ordered_ex_gates = sabre(front_layer=front_layer, coupling_map=backend.coupling_map, mapping=mapping, distrance_matrix=dist_matrix, dag=dag, fw=fw_complex)
        

        circuit = Layout.dag_to_circuit(dag, ordered_ex_gates, swaps)

        circuit = Layout.direction_fix(circuit, backend.coupling_map)

        return circuit, mapping
    
    @staticmethod
    def initial_isomorphism(qc, backend):
        """Check if the circuit's interaction graph is isomorphic to the backend's coupling map.
           If so, return True and the mapping; otherwise, return False and an empty mapping."""
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
        """Convert a QuantumCircuit to a DAG representation."""
        dag = DAG()
        last_gate_on_qubit = {}
        id_counter_two_qubit = 0
        id_counter_one_qubit = 0
        for instrunction in circuit.data:
            qargs = instrunction.qubits
            cargs = instrunction.clbits
            if len(qargs) == 2:  # two-qubit gate
                q0, q1 = qargs
                idx0, _ = circuit.find_bit(q0)
                idx1, _ = circuit.find_bit(q1)
                gate_id = f"g{id_counter_two_qubit}"
                id_counter_two_qubit += 1

                cbits = [circuit.find_bit(cbit).index for cbit in instrunction.clbits]

                dag.add_node(gate_id, data=instrunction.operation, qubits=[idx0, idx1], classical_bits=cbits)
                
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
                cbits = [circuit.find_bit(cbit).index for cbit in instrunction.clbits]
                dag.add_node(gate_id, data=instrunction.operation, qubits=[idx0], classical_bits=cbits)

                # Add edge from last gate on this qubit to this gate
                if idx0 in last_gate_on_qubit:
                    dag.add_edge(last_gate_on_qubit[idx0], gate_id)
                
                # Update last gate on this qubit
                last_gate_on_qubit[idx0] = gate_id
        
        return dag

    @staticmethod
    def get_initial_mapping(dag: DAG, backend, qc: QuantumCircuit):
        """Compute an initial mapping of virtual qubits to physical qubits based on BFS traversal of the backend's coupling map.
           Returns a mapping dictionary {virtual_qubit: physical_qubit}."""

        # Assign best starting qubit, then use BFS to assign the rest based on connectivity
        # Mapping is of type {virtual_qubit: physical_qubit}
        # Ensures no virtual qubits map to the same physical qubit
        starting_qubit = Layout.compute_best_starting_qubit(backend)
        mapping = {}
        mapping[0] = starting_qubit

        total_nodes_visited = 0
        visited = set()
        queue = [starting_qubit]  # Start BFS from the first qubit

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

    @staticmethod
    def dag_to_circuit(dag: DAG, ordered_ex_gates: list, swaps: list) -> QuantumCircuit:
        """Convert a DAG representation back to a QuantumCircuit, applying the ordered execution of gates and swaps."""

        num_qubits = max(qubit for qubits in dag.qubits.values() for qubit in qubits) + 1
        num_clbits = max(clbit for clbits in dag.classical_bits.values() for clbit in clbits) + 1
        vmap = [i for i in range(num_qubits)]
        circuit = QuantumCircuit(num_qubits, num_clbits)

        # for node_id in ordered_ex_gates:
        #     print(f"Node: {node_id}, Qubits: {dag.qubits[node_id]}, Classical Bits: {dag.classical_bits[node_id]}, Data: {dag.nodes[node_id]}")

        for node_id in ordered_ex_gates:
            gate_data = dag.nodes[node_id]
            needed_swaps = [swap for swap in swaps if swap[0] == node_id]
            for swap in needed_swaps:
                (v0, v1) = swap[1]
                circuit.cx(vmap[v0], vmap[v1])
                circuit.cx(vmap[v1], vmap[v0])
                circuit.cx(vmap[v0], vmap[v1])
                # update vmap to reflect the swap
                vmap[v0], vmap[v1] = vmap[v1], vmap[v0]
        
            # print(f"Nodeid: {node_id}")
            qubits = dag.qubits[node_id]
            clbits = dag.classical_bits[node_id]
            if gate_data is not None:
                # remap qubits through vmap to get current physical locations
                remapped_qubits = [vmap[q] for q in qubits]
                circuit.append(gate_data, remapped_qubits, clbits)
                # print(f"Operation: {gate_data}, Qubits: {remapped_qubits}, Classical bits: {clbits}")

        return circuit

    def direction_fix(circuit, coupling_map):
        """Fix the direction of CNOT gates in the circuit to match the backend's coupling map.
           If a CNOT gate is in the wrong direction, it is replaced with an equivalent sequence of gates."""

        direction_fixed_qc = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
        for instruction in circuit.data:
            op = instruction.operation
            qubits = [circuit.find_bit(qubit).index for qubit in instruction.qubits]
            cbits = [circuit.find_bit(cbit).index for cbit in instruction.clbits]
            if op.name == "cx":
                q1, q2 = qubits[0], qubits[1]
                if (q1, q2) not in coupling_map and (q2, q1) in coupling_map:
                    direction_fixed_qc.h(q1)
                    direction_fixed_qc.h(q2)
                    direction_fixed_qc.cx(q2, q1)
                    direction_fixed_qc.h(q1)
                    direction_fixed_qc.h(q2)
                else:
                    direction_fixed_qc.append(op, qubits, cbits)
            else:
                direction_fixed_qc.append(op, qubits, cbits)
        
        return direction_fixed_qc

    def compute_best_starting_qubit(backend):
        """Compute the best starting qubit for the initial mapping based on a BFS traversal of the backend's coupling map. (Heuristic approach)
           The qubit with the highest score (lowest error) is selected as the starting point."""

        coupling_map = backend.coupling_map
        two_qubit_gate = 'ecr' if 'ecr' in backend.operation_names else 'cz'

        error_map = {}
        for edge in coupling_map.get_edges():
            error_map[edge] = backend.target[two_qubit_gate][edge].error

        qubit_scores = {i: 1.0 for i in range(backend.num_qubits)}

        for edge, error in error_map.items():
            qubit_scores[edge[0]] *= (1 - error)
            qubit_scores[edge[1]] *= (1 - error)


        for i in range(backend.num_qubits):
            qubit_props = backend.properties().qubit_property(i)
            readout_error = qubit_props.get("readout_error", (None,))[0]
            qubit_scores[i] *= (1 - readout_error)
            qubit_scores[i] *= Layout.bfs_sum_error_depth(i, coupling_map, depth=2, qubit_scores=qubit_scores)

        highest_score_qubit = max(qubit_scores, key=qubit_scores.get)
        return highest_score_qubit


    def bfs_sum_error_depth(start, coupling_map, depth, qubit_scores):
        """Perform a BFS traversal of the coupling map starting from the given qubit, summing the error scores of neighboring qubits up to the specified depth.
           Returns the cumulative score for the starting qubit based on its neighbors' error rates."""

        visited = set()
        queue = [(start, 0)]  # (node, current_depth)
        area_score = 1

        while queue:
            node, current_depth = queue.pop(0)
            if node not in visited and current_depth <= depth:
                visited.add(node)
                area_score *= qubit_scores[node]
                
                neighbor_indices = [n for n in coupling_map.neighbors(node)]

                for neighbor in neighbor_indices:
                    queue.append((neighbor, current_depth + 1))
        
        
        
        return area_score