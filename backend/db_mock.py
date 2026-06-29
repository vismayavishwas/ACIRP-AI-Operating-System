import os
import json
import math
from typing import List, Optional, Dict, Any
from models import Incident

DB_FILE = os.path.join(os.path.dirname(__file__), "incidents_db.json")

class MockDB:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._write_db({})
            
    def _read_db(self) -> Dict[str, Any]:
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_db(self, data: Dict[str, Any]):
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        data = self._read_db()
        raw = data.get(incident_id)
        if not raw:
            return None
        return Incident.model_validate(raw)

    def save_incident(self, incident: Incident):
        data = self._read_db()
        data[incident.id] = incident.model_dump()
        self._write_db(data)

    def list_incidents(self) -> List[Incident]:
        data = self._read_db()
        return [Incident.model_validate(val) for val in data.values()]

    def find_nearby_resolved(self, lat: float, lon: float, issue_type: str, max_dist_meters: float = 500.0) -> List[Incident]:
        """
        Uses the Haversine formula to find nearby resolved incidents of the same type.
        """
        resolved = []
        for inc in self.list_incidents():
            if inc.status == "CLOSED" and inc.issue_type == issue_type:
                dist = self._haversine(lat, lon, inc.latitude, inc.longitude)
                if dist <= max_dist_meters:
                    resolved.append(inc)
        return resolved

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # Distance in meters
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c
