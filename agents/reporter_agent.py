"""Reporter Agent — runs Appium pytest scripts, saves HTML report to a timestamped
directory, and opens it in the default browser."""

from __future__ import annotations

import logging
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ReporterAgent:
    """Execute generated Appium test scripts via pytest, save an HTML report to a
    timestamped directory under ``artifacts/test_execution_reports/``, and open
    the report in the default browser.

    Can be used standalone::

        agent = ReporterAgent()
        report_path = agent.run()

    Or triggered at the end of the full pipeline::

        agent = ReporterAgent(project_root="/path/to/project")
        agent.run(open_browser=True)
    """

    def __init__(self, project_root: Optional[Path | str] = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[1])
        self.scripts_dir = self.project_root / "artifacts" / "generated_appium_scripts"
        self.reports_base = self.project_root / "artifacts" / "test_execution_reports"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        scripts_dir: Optional[Path | str] = None,
        open_browser: bool = True,
    ) -> Path:
        """Run pytest over the generated Appium scripts, save an HTML report, and
        optionally open it in the browser.

        Args:
            scripts_dir: Override the folder containing test scripts.
            open_browser: Whether to open the HTML report automatically.

        Returns:
            Path to the generated HTML report file.
        """
        source = Path(scripts_dir or self.scripts_dir)
        if not source.exists():
            raise FileNotFoundError(f"Scripts directory not found: {source}")

        # Timestamped output folder
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = self.reports_base / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        report_html = run_dir / "report.html"

        logger.info("[ReporterAgent] Running tests from: %s", source)
        logger.info("[ReporterAgent] Saving report to: %s", report_html)
        print(f"[ReporterAgent] Running tests from: {source}")
        print(f"[ReporterAgent] Saving report to:   {report_html}")

        exit_code = self._run_pytest(source, report_html)

        status = "PASSED" if exit_code == 0 else "FAILED/ERRORS"
        logger.info("[ReporterAgent] Test run complete — %s (exit code %d)", status, exit_code)
        print(f"[ReporterAgent] Test run complete — {status} (exit code {exit_code})")
        print(f"[ReporterAgent] Report: {report_html}")

        if open_browser and report_html.exists():
            webbrowser.open(report_html.as_uri())

        return report_html

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_pytest(self, scripts_dir: Path, report_html: Path) -> int:
        """Invoke pytest as a subprocess and return the exit code."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(scripts_dir),
            f"--html={report_html}",
            "--self-contained-html",
            "-v",                        # verbose: show each test name
            "--tb=long",                 # full traceback on failure
            "--log-cli-level=INFO",      # stream logger.info() calls live
            "--log-cli-format=%(asctime)s [%(levelname)s] %(message)s",
            "--capture=tee-sys",         # capture stdout/stderr AND show in report
        ]
        result = subprocess.run(cmd, cwd=str(self.project_root))
        return result.returncode
