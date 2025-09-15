from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional


class RelationsGraph:
    """Simple container/location relations.

    Maintains a mapping of entity_id -> container_id and container_id -> contents list.
    MVP: no capacity/constraints; atomic updates; idempotent operations.
    """

    def __init__(self) -> None:
        self._container_of: Dict[str, Optional[str]] = {}
        self._contents_of: Dict[str, List[str]] = defaultdict(list)

    def get_container_of(self, entity_id: str) -> Optional[str]:
        return self._container_of.get(entity_id)

    def get_contents_of(self, container_id: str) -> List[str]:
        return list(self._contents_of.get(container_id, []))

    def place_entity(self, entity_id: str, container_id: str) -> None:
        # Remove from previous container if exists
        prev = self._container_of.get(entity_id)
        if prev is not None:
            try:
                self._contents_of[prev].remove(entity_id)
            except ValueError:
                pass

        # Place into new container
        self._container_of[entity_id] = container_id
        if entity_id not in self._contents_of[container_id]:
            self._contents_of[container_id].append(entity_id)

    def move_entity(self, entity_id: str, new_container_id: str) -> None:
        self.place_entity(entity_id=entity_id, container_id=new_container_id)


