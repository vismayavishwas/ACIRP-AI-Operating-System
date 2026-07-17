import os
import importlib
import sys

# Ensure the parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

def test_config_defaults():
    # Test settings are loaded with correct defaults
    settings = config.Settings()
    assert settings.photo_confidence_threshold == 0.70
    assert settings.verification_threshold == 0.65
    assert settings.escalation_threshold == 0.85
    assert settings.monitor_sleep_interval_sec == 10
    assert settings.max_portal_retries == 3
    assert "garbage" in settings.default_routing
    assert "pothole" in settings.default_routing
    assert "fallen_tree" in settings.default_routing

def test_config_env_override(monkeypatch):
    # Test setting overrides via environment variables
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setenv("PHOTO_CONFIDENCE_THRESHOLD", "0.95")
    
    # Reload settings/config under mock env
    importlib.reload(config)
    
    assert config.settings.gemini_api_key == "test-key-123"
    
    # Clean up reload to reset normal module state
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("PHOTO_CONFIDENCE_THRESHOLD", raising=False)
    importlib.reload(config)
