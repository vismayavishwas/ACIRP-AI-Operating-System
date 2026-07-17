from abc import ABC, abstractmethod
from typing import List, Optional
from models import Incident

class BaseDatabase(ABC):
    @abstractmethod
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Retrieve an incident by ID."""
        pass

    @abstractmethod
    def save_incident(self, incident: Incident) -> None:
        """Save/update an incident."""
        pass

    @abstractmethod
    def list_incidents(self) -> List[Incident]:
        """List all incidents."""
        pass

    @abstractmethod
    def upload_image(self, file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
        """Upload image and return public URL (or None if local JSON storage is active)."""
        pass

    @abstractmethod
    def find_nearby_resolved(self, lat: float, lon: float, issue_type: str, max_dist_meters: float = 500.0) -> List[Incident]:
        """Find nearby resolved cases of the same issue type."""
        pass
