import os
import json
import math
from typing import List, Optional, Dict, Any
from models import Incident
from db.base import BaseDatabase

# Target incidents_db.json in parent directory (backend/)
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "incidents_db.json")

class JSONDatabase(BaseDatabase):
    def __init__(self, db_file_override: Optional[str] = None):
        self.db_file = db_file_override or DB_FILE
        if not os.path.exists(self.db_file):
            self._write_db({})

    def _read_db(self) -> Dict[str, Any]:
        try:
            with open(self.db_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_db(self, data: Dict[str, Any]):
        with open(self.db_file, "w") as f:
            json.dump(data, f, indent=4)

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        data = self._read_db()
        raw = data.get(incident_id)
        if not raw:
            return None
        return Incident.model_validate(raw)

    def save_incident(self, incident: Incident) -> None:
        data = self._read_db()
        data[incident.id] = incident.model_dump()
        self._write_db(data)

    def list_incidents(self) -> List[Incident]:
        data = self._read_db()
        return [Incident.model_validate(val) for val in data.values()]

    def upload_image(self, file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
        # JSON database does not support cloud uploads, returns None to trigger local static backup url path
        return None

    def find_nearby_resolved(self, lat: float, lon: float, issue_type: str, max_dist_meters: float = 500.0) -> List[Incident]:
        resolved = []
        for inc in self.list_incidents():
            if inc.status == "CLOSED" and inc.issue_type == issue_type:
                dist = self._haversine(lat, lon, inc.latitude, inc.longitude)
                if dist <= max_dist_meters:
                    resolved.append(inc)
        return resolved

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c
