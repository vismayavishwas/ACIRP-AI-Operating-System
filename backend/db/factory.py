import os
import logging
from db.base import BaseDatabase
from db.json_db import JSONDatabase
from db.firebase_db import FirebaseDatabase, comp_id_context

logger = logging.getLogger("acirp.db.factory")

def get_db() -> BaseDatabase:
    # Read DB_PROVIDER from environment (if set) or fallback to config settings, defaulting to "json"
    from config import settings
    provider = os.getenv("DB_PROVIDER", settings.db_provider).lower()
    
    if provider == "firebase":
        from db.firebase_db import HAS_FIREBASE
        if HAS_FIREBASE:
            logger.info("Database Factory: Instantiating FirebaseDatabase")
            return FirebaseDatabase()
        else:
            logger.warning("Database Factory: Firebase is configured but libraries are missing. Falling back to JSONDatabase.")
            return JSONDatabase()
    
    logger.info("Database Factory: Instantiating JSONDatabase")
    return JSONDatabase()
