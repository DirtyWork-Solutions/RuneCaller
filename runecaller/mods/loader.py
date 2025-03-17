import networkx as nx
import importlib

from bedrocked.reporting.reported import logger


def reload_expansion(expansion_module):
    """
    Dynamically reload an extension module.
    This allows updating the extension at runtime without restarting the application.
    """
    try:
        new_module = importlib.reload(expansion_module)
        logger.success(f"Expansion '{expansion_module.__name__}' reloaded successfully.")
        return new_module
    except Exception as e:
        logger.exception(f"Failed to reload expansion {expansion_module.__name__}: {e}")
        return None


class DependencyResolver:
    """
    Resolve and validate dependencies for modifications.
    Builds a dependency graph and detects conflicts or circular dependencies.
    """

    def __init__(self):
        # Directed graph: nodes are extensions; edges represent dependencies.
        self.graph = nx.DiGraph()

    def add_expansion(self, extension):
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


class RequirementsResolver:  # TODO: finish fork of dependency resolver
    """
    Resolve and validate requirements for modifications.
    Builds a dependency graph and detects conflicts or circular dependencies.
    """

    def __init__(self):
        # Directed graph: nodes are extensions; edges represent dependencies.
        self.graph = nx.DiGraph()

    def add_requirement(self, requirement):  # TODO: allow for
        """
        Add an extension to the dependency graph.
        The extension must have attributes: name, version, and dependencies.
        """
        self.graph.add_node(requirement.name, version=requirement.version)
        for dep in requirement.dependencies:
            self.graph.add_edge(requirement.name, dep)

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


