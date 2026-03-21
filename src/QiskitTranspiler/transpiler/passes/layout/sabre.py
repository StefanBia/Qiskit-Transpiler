from random import random

from QiskitTranspiler.transpiler.passes.layout.floyd_w import FloydWarshall


def sabre(front_layer, coupling_map, mapping, distrance_matrix, dag, fw: FloydWarshall):
    """SABRE heuristic search for qubit mapping.

    Args:
        front_layer (list): List of gates in the current front layer.
        coupling_map (CouplingMap): Coupling map of the target backend.
        mapping (Layout): Current mapping of virtual to physical qubits.
        trials (int): Number of random trials to perform for each candidate swap.
    Returns:
        swap (tuple): The best swap found, represented as a tuple of physical qubits.
    """
    print("Distance matrix:\n", distrance_matrix)

    resolved_gates = []
    layout = [i for i in range(len(mapping))]
    reverse_layout = [i for i in range(len(mapping))]
    swaps = []
    while front_layer:
        best_swap = None
        # print('\n-----------------------------------------------------------\n')
        # print('We enter the while loop, front_layer:', front_layer)
        execute_gate_list = []
        for node_id in front_layer:
            qargs = dag.qubits[node_id]
            if len(qargs) == 2:  # two-qubit gate
                idx0, idx1 = qargs

                # Check if the current mapping allows this gate to be executed
                # The distance matrix is indexed by virtual qubits, so we need to get the virtual qubits corresponding to the physical qubits in the current mapping
                if distrance_matrix[layout[idx0]][layout[idx1]] == 1:
                    execute_gate_list.append(node_id)
            else:  # single-qubit gate
                execute_gate_list.append(node_id)
        
        # print("Executable gates in front layer:", execute_gate_list)

        if execute_gate_list:
            for node_id in execute_gate_list:
                front_layer.remove(node_id)
                resolved_gates.append(node_id)
                for successor in dag.get_successors(node_id):
                    if all(pred in resolved_gates for pred in dag.get_predecessors(successor)):
                        front_layer.append(successor)
            continue  # Skip to the next iteration of the while loop to check for new executable gates
        else:
            score = {}
            for node_id in front_layer:
                qargs = dag.qubits[node_id]
                if len(qargs) == 2:  # two-qubit gate
                    idx0, idx1 = qargs
                    score[node_id] = distrance_matrix[layout[idx0]][layout[idx1]]

            min_score_nodes = [node_id for node_id, s in score.items() if s == min(score.values())]
        
            best_swap = min_score_nodes[0]
            
            idx0, idx1 = dag.qubits[best_swap]
            # print("Node with minimum score:", best_swap)

            min_path = fw.get_path(layout[idx0], layout[idx1])
            # print("Shortest path between qubits", idx0, "and", idx1, ":", min_path)

            # print("layout before swaps:", layout)
            # print("reverse_layout before swaps:", reverse_layout)

            for i in range(len(min_path) - 2):
                p0, p1 = min_path[i], min_path[i + 1]
                v0 = reverse_layout[p0]
                v1 = reverse_layout[p1]
                # print(f"i={i}: p0={p0}, p1={p1}, v0={v0}, v1={v1}")

                swaps.append((best_swap, (v0, v1)))
                layout[v0], layout[v1] = layout[v1], layout[v0]
                reverse_layout[p0], reverse_layout[p1] = reverse_layout[p1], reverse_layout[p0]
                # print("Performing swap:", (v0, v1))
                # print("layout:", layout)
                # print("reverse_layout:", reverse_layout)

            # this should be 1 after the swaps
            # print("New distance between qubits", idx0, "and", idx1, "after swaps:", distrance_matrix[layout[idx0]][layout[idx1]])

    # print("Done yuppie\n")     

    return swaps, resolved_gates