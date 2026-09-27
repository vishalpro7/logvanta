from datetime import datetime
from typing import Any


class MappingRegistry:

    def __init__(self):
        self._versions: dict[str, list[dict[str, Any]]] = {}

    def create_version(
        self,
        source: str,
        mappings: list[dict[str, Any]],
        confidence: float,
        status: str = "candidate",
    ) -> dict[str, Any]:

        versions = self._versions.setdefault(source, [])

        version_number = len(versions) + 1

        version = {
            "source": source,
            "version": version_number,
            "mappings": mappings,
            "confidence": confidence,
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
        }

        versions.append(version)

        return version

    def get_versions(self, source: str) -> list[dict[str, Any]]:
        return self._versions.get(source, [])

    def get_active_version(self, source: str):
        versions = self._versions.get(source, [])

        for version in reversed(versions):
            if version["status"] == "active":
                return version

        return None

    def activate_version(
        self,
        source: str,
        version_number: int,
    ) -> dict[str, Any]:

        versions = self._versions.get(source, [])

        target = None

        for version in versions:
            if version["version"] == version_number:
                target = version
            else:
                version["status"] = "archived"

        if target is None:
            raise ValueError(
                f"Version {version_number} not found for {source}"
            )

        target["status"] = "active"

        return target


mapping_registry = MappingRegistry()