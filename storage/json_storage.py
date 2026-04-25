import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from app.domain.models import Campaign


class JsonStorage:
    def save_campaign(self, campaign: Campaign, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                self._to_jsonable(campaign),
                file,
                ensure_ascii=False,
                indent=2,
            )

    def _to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            return self._to_jsonable(asdict(value))

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, dict):
            return {
                str(key): self._to_jsonable(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [self._to_jsonable(item) for item in value]

        return value