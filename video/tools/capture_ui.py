#!/usr/bin/env python3
"""Capture crisp 1920x1080 real UI interaction stills for Remotion scenes."""

from __future__ import annotations

from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path("video/remotion/public/shots")
OUT_DIR.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8080"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT_DIR / "ui_01_pt102_hero.png"))

        cite = page.locator("button:has-text('EHR L'), button:has-text('Protocol L'), .citation-pill").first
        if cite.count() > 0:
            cite.click()
            page.wait_for_timeout(600)
        page.screenshot(path=str(OUT_DIR / "ui_02_citation_click.png"))

        swarm_tab = page.locator("[role='tab']:has-text('Swarm'), button:has-text('Swarm Board')").first
        if swarm_tab.count() > 0:
            swarm_tab.click()
            page.wait_for_timeout(600)
        page.screenshot(path=str(OUT_DIR / "ui_03_swarm_board.png"))

        signoff_btn = page.locator("button:has-text('Sign-Off'), button:has-text('Sign Off')").first
        if signoff_btn.count() > 0:
            signoff_btn.click()
            page.wait_for_timeout(600)
        page.screenshot(path=str(OUT_DIR / "ui_04_signoff_modal.png"))

        page.goto(f"{BASE}/judge", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT_DIR / "ui_05_judge_top.png"))

        page.evaluate("window.scrollTo(0, 560)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT_DIR / "ui_06_judge_scorecard.png"))

        browser.close()
    print("Captured UI stills:", sorted(p.name for p in OUT_DIR.glob("ui_*.png")))


if __name__ == "__main__":
    main()
