from bedrocked.reporting.reported import logger

class LifecycleManager:
    def __init__(self):
        self.components = []

    def register_component(self, component):
        """
        Register a component that implements start() and shutdown() methods.
        """
        self.components.append(component)
        logger.info(f"Registered component: {component.__class__.__name__}")

    def start(self):
        """
        Start all registered components.
        """
        logger.info("Starting all components...")
        for component in self.components:
            try:
                component.start()
                logger.success(f"Started: {component.__class__.__name__}")
            except Exception as e:
                logger.exception(f"Failed to start {component.__class__.__name__}: {e}")

    def shutdown(self):
        """
        Shutdown all registered components.
        """
        logger.info("Shutting down all components...")
        for component in self.components:
            try:
                component.shutdown()
                logger.success(f"Shutdown: {component.__class__.__name__}")
            except Exception as e:
                logger.exception(f"Failed to shutdown {component.__class__.__name__}: {e}")


if __name__ == '__main__':
    # Example component interface:
    class ComponentInterface:
        def start(self):
            logger.debug("started component")
            logger.error("Not implemented yet")

        def shutdown(self):
            logger.warning("Not implemented yet.")

    test = ComponentInterface()
    manager = LifecycleManager()
    manager.register_component(test)
    manager.start()
    manager.shutdown()