"""conftest.py — pytest-html report customisation and logging setup."""

from __future__ import annotations

import base64
import datetime
import logging
import platform
import sys
from pathlib import Path

import pytest

# ── Logging configuration ─────────────────────────────────────────────────────
# Do NOT call logging.basicConfig() here — pytest manages its own log handlers.
# Log level and format are controlled via --log-cli-level in reporter_agent.py.
# This prevents duplicate log entries in the HTML report.
logger = logging.getLogger(__name__)


# ── Environment table shown at top of report ──────────────────────────────────

def pytest_configure(config):
    config._metadata = {
        "Project": "Mobile Test Generator — Capstone",
        "Platform": platform.system() + " " + platform.release(),
        "Python": sys.version.split()[0],
        "Appium Server": "http://127.0.0.1:4723",
        "App Package": "com.saucelabs.mydemoapp.android",
        "Run Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ── Report title ──────────────────────────────────────────────────────────────

@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report):
    report.title = "Appium Test Execution Report — Mobile Test Generator"


# ── Custom CSS injected into the self-contained HTML ─────────────────────────

@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([
        "<style>"
        "body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; color: #2c3e50; }"
        "h1 { background: #2c3e50; color: #fff; padding: 16px 24px; border-radius: 6px; }"
        "#environment td, #environment th { padding: 8px 14px; border: 1px solid #dce1e7; }"
        "#environment th { background: #34495e; color: #fff; }"
        "#environment tr:nth-child(even) { background: #eaf0fb; }"
        ".passed  { color: #27ae60; font-weight: bold; }"
        ".failed  { color: #e74c3c; font-weight: bold; }"
        ".error   { color: #e67e22; font-weight: bold; }"
        "td.col-name { font-family: monospace; font-size: 0.9em; }"
        "td.col-duration { color: #7f8c8d; }"
        ".summary-passes  { background:#eafaf1; border-left:4px solid #27ae60; padding:8px 16px; border-radius:4px; margin:4px 0; }"
        ".summary-failures { background:#fdedec; border-left:4px solid #e74c3c; padding:8px 16px; border-radius:4px; margin:4px 0; }"
        ".screenshot { max-width: 100%; border: 2px solid #e74c3c; border-radius: 4px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }"
        "</style>"
    ])


# ── Screenshot capture on test failure ────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on test failure and attach to HTML report."""
    outcome = yield
    report = outcome.get_result()
    
    # Only capture screenshot for test call failures (not setup/teardown)
    if report.when == "call" and report.failed:
        # Create screenshots directory
        screenshot_dir = Path("artifacts/test_screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to get driver from test instance
        driver = None
        if hasattr(item.instance, "driver"):
            driver = item.instance.driver
        
        if driver:
            try:
                # Generate screenshot filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                platform_name = getattr(item.instance, "platform", "unknown")
                screenshot_name = f"{item.nodeid.replace('::', '_').replace('/', '_')}_{platform_name}_{timestamp}.png"
                screenshot_path = screenshot_dir / screenshot_name
                
                # Capture screenshot
                driver.save_screenshot(str(screenshot_path))
                logger.info(f"Screenshot saved: {screenshot_path}")
                
                # Attach screenshot to HTML report (embedded as base64)
                with open(screenshot_path, "rb") as f:
                    screenshot_data = base64.b64encode(f.read()).decode("utf-8")
                
                # Add screenshot to report extras
                extra = getattr(report, "extra", [])
                if extra is None:
                    extra = []
                extra.append(pytest_html.extras.html(
                    f'<div><h3>Failure Screenshot</h3>'
                    f'<img src="data:image/png;base64,{screenshot_data}" class="screenshot" '
                    f'alt="Screenshot at failure" /></div>'
                ))
                report.extra = extra
                
            except Exception as e:
                logger.error(f"Failed to capture screenshot: {e}")


# ── Import pytest_html extras for screenshot embedding ────────────────────────

try:
    import pytest_html
except ImportError:
    logger.warning("pytest-html not installed, screenshot embedding disabled")
