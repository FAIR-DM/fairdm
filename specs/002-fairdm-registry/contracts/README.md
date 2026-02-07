# API Contracts - FairDM Registry System

This directory contains Python Protocol definitions specifying the exact API contracts for the registry system. These serve as:

1. **Type Hints**: Enable static type checking with mypy
2. **Documentation**: Complete method signatures with docstrings
3. **Contracts**: Expected behavior and return types
4. **Testing**: Interface compliance verification

## Files

- `registry.py` - FairDMRegistry Protocol with registration and introspection APIs
- `config.py` - ModelConfiguration Protocol with component access methods
- `factories.py` - ComponentFactory Protocol for generating components
- `exceptions.py` - Custom exception classes with type signatures

## Usage

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts.registry import FairDMRegistryProtocol
    from .contracts.config import ModelConfigurationProtocol

def my_function(registry: 'FairDMRegistryProtocol'):
    """Type-checked function using registry."""
    config = registry.get_for_model(RockSample)
    form_class = config.get_form_class()
```

## Type Checking

Run mypy to verify implementations match protocols:

```bash
poetry run mypy fairdm/registry/
```
