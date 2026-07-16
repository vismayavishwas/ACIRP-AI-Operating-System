import os
import json
import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger("acirp.mem0")

MEM0_DB_FILE = os.path.join(os.path.dirname(__file__), "mem0_db.json")

class Mem0Manager:
    def __init__(self):
        self.api_key = os.getenv("MEM0_API_KEY")
        self.base_url = "https://api.mem0.ai/v1"
        self.use_cloud = bool(self.api_key)
        
        if self.use_cloud:
            logger.info("Mem0: Using cloud API key for memory storage.")
        else:
            logger.warning("Mem0: MEM0_API_KEY environment variable not found. Using local JSON memory fallback.")
            if not os.path.exists(MEM0_DB_FILE):
                self._write_local_db({})

    def _write_local_db(self, data: Dict[str, Any]):
        with open(MEM0_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _read_local_db(self) -> Dict[str, Any]:
        try:
            with open(MEM0_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def add_memory(self, content: str, user_id: str):
        """
        Adds a memory block for a specific complainant.
        """
        user_id = user_id or "anonymous_citizen"
        # Sanitize user_id to fit Mem0 requirement (alphanumeric, max length, etc.)
        sanitized_user_id = "".join(c for c in user_id if c.isalnum() or c in "-_").strip()
        if not sanitized_user_id:
            sanitized_user_id = "anonymous_citizen"

        if self.use_cloud:
            try:
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "user_id": sanitized_user_id
                }
                r = httpx.post(f"{self.base_url}/memories/", json=payload, headers=headers, timeout=10.0)
                if r.status_code in [200, 201]:
                    logger.info(f"Mem0 Cloud: Added memory for {sanitized_user_id}")
                else:
                    logger.error(f"Mem0 Cloud error: {r.status_code} - {r.text}")
            except Exception as e:
                logger.error(f"Failed to save to Mem0 Cloud: {e}")
        
        # Local fallback persistence
        data = self._read_local_db()
        if sanitized_user_id not in data:
            data[sanitized_user_id] = []
        data[sanitized_user_id].append({
            "content": content,
            "timestamp": "2026-07-16"
        })
        self._write_local_db(data)

    def search_memories(self, query: str, user_id: str) -> List[str]:
        """
        Retrieves matching memories for a specific complainant.
        """
        user_id = user_id or "anonymous_citizen"
        sanitized_user_id = "".join(c for c in user_id if c.isalnum() or c in "-_").strip()
        if not sanitized_user_id:
            sanitized_user_id = "anonymous_citizen"

        if self.use_cloud:
            try:
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "query": query,
                    "user_id": sanitized_user_id
                }
                r = httpx.post(f"{self.base_url}/memories/search/", json=payload, headers=headers, timeout=10.0)
                if r.status_code == 200:
                    mem_data = r.json()
                    results = []
                    # Standard cloud search format is list of memories
                    if isinstance(mem_data, list):
                        for item in mem_data:
                            if isinstance(item, dict) and "memory" in item:
                                results.append(item["memory"])
                            elif isinstance(item, dict) and "content" in item:
                                results.append(item["content"])
                    return results
            except Exception as e:
                logger.error(f"Failed to query Mem0 Cloud: {e}")

        # Local fallback search
        data = self._read_local_db()
        user_memories = data.get(sanitized_user_id, [])
        return [m["content"] for m in user_memories]
