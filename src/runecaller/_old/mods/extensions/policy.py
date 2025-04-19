from bedrocked.reporting.reported import logger



class PolicyEngine:
    """
    A simple policy engine to enforce dynamic policies for modifications.
    Policies are functions that accept an extension and return True (compliant) or False.
    """

    def __init__(self):
        self.policies = []  # Registered policy functions

    def register_policy(self, policy_fn):
        """
        Register a new policy function.
        """
        self.policies.append(policy_fn)

    def enforce_policies(self, extension) -> bool:
        """
        Check if an extension complies with all registered policies.
        """
        for policy in self.policies:
            if not policy(extension):
                logger.warning(f"Extension {extension.name} failed policy {policy.__name__}")
                return False
        return True
