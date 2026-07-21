"""Enhanced end-to-end pipeline with LangChain and self-healing.

Runs all steps with the new features:
  Step 1  – Screenshots → SSM JSON (LangChain Vision Agent)
  Step 2  – SSM JSON → Manual test cases (LangChain Test Case Agent)
  Step 3  – SSM JSON → Multi-strategy locators
  Step 4  – Locators → Self-healing Appium scripts
  Step 5  – Scripts → Review reports
  Step 6  – Scripts → Test execution with healing

Usage:
    python pipelines/run_all_enhanced.py artifacts/input_screenshots
    python pipelines/run_all_enhanced.py artifacts/input_screenshots --no-browser
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.enhanced_config import get_config

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0].startswith("--"):
        print("Usage: python pipelines/run_all_enhanced.py <screenshots_folder> [--no-browser]")
        return 2

    screenshots_dir = args[0]
    open_browser = "--no-browser" not in args
    
    # Load configuration
    config = get_config()
    
    print("\n" + "=" * 70)
    print("🚀 ENHANCED MOBILE TEST GENERATOR PIPELINE")
    print("=" * 70)
    print(f"✓ LangChain Integration: Enabled")
    print(f"✓ Self-Healing: {config.self_healing_enabled}")
    print(f"✓ AI Vision Healing: {config.ai_vision_healing}")
    print(f"✓ Token Tracking: {config.enable_token_tracking}")
    print(f"✓ LLM Caching: {config.enable_llm_cache}")
    print("=" * 70 + "\n")

    # Step 1: Screenshots → SSM JSON (LangChain Vision Agent)
    print("\n" + "=" * 70)
    print("STEP 1: Screenshots → SSM JSON (LangChain Vision Agent)")
    print("=" * 70)
    
    try:
        from agents.langchain_vision_agent import create_langchain_vision_agent
    except ImportError:
        print("⚠ LangChain not available, falling back to standard agent")
        from agents.vision_agent import create_vision_agent as create_langchain_vision_agent
    
    from models.ssm import ScreenSemanticModel
    import json
    import time
    import shutil
    
    screenshots_path = Path(screenshots_dir)
    ssm_out_dir = config.ssm_output_dir
    if ssm_out_dir.exists():
        shutil.rmtree(ssm_out_dir)
    ssm_out_dir.mkdir(parents=True, exist_ok=True)

    vision_provider = config.vision_agent_provider
    prompt_path = ROOT / "prompts" / "vision_analysis.txt"
    vision_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else None
    
    vision_agent = create_langchain_vision_agent(
        provider=vision_provider,
        prompt_template=vision_prompt
    )

    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    image_files = sorted(p for p in screenshots_path.iterdir() if p.suffix.lower() in image_extensions)

    ssm_results = []
    for img in image_files:
        print(f"\n📸 Analyzing: {img.name}")
        raw = vision_agent.analyze_image(str(img))
        ssm = ScreenSemanticModel.model_validate(raw)
        timestamp = int(time.time())
        out_path = ssm_out_dir / f"ssm_{ssm.screen_name}_{timestamp}.json"
        out_path.write_text(ssm.model_dump_json(indent=2), encoding="utf-8")
        ssm_results.append({"path": out_path, "data": ssm.model_dump()})
        print(f"  ✓ SSM saved → {out_path.name}")
    
    # Show token usage if using LangChain
    if hasattr(vision_agent, 'get_usage_stats'):
        stats = vision_agent.get_usage_stats()
        print(f"\n💰 Token Usage: {stats['total_tokens']} tokens | Cost: ${stats['total_cost']:.4f}")

    # Step 2: SSM JSON → Manual Test Cases (Standard Agent)
    print("\n" + "=" * 70)
    print("STEP 2: SSM JSON → Manual Test Cases")
    print("=" * 70)
    
    from agents.testcase_agent import create_testcase_agent

    tc_provider = config.testcase_agent_provider
    tc_prompt_path = ROOT / "prompts" / "test_generation.txt"
    tc_prompt = tc_prompt_path.read_text(encoding="utf-8") if tc_prompt_path.exists() else None
    tc_agent = create_testcase_agent(provider=tc_provider, prompt_template=tc_prompt)

    tc_out_dir = config.manual_testcases_dir
    tc_out_dir.mkdir(parents=True, exist_ok=True)

    for item in ssm_results:
        ssm_data = item["data"]
        ssm_path = item["path"]
        result_text = tc_agent.generate_from_ssm(ssm_data, filename=ssm_path.stem)
        timestamp = int(time.time())
        tc_path = tc_out_dir / f"manual_testcases_{ssm_path.stem}_{timestamp}.txt"
        tc_path.write_text(result_text, encoding="utf-8")
        print(f"  ✓ Test cases saved → {tc_path.name}")

    # Step 3: SSM JSON → Multi-Strategy Locators
    print("\n" + "=" * 70)
    print("STEP 3: SSM JSON → Multi-Strategy Locators")
    print("=" * 70)
    
    try:
        from agents.multi_strategy_locator_agent import MultiStrategyLocatorAgent
        locator_agent = MultiStrategyLocatorAgent(project_root=ROOT)
        generated_files = locator_agent.run()
        print(f"\n✓ Generated {len(generated_files)} locator files with multi-strategy support")
    except Exception as e:
        print(f"⚠ Multi-strategy locator failed: {e}")
        print("  Falling back to standard locator agent...")
        from agents.locator_agent import LocatorAgent
        locator_agent = LocatorAgent()
        locator_agent.run()

    # Step 4: Locators → Self-Healing Appium Scripts
    print("\n" + "=" * 70)
    print("STEP 4: Locators → Self-Healing Appium Scripts")
    print("=" * 70)
    
    try:
        from agents.self_healing_appium_generator import SelfHealingAppiumGenerator
        appium_agent = SelfHealingAppiumGenerator(project_root=ROOT)
        script_files = appium_agent.generate_scripts_from_directory()
        print(f"\n✓ Generated {len(script_files)} self-healing test scripts")
    except Exception as e:
        print(f"⚠ Self-healing generator failed: {e}")
        print("  Falling back to standard Appium generator...")
        from agents.appium_generator_agent import AppiumGeneratorAgent
        appium_agent = AppiumGeneratorAgent(project_root=ROOT)
        appium_agent.generate_scripts_from_directory()

    # Step 5: Scripts → Review Reports
    print("\n" + "=" * 70)
    print("STEP 5: Scripts → Review Reports")
    print("=" * 70)
    
    from agents.reviewer_agent import ReviewerAgent
    reviewer = ReviewerAgent(project_root=ROOT)
    reviewer.review_scripts()

    # Step 6: Run Tests → HTML Report
    print("\n" + "=" * 70)
    print("STEP 6: Running Tests → HTML Execution Report")
    print("=" * 70)
    
    from agents.reporter_agent import ReporterAgent
    reporter = ReporterAgent(project_root=ROOT)
    report_path = reporter.run(open_browser=open_browser)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"📊 Execution Report: {report_path}")
    
    if config.healing_repository_enabled:
        healing_db = ROOT / "artifacts" / "healing_repository.db"
        if healing_db.exists():
            print(f"🔧 Healing Repository: {healing_db}")
    
    if config.enable_token_tracking:
        token_log = config.token_tracking_log
        if token_log.exists():
            print(f"💰 Token Usage Log: {token_log}")
    
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
