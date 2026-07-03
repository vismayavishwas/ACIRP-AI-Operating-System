import os
import json
import math
import logging
from typing import List, Optional, Dict, Any
from models import Incident

logger = logging.getLogger("acirp.db")

# Try to import firebase_admin
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

DB_FILE = os.path.join(os.path.dirname(__file__), "incidents_db.json")

class MockDB:
    def __init__(self):
        self.use_firebase = False
        self.db = None
        self.bucket = None
        
        if not HAS_FIREBASE:
            logger.warning("firebase-admin package not installed. Using local JSON DB.")
            self._init_local_db()
            return

        # Check for serviceAccountKey.json
        key_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
        firebase_cred = None

        if os.path.exists(key_path):
            try:
                firebase_cred = credentials.Certificate(key_path)
                logger.info(f"Loaded Firebase credentials from file: {key_path}")
            except Exception as e:
                logger.error(f"Error loading credentials file: {e}")
        else:
            # Try to load from environment variables (useful on Render/production)
            cred_json_str = os.getenv("FIREBASE_CREDENTIALS")
            if cred_json_str:
                try:
                    cred_dict = json.loads(cred_json_str)
                    firebase_cred = credentials.Certificate(cred_dict)
                    logger.info("Loaded Firebase credentials from env var FIREBASE_CREDENTIALS")
                except Exception as e:
                    logger.error(f"Error parsing FIREBASE_CREDENTIALS env var: {e}")

        # If we have credentials, initialize Firebase
        if firebase_cred:
            try:
                project_id = os.getenv("FIREBASE_PROJECT_ID") or firebase_cred.project_id
                bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET") or f"{project_id}.appspot.com"
                
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(firebase_cred, {
                        'storageBucket': bucket_name
                    })
                
                self.db = firestore.client()
                self.collection = self.db.collection("incidents")
                self.bucket = storage.bucket()
                self.use_firebase = True
                logger.info(f"Successfully initialized Firebase (Project ID: {project_id}, Bucket: {bucket_name})")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin: {e}. Falling back to local DB.")
                self._init_local_db()
        else:
            logger.warning("No Firebase credentials found. Falling back to local JSON DB.")
            self._init_local_db()

    def _init_local_db(self):
        self.use_firebase = False
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
        if self.use_firebase:
            try:
                doc = self.collection.document(incident_id).get()
                if not doc.exists:
                    return None
                return Incident.model_validate(doc.to_dict())
            except Exception as e:
                logger.error(f"Firestore get_incident error: {e}")
                return None
        else:
            data = self._read_db()
            raw = data.get(incident_id)
            if not raw:
                return None
            return Incident.model_validate(raw)

    def save_incident(self, incident: Incident):
        if self.use_firebase:
            try:
                self.collection.document(incident.id).set(incident.model_dump())
            except Exception as e:
                logger.error(f"Firestore save_incident error: {e}")
        else:
            data = self._read_db()
            data[incident.id] = incident.model_dump()
            self._write_db(data)

    def list_incidents(self) -> List[Incident]:
        if self.use_firebase:
            try:
                docs = self.collection.stream()
                incidents = []
                for doc in docs:
                    try:
                        incidents.append(Incident.model_validate(doc.to_dict()))
                    except Exception as e:
                        logger.error(f"Error parsing doc {doc.id}: {e}")
                return incidents
            except Exception as e:
                logger.error(f"Firestore list_incidents error: {e}")
                return []
        else:
            data = self._read_db()
            return [Incident.model_validate(val) for val in data.values()]

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

    def upload_image(self, file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
        """
        Uploads image to Firebase Storage and returns the public URL.
        Falls back to None if Firebase is not active.
        """
        if not self.use_firebase or not self.bucket:
            return None
        try:
            blob = self.bucket.blob(f"images/{filename}")
            blob.upload_from_string(file_bytes, content_type=content_type)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Firebase Storage upload error: {e}")
            return None
