from typing import Dict, Type
from .base import BaseFareAdapter

ADAPTER_REGISTRY: Dict[str, Type[BaseFareAdapter]] = {}

def register_adapter(name: str):
    def decorator(cls: Type[BaseFareAdapter]):
        ADAPTER_REGISTRY[name] = cls
        return cls
    return decorator

def get_adapter(name: str) -> Type[BaseFareAdapter]:
    if name not in ADAPTER_REGISTRY:
        raise ValueError(f"No adapter registered for {name}")
    return ADAPTER_REGISTRY[name]
