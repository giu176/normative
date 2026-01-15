from __future__ import annotations

from typing import Callable, Dict

from app.providers import eurlex, iso, normattiva

ProviderModule = Dict[str, Callable[..., object]]


PROVIDERS: dict[str, object] = {
    "eurlex": eurlex,
    "normattiva": normattiva,
    "iso": iso,
}


def get_provider(name: str) -> object:
    provider = PROVIDERS.get(name.lower())
    if not provider:
        available = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")
    return provider
