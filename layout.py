from VF2 import VF2, Graph, find_subgraph_match
import matplotlib.pyplot as plt
import networkx as nx  # optional, easier layout


class Layout:
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

    def run_layout(qc, backend):
        graph = Graph()

        # Add all qubits as nodes
        for q in qc.qubits:
            graph.add_node(q, label=str(q))

        # Add edges for every 2-qubit gate
        for instr, qargs, cargs in qc.data:
            if len(qargs) == 2:  # two-qubit gate
                q0, q1 = qargs
                graph.add_edge(q0, q1)
