import networkx as nx
import matplotlib.pyplot as plt

def visualize_dependency_graph(graph):
    """
    Visualize the dependency graph using matplotlib.
    """
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_color='lightblue',
            edge_color='gray', node_size=1500, font_size=10)
    plt.title("Dependency Graph")
    plt.show()
