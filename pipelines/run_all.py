"""End-to-end pipeline runner.

Runs all steps in sequence:
  Step 1  – Screenshots      → SSM JSON          (ssm_generator)
  Step 2  – SSM JSON         → Manual test cases (testcase_generator)
  Step 3  – SSM JSON         → Locator JSON      (locator_agent)
  Step 4  – Locator JSON     → Appium scripts    (appium_generator_agent)
  Step 5  – Appium scripts   → Review reports    (reviewer_agent)
  Step 6  – Appium scripts   → Test execution HTML report (reporter_agent)

Usage:
    python pipelines/run_all.py artifacts/input_screenshots
    python pipelines/run_all.py artifacts/input_screenshots --no-browser
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.config import load_environment

load_environment()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0].startswith("--"):
        print("Usage: python pipelines/run_all.py <screenshots_folder> [--no-browser]")
        return 2

    screenshots_dir = args[0]
    open_browser = "--no-browser" not in args

    # ── Step 1: Screenshots → SSM JSON (Vision Agent) ───────────────────
    print("\n=== Step 1: Screenshots → SSM JSON ===")
    from agents.vision_agent import create_vision_agent
    from models.ssm import ScreenSemanticModel

    screenshots_path = Path(screenshots_dir)
    ssm_out_dir = ROOT / "artifacts" / "ssm_json_output"
    if ssm_out_dir.exists():
        shutil.rmtree(ssm_out_dir)
    ssm_out_dir.mkdir(parents=True, exist_ok=True)

    vision_provider = os.getenv("VISION_AGENT_PROVIDER", "mock")
    prompt_path = ROOT / "prompts" / "vision_analysis.txt"
    vision_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else None
    vision_agent = create_vision_agent(provider=vision_provider, prompt_template=vision_prompt)

    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    image_files = sorted(p for p in screenshots_path.iterdir() if p.suffix.lower() in image_extensions)

    ssm_results = []   # ← in-memory SSM dicts passed directly to Step 2
    for img in image_files:
        raw = vision_agent.analyze_image(str(img))
        ssm = ScreenSemanticModel.model_validate(raw)
        timestamp = int(time.time())
        out_path = ssm_out_dir / f"ssm_{ssm.screen_name}_{timestamp}.json"
        out_path.write_text(ssm.model_dump_json(indent=2), encoding="utf-8")
        ssm_results.append({"path": out_path, "data": ssm.model_dump()})
        print(f"  SSM saved → {out_path.name}")

    # ── Step 2: SSM JSON → Manual Test Cases (TestCaseAgent) ─────────────
    # SSM data is passed in-memory directly from Step 1 — no file re-read needed.
    print("\n=== Step 2: SSM JSON → Manual Test Cases ===")
    from agents.testcase_agent import create_testcase_agent

    tc_provider = os.getenv("TESTCASE_AGENT_PROVIDER") or ("openai" if os.getenv("OPENAI_API_KEY") else "mock")
    tc_prompt_path = ROOT / "prompts" / "test_generation.txt"
    tc_prompt = tc_prompt_path.read_text(encoding="utf-8") if tc_prompt_path.exists() else None
    tc_agent = create_testcase_agent(provider=tc_provider, prompt_template=tc_prompt)

    tc_out_dir = ROOT / "artifacts" / "manual_testcases"
    tc_out_dir.mkdir(parents=True, exist_ok=True)

    for item in ssm_results:
        ssm_data = item["data"]
        ssm_path = item["path"]
        result_text = tc_agent.generate_from_ssm(ssm_data, filename=ssm_path.stem)
        timestamp = int(time.time())
        tc_path = tc_out_dir / f"manual_testcases_{ssm_path.stem}_{timestamp}.txt"
        tc_path.write_text(result_text, encoding="utf-8")
        print(f"  Test cases saved → {tc_path.name}")

    # ── Step 3: SSM JSON → Locator JSON ─────────────────────────────────
    print("\n=== Step 3: SSM JSON → Locator JSON ===")
    import sys as _sys
    _agents_path = str(ROOT / "agents")
    if _agents_path not in _sys.path:
        _sys.path.insert(0, _agents_path)
    from agents.locator_agent import LocatorAgent
    locator_agent = LocatorAgent(project_root=ROOT)
    locator_agent.run()

    # ── Step 4: Locator JSON → Appium scripts ───────────────────────────
    print("\n=== Step 4: Locator JSON → Appium Scripts ===")
    from agents.appium_generator_agent import AppiumGeneratorAgent
    appium_agent = AppiumGeneratorAgent(project_root=ROOT)
    appium_agent.generate_scripts_from_directory()

    # ── Step 5: Appium scripts → Review reports ──────────────────────────
    print("\n=== Step 5: Appium Scripts → Review Reports ===")
    from agents.reviewer_agent import ReviewerAgent
    reviewer = ReviewerAgent(project_root=ROOT)
    reviewer.review_scripts()

    # ── Step 6: Run Appium scripts → HTML execution report ───────────────
    print("\n=== Step 6: Running Tests → HTML Execution Report ===")
    from agents.reporter_agent import ReporterAgent
    reporter = ReporterAgent(project_root=ROOT)
    report_path = reporter.run(open_browser=open_browser)
    print(f"\nAll steps complete. Execution report → {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
