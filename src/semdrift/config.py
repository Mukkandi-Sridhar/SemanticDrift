"""Load study configurations and enforce explicit provider pins."""

import tomllib
from pathlib import Path
from typing import Any

from .data import ROOT


def load_config(path: Path | str) -> dict[str, Any]:
    path = Path(path).resolve()
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    with (path.parent / config.get("models_file", "models.toml")).open("rb") as stream:
        models = tomllib.load(stream)["models"]
    config["model_settings"] = {name: models[name] for name in config["models"]}
    config["root"] = ROOT
    return config


def check_pin(config: dict[str, Any], dry_run: bool = False) -> None:
    for model in config["model_settings"].values():
        if model["provider"] == "openrouter" and model.get("provider_pin", "").strip() in (
            "",
            "TODO",
        ):
            if not dry_run:
                raise ValueError("Set OpenRouter provider_pin before a real run or batch build")
