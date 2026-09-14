"""Render the local web UI for repeatable visual review.

Run while ``reality web`` is listening on port 8000:
    .venv/bin/python scripts/visual_audit.py
"""

from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT = Path("/private/tmp/business-reality-ui-audit")
ROUTES = {
    "overview": "/app",
    "issues": "/issues",
    "commitments": "/commitments",
    "inventory": "/inventory",
    "documents": "/documents",
    "timeline": "/timeline",
    "open-items": "/finance/open-items",
    "payments": "/finance/payments",
    "journal": "/finance/journal",
    "parties": "/master/parties",
    "items": "/master/items",
    "locations": "/master/locations",
    "payment-terms": "/master/payment-terms",
    "pricing": "/master/pricing",
    "integrations": "/integrations",
    "chat": "/chat",
    "explorer": "/explorer",
    "documentation": "/documentation",
}


async def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    errors: list[str] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        desktop = await browser.new_context(viewport={"width": 1440, "height": 1000})
        page = await desktop.new_page()
        page.on(
            "console",
            lambda message: errors.append(f"{page.url} console: {message.text}")
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: errors.append(f"{page.url} page: {error}"))

        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page.screenshot(path=OUTPUT / "desktop-homepage.png", full_page=True)

        await page.goto(f"{BASE_URL}/app", wait_until="networkidle")
        commitment_href = await page.locator('a[href^="/commitments?tenant="]').first.get_attribute("href")
        if not commitment_href:
            raise RuntimeError("No active tenant found. Create a tenant before the visual audit.")
        tenant = parse_qs(urlparse(commitment_href).query)["tenant"][0]

        for name, route in ROUTES.items():
            await page.goto(f"{BASE_URL}{route}?tenant={tenant}", wait_until="networkidle")
            safe_name = re.sub(r"[^a-z0-9-]", "-", name)
            await page.screenshot(path=OUTPUT / f"desktop-{safe_name}.png", full_page=True)

        await page.goto(f"{BASE_URL}/issues?tenant={tenant}", wait_until="networkidle")
        review_button = page.get_by_role("button", name=re.compile("Review issue"))
        if await review_button.count():
            await review_button.first.click()
            await page.screenshot(path=OUTPUT / "desktop-issue-modal.png")

        await page.goto(f"{BASE_URL}/integrations?tenant={tenant}", wait_until="networkidle")
        add_source_button = page.get_by_role("button", name="Add source")
        if await add_source_button.count():
            await add_source_button.click()
            await page.screenshot(path=OUTPUT / "desktop-integration-modal.png")

        await page.goto(f"{BASE_URL}/documents?tenant={tenant}", wait_until="networkidle")
        detail_href = await page.locator('a[href^="/documents/"]').first.get_attribute("href")
        if detail_href:
            await page.goto(f"{BASE_URL}{detail_href}", wait_until="networkidle")
            await page.screenshot(path=OUTPUT / "desktop-document-detail.png", full_page=True)

        mobile = await browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = await mobile.new_page()
        await mobile_page.goto(f"{BASE_URL}/", wait_until="networkidle")
        await mobile_page.screenshot(path=OUTPUT / "mobile-homepage.png", full_page=True)
        for name, route in {"overview": "/app", "commitments": "/commitments", "document-detail": detail_href}.items():
            if not route:
                continue
            separator = "&" if "?" in route else "?"
            await mobile_page.goto(f"{BASE_URL}{route}{separator}tenant={tenant}", wait_until="networkidle")
            await mobile_page.screenshot(path=OUTPUT / f"mobile-{name}.png", full_page=True)

        await browser.close()

    (OUTPUT / "browser-errors.txt").write_text("\n".join(errors), encoding="utf-8")
    print(f"Rendered {len(list(OUTPUT.glob('*.png')))} screenshots to {OUTPUT}")
    print(f"Browser errors: {len(errors)}")


if __name__ == "__main__":
    asyncio.run(main())
