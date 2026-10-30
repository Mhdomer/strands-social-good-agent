"""Automated UI screenshot and video recording capture script for Nafas (نَفَس).

Uses Playwright to interact with the live web dashboard, execute scenarios,
capture high-resolution screenshots, and record an MP4 walkthrough video.
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright


SCREENSHOTS_DIR = Path("docs/images")
VIDEOS_DIR = Path("docs/videos")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    # 1. Start UI server in background subprocess if not running
    server_process = subprocess.Popen(
        [".venv/bin/python", "-m", "nafas.ui.server"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)  # Wait for server to bind port 8000

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1366, "height": 850},
                record_video_dir=str(VIDEOS_DIR),
                record_video_size={"width": 1280, "height": 720},
            )
            page = await context.new_page()

            print("Navigating to http://localhost:8000...")
            await page.goto("http://localhost:8000")
            await page.wait_for_timeout(1000)

            # 1. Capture Dashboard Overview (Arabic)
            print("Capturing 01_dashboard_overview.png...")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "01_dashboard_overview.png"))

            # 2. Trigger Scenario 1: Riyadh Heatwave Worker
            print("Simulating Scenario 1 (Riyadh Heatwave)...")
            await page.click('button[onclick="runPreset(1)"]')
            try:
                await page.wait_for_selector("#active-loading-row", state="detached", timeout=45000)
            except Exception as e:
                print(f"Warning on scenario 1 wait: {e}")
                await page.wait_for_timeout(10000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "02_heatwave_worker.png"))

            # 3. Trigger Scenario 2: Asthmatic Child Brufen Check
            print("Simulating Scenario 2 (Asthmatic Child Brufen Check)...")
            await page.reload()
            await page.wait_for_timeout(1000)
            await page.click('button[onclick="runPreset(2)"]')
            try:
                await page.wait_for_selector("#active-loading-row", state="detached", timeout=45000)
            except Exception as e:
                print(f"Warning on scenario 2 wait: {e}")
                await page.wait_for_timeout(10000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "03_contraindication_interception.png"))

            # 4. Trigger Scenario 3: Emergency Cyanosis Dispatch
            print("Simulating Scenario 3 (Cyanosis Red-Flag Alarm)...")
            await page.reload()
            await page.wait_for_timeout(1000)
            await page.click('button[onclick="runPreset(3)"]')
            try:
                await page.wait_for_selector("#active-loading-row", state="detached", timeout=15000)
            except Exception as e:
                print(f"Warning on scenario 3 wait: {e}")
                await page.wait_for_timeout(3000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "04_emergency_cyanosis_dispatch.png"))

            # 5. Switch to English and capture English Mode Overview
            print("Switching to English Mode...")
            await page.reload()
            await page.wait_for_timeout(800)
            await page.click("#lang-btn")
            await page.wait_for_timeout(1000)
            print("Capturing 05_english_dashboard_view.png...")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "05_english_dashboard_view.png"))

            await page.wait_for_timeout(1500)
            await context.close()
            await browser.close()
            print("Playwright session complete.")

        # Convert webm video to mp4 using ffmpeg
        video_files = list(VIDEOS_DIR.glob("*.webm"))
        if video_files:
            latest_video = max(video_files, key=os.path.getctime)
            output_mp4 = VIDEOS_DIR / "nafas_demo_walkthrough.mp4"
            print(f"Converting {latest_video} to {output_mp4} via ffmpeg...")
            subprocess.run([
                "ffmpeg", "-y", "-i", str(latest_video),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", "30", str(output_mp4)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"MP4 demo video generated successfully: {output_mp4}")

    finally:
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    asyncio.run(main())
