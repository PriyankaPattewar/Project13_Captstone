"""Enhanced configuration management with validation and path resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class Config:
    """Centralized configuration with environment variable loading and validation."""
    
    def __init__(self, dotenv_path: Path | str | None = None):
        """Initialize configuration and load environment variables.
        
        Args:
            dotenv_path: Path to .env file. Defaults to project root .env
        """
        self.project_root = self._detect_project_root()
        
        if dotenv_path is None:
            dotenv_path = self.project_root / ".env"
        else:
            dotenv_path = Path(dotenv_path)
        
        self._load_env(dotenv_path)
        self._validate_required_vars()
    
    def _detect_project_root(self) -> Path:
        """Auto-detect project root directory."""
        env_root = os.getenv("PROJECT_ROOT")
        if env_root:
            return Path(env_root).resolve()
        
        # Try to find project root by looking for key files
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / "requirements.txt").exists() or (parent / "README.md").exists():
                return parent
        
        # Fallback to parent of services directory
        return Path(__file__).resolve().parents[1]
    
    def _load_env(self, dotenv_path: Path) -> None:
        """Load environment variables from .env file."""
        if load_dotenv and dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path)
    
    def _validate_required_vars(self) -> None:
        """Validate that required environment variables are set."""
        vision_provider = self.vision_agent_provider
        testcase_provider = self.testcase_agent_provider
        
        # Only require API key if using OpenAI
        if vision_provider == "openai" or testcase_provider == "openai":
            if not self.openai_api_key or self.openai_api_key == "your_openai_api_key_here":
                raise EnvironmentError(
                    "OPENAI_API_KEY is required when using 'openai' provider. "
                    "Set it in your .env file or use 'mock' provider for testing."
                )
    
    # ========================================
    # AI/LLM Configuration
    # ========================================
    
    @property
    def vision_agent_provider(self) -> str:
        """Get vision agent provider (openai, mock)."""
        return os.getenv("VISION_AGENT_PROVIDER", "mock")
    
    @property
    def testcase_agent_provider(self) -> str:
        """Get test case agent provider (openai, mock)."""
        return os.getenv("TESTCASE_AGENT_PROVIDER", "mock")
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key."""
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def openai_model(self) -> str:
        """Get OpenAI model name."""
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    @property
    def openai_api_base(self) -> Optional[str]:
        """Get OpenAI API base URL (optional)."""
        return os.getenv("OPENAI_API_BASE", None)
    
    # ========================================
    # Appium Configuration
    # ========================================
    
    @property
    def appium_server_url(self) -> str:
        """Get Appium server URL."""
        return os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723")
    
    @property
    def app_package(self) -> str:
        """Get Android app package name."""
        return os.getenv("APP_PACKAGE", "com.saucelabs.mydemoapp.android")
    
    @property
    def app_activity(self) -> str:
        """Get Android app activity name."""
        return os.getenv("APP_ACTIVITY", "com.saucelabs.mydemoapp.android.view.activities.SplashActivity")
    
    @property
    def platform_name(self) -> str:
        """Get platform name."""
        return os.getenv("PLATFORM_NAME", "Android")
    
    @property
    def automation_name(self) -> str:
        """Get automation name."""
        return os.getenv("AUTOMATION_NAME", "UiAutomator2")
    
    @property
    def device_name(self) -> str:
        """Get device name."""
        return os.getenv("DEVICE_NAME", "Android Emulator")
    
    @property
    def app_path(self) -> Path:
        """Get absolute path to APK file."""
        app_path_str = os.getenv("APP_PATH", "demo_mobile_apps/mda-2.2.0-25.apk")
        app_path = Path(app_path_str)
        
        # If relative path, resolve from project root
        if not app_path.is_absolute():
            app_path = self.project_root / app_path
        
        return app_path.resolve()
    
    # ========================================
    # Path Configuration
    # ========================================
    
    @property
    def artifacts_dir(self) -> Path:
        """Get artifacts directory path."""
        return self.project_root / os.getenv("ARTIFACTS_DIR", "artifacts")
    
    @property
    def input_screenshots_dir(self) -> Path:
        """Get input screenshots directory."""
        return self.project_root / os.getenv("INPUT_SCREENSHOTS_DIR", "artifacts/input_screenshots")
    
    @property
    def ssm_output_dir(self) -> Path:
        """Get SSM output directory."""
        return self.project_root / os.getenv("SSM_OUTPUT_DIR", "artifacts/ssm_json_output")
    
    @property
    def manual_testcases_dir(self) -> Path:
        """Get manual test cases directory."""
        return self.project_root / os.getenv("MANUAL_TESTCASES_DIR", "artifacts/manual_testcases")
    
    @property
    def locator_output_dir(self) -> Path:
        """Get locator output directory."""
        return self.project_root / os.getenv("LOCATOR_OUTPUT_DIR", "artifacts/locator_output")
    
    @property
    def generated_scripts_dir(self) -> Path:
        """Get generated scripts directory."""
        return self.project_root / os.getenv("GENERATED_SCRIPTS_DIR", "artifacts/generated_appium_scripts")
    
    @property
    def review_reports_dir(self) -> Path:
        """Get review reports directory."""
        return self.project_root / os.getenv("REVIEW_REPORTS_DIR", "artifacts/review_reports")
    
    @property
    def test_reports_dir(self) -> Path:
        """Get test execution reports directory."""
        return self.project_root / os.getenv("TEST_REPORTS_DIR", "artifacts/test_execution_reports")
    
    # ========================================
    # Self-Healing Configuration
    # ========================================
    
    @property
    def self_healing_enabled(self) -> bool:
        """Check if self-healing is enabled."""
        return os.getenv("SELF_HEALING_ENABLED", "true").lower() in ("true", "1", "yes")
    
    @property
    def healing_max_retries(self) -> int:
        """Get maximum retries for healing."""
        return int(os.getenv("HEALING_MAX_RETRIES", "3"))
    
    @property
    def ai_vision_healing(self) -> bool:
        """Check if AI vision healing is enabled."""
        return os.getenv("AI_VISION_HEALING", "true").lower() in ("true", "1", "yes")
    
    @property
    def healing_repository_enabled(self) -> bool:
        """Check if healing repository is enabled."""
        return os.getenv("HEALING_REPOSITORY_ENABLED", "true").lower() in ("true", "1", "yes")
    
    # ========================================
    # Test Execution Configuration
    # ========================================
    
    @property
    def explicit_wait_timeout(self) -> int:
        """Get explicit wait timeout in seconds."""
        return int(os.getenv("EXPLICIT_WAIT_TIMEOUT", "10"))
    
    @property
    def implicit_wait_timeout(self) -> int:
        """Get implicit wait timeout in seconds."""
        return int(os.getenv("IMPLICIT_WAIT_TIMEOUT", "5"))
    
    @property
    def auto_open_browser(self) -> bool:
        """Check if browser should auto-open after test execution."""
        return os.getenv("AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")
    
    # ========================================
    # Logging Configuration
    # ========================================
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    @property
    def log_format(self) -> str:
        """Get log format."""
        return os.getenv("LOG_FORMAT", "%(asctime)s [%(levelname)s] %(message)s")
    
    # ========================================
    # Performance & Caching
    # ========================================
    
    @property
    def enable_llm_cache(self) -> bool:
        """Check if LLM caching is enabled."""
        return os.getenv("ENABLE_LLM_CACHE", "true").lower() in ("true", "1", "yes")
    
    @property
    def cache_backend(self) -> str:
        """Get cache backend type."""
        return os.getenv("CACHE_BACKEND", "file")
    
    @property
    def cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        return int(os.getenv("CACHE_TTL", "86400"))
    
    # ========================================
    # Cost Tracking
    # ========================================
    
    @property
    def enable_token_tracking(self) -> bool:
        """Check if token tracking is enabled."""
        return os.getenv("ENABLE_TOKEN_TRACKING", "true").lower() in ("true", "1", "yes")
    
    @property
    def token_tracking_log(self) -> Path:
        """Get token tracking log file path."""
        return self.project_root / os.getenv("TOKEN_TRACKING_LOG", "artifacts/token_usage.log")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_environment(dotenv_path: Path | None = None) -> None:
    """Load environment variables (backward compatibility)."""
    global _config
    _config = Config(dotenv_path=dotenv_path)
