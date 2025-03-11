# RuneCaller

RuneCaller is the event, hook, and mods/extension project. It empowers developers to enhance and customize their
applications with a robust event handling system and modular extensions.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

RuneCaller is designed to integrate seamlessly with PyForged, providing an intuitive API for managing events, hooks, 
and mods/extensions. Whether you're building a new feature or enhancing an existing one, RuneCaller gives you the 
flexibility to respond to events and load custom modules dynamically.

---

## Features

- **Event Hooks:** Listen to and trigger events within the PyForged framework.
- **Modular Extensions:** Easily load, manage, and unload mods to extend functionality.
- **Customizable:** Configure events and hooks to fit your unique application needs.
- **Community-Driven:** Open-source and built with contributions from the community.

---

## Getting Started

### Prerequisites

- Python 3.13 or higher.
- An existing PyForged installation.

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/YourUsername/RuneCaller.git
2. Navigate to the Project Directory:
    ```bash
    cd RuneCaller
3. Install Dependencies:
    ```bash
    pip install -r requirements.txt

### Usage
Integrate RuneCaller into your PyForged project by importing the module and registering event hooks:

    ```python

    from runecaller import EventHook

    def on_custom_event(data):
        print("Custom event triggered with data:", data)

    # Register an event hook
    EventHook.register('custom_event', on_custom_event)

Load and manage mods/extensions dynamically with the ModManager:

    ```
    from runecaller import ModManager

    mod_manager = ModManager()
    mod_manager.load_mod("example_mod")

For more details and advanced usage, refer to the Documentation.

## Documentation
Detailed guides, API references, and examples are available in our documentation. Visit our Wiki for more information.

## Contributing
Contributions are welcome! To contribute:

- Fork the repository.
- Create a new branch for your feature or bugfix.
- Commit your changes and open a pull request.
- Follow the guidelines in our CONTRIBUTING.md. 
 
Please report any issues or suggestions via the repository's issue tracker.

## License
RuneCaller is distributed under the MIT License. See the [LICENSE.md](LICENSE.md) file for more details.

## Acknowledgements
 - PyForged Team: For creating a powerful framework that inspired this project.
 - Contributors: Thanks to everyone who has contributed ideas, code, and feedback to RuneCaller.
