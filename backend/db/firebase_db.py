import os
import math
import logging
from typing import List, Optional
from models import Incident
from db.base import BaseDatabase
from contextvars import ContextVar

logger = logging.getLogger("acirp.db.firebase")

# ContextVar to track the active competition database context dynamically per request
comp_id_context = ContextVar("comp_id", default="google")

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

class FirebaseDatabase(BaseDatabase):
    def __init__(self):
        self.apps = {}
        self.db_clients = {}
        self.buckets = {}
        
        if not HAS_FIREBASE:
            logger.warning("firebase-admin package not installed. FirebaseDatabase is disabled.")
            return

        # 1. Initialize GOOGLE Firebase App
        google_cred = self._load_credentials("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
        if google_cred:
            try:
                proj_id = os.getenv("FIREBASE_PROJECT_ID") or google_cred.project_id
                bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET") or f"{proj_id}.appspot.com"
                
                # Check if default app is already initialized
                if not firebase_admin._apps:
                    app = firebase_admin.initialize_app(google_cred, {
                        'storageBucket': bucket_name
                    })
                else:
                    app = firebase_admin.get_app()
                
                self.apps["google"] = app
                self.db_clients["google"] = firestore.client(app=app)
                self.buckets["google"] = storage.bucket(app=app)
                logger.info(f"Initialized Google Firebase (Project ID: {proj_id})")
            except Exception as e:
                logger.error(f"Failed to initialize Google Firebase: {e}")

        # 2. Initialize UNSTOP Firebase App
        unstop_cred = self._load_credentials("FIREBASE_CREDENTIALS_UNSTOP", "serviceAccountKey_unstop.json")
        if unstop_cred:
            try:
                proj_id = os.getenv("FIREBASE_PROJECT_ID_UNSTOP") or unstop_cred.project_id
                bucket_name = f"{proj_id}.appspot.com"
                
                # Use a named app for Unstop to avoid name collision
                app = firebase_admin.initialize_app(unstop_cred, {
                    'storageBucket': bucket_name
                }, name="unstop")
                
                self.apps["unstop"] = app
                self.db_clients["unstop"] = firestore.client(app=app)
                self.buckets["unstop"] = storage.bucket(app=app)
                logger.info(f"Initialized Unstop Firebase (Project ID: {proj_id})")
            except Exception as e:
                logger.error(f"Failed to initialize Unstop Firebase: {e}")

    def _load_credentials(self, env_var: str, file_name: str):
        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_name)
        if os.path.exists(key_path):
            try:
                return credentials.Certificate(key_path)
            except Exception as e:
                logger.error(f"Error loading credentials file {file_name}: {e}")
        else:
            import json
            cred_json_str = os.getenv(env_var)
            if cred_json_str:
                try:
                    cred_dict = json.loads(cred_json_str)
                    return credentials.Certificate(cred_dict)
                except Exception as e:
                    logger.error(f"Error parsing {env_var} env var: {e}")
        return None

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        comp_id = comp_id_context.get()
        if comp_id in self.db_clients:
            try:
                doc = self.db_clients[comp_id].collection("incidents").document(incident_id).get()
                if not doc.exists:
                    return None
                return Incident.model_validate(doc.to_dict())
            except Exception as e:
                logger.error(f"Firestore get_incident error for {comp_id}: {e}")
                return None
        return None

    def save_incident(self, incident: Incident) -> None:
        comp_id = comp_id_context.get()
        if comp_id in self.db_clients:
            try:
                self.db_clients[comp_id].collection("incidents").document(incident.id).set(incident.model_dump())
            except Exception as e:
                logger.error(f"Firestore save_incident error for {comp_id}: {e}")

    def list_incidents(self) -> List[Incident]:
        comp_id = comp_id_context.get()
        if comp_id in self.db_clients:
            try:
                docs = self.db_clients[comp_id].collection("incidents").stream()
                incidents = []
                for doc in docs:
                    try:
                        incidents.append(Incident.model_validate(doc.to_dict()))
                    except Exception as e:
                        logger.error(f"Error parsing doc {doc.id} for {comp_id}: {e}")
                return incidents
            except Exception as e:
                logger.error(f"Firestore list_incidents error for {comp_id}: {e}")
                return []
        return []

    def upload_image(self, file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
        comp_id = comp_id_context.get()
        if comp_id not in self.buckets:
            return None
        try:
            blob = self.buckets[comp_id].blob(f"images/{filename}")
            blob.upload_from_string(file_bytes, content_type=content_type)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Firebase Storage upload error for {comp_id}: {e}")
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
