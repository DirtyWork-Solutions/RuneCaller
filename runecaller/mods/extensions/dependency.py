import networkx as nx
from bedrocked.reporting.reported import logger


class DependencyResolver:
    """
    Resolve and validate dependencies for modifications.
    Builds a dependency graph and detects conflicts or circular dependencies.
    """

    def __init__(self):
        # Directed graph: nodes are extensions; edges represent dependencies.
        self.graph = nx.DiGraph()

    def add_extension(self, extension):
        """
        Add an extension to the dependency graph.
        The extension must have attributes: name, version, and dependencies.
        """
        self.graph.add_node(extension.name, version=extension.version)
        for dep in extension.dependencies:
            self.graph.add_edge(extension.name, dep)

    def detect_conflicts(self):
        """
        Detect circular dependencies and return a list of issues found.
        """
        issues = []
        cycles = list(nx.simple_cycles(self.graph))
        if cycles:
            issues.append(f"Circular dependencies detected: {cycles}")
        # Additional version conflict checks can be added here.
        return issues

    def get_dependency_graph(self):
        """
        Return the internal dependency graph.
        """
        return self.graph
