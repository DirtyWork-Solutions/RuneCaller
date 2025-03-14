from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ExtensionMetadata:
    name: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    author: str = ''
    description: str = ''
    # Additional fields such as compatibility and state can be added.
    state: str = 'inactive'  # or 'active'
    config: Dict[str, any] = field(default_factory=dict)
