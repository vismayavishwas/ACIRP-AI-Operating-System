import os
import httpx
import logging
from playwright.async_api import async_playwright
from config import MAX_PORTAL_RETRIES

logger = logging.getLogger("acirp.portal")

async def submit_to_portal_hybrid(incident_data: dict, mode: str = "api") -> str:
    """
    Submits incident to the mock municipal portal.
    Supports two modes:
      - 'api': Direct REST request (fast, stable, works in cloud/headless environments)
      - 'playwright': Launches a browser, loads the portal page, types, and submits (great for video demos)
    """
    if mode == "playwright":
        try:
            return await submit_via_playwright(incident_data)
        except Exception as e:
            logger.warning(f"Playwright submission failed: {e}. Falling back to direct API submission.")
            # Fall back to API mode on failure
            return await submit_via_api(incident_data)
    else:
        return await submit_via_api(incident_data)

async def submit_via_api(incident_data: dict) -> str:
    """
    Direct API request to the mock municipal portal submission endpoint.
    """
    port = os.environ.get("PORT", "8000")
    url = f"http://127.0.0.1:{port}/api/mock-portal/submit"
    payload = {
        "incident_id": incident_data.get("id"),
        "issue_type": incident_data.get("issue_type"),
        "severity": incident_data.get("severity"),
        "latitude": incident_data.get("latitude"),
        "longitude": incident_data.get("longitude")
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=5.0)
        response.raise_for_status()
        res_json = response.json()
        token = res_json.get("complaint_token")
        if not token:
            raise ValueError("Portal response missing complaint_token")
        return token

async def submit_via_playwright(incident_data: dict) -> str:
    """
    Uses Playwright to automate filing the complaint on the mock portal webpage.
    Provides full retry/recovery mechanism.
    """
    port = os.environ.get("PORT", "8000")
    url = f"http://127.0.0.1:{port}/mock-portal"
    retries = 0
    
    while retries < MAX_PORTAL_RETRIES:
        try:
            async with async_playwright() as p:
                # Launch headless browser for background execution
                # Set headless=False to visually see it during local debugging
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Load the mock portal
                await page.goto(url, wait_until="networkidle", timeout=5000)
                
                # Fill in the form fields using selector targets
                await page.fill("#incident-id", incident_data.get("id"))
                await page.select_option("#issue-type", value=incident_data.get("issue_type", "garbage"))
                await page.fill("#latitude", str(incident_data.get("latitude", 0.0)))
                await page.fill("#longitude", str(incident_data.get("longitude", 0.0)))
                await page.select_option("#severity", value=incident_data.get("severity", "medium"))
                
                # Click submit
                await page.click("#submit-btn")
                
                # Wait for the token element to appear in the DOM
                await page.wait_for_selector("#complaint-token", state="attached", timeout=5000)
                token = await page.input_value("#complaint-token")
                
                await browser.close()
                return token
        except Exception as e:
            retries += 1
            logger.error(f"Playwright submission attempt {retries} failed: {e}")
            if retries >= MAX_PORTAL_RETRIES:
                raise e
