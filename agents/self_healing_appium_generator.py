"""Enhanced Appium script generator with self-healing support.

Generates pytest-style Appium test scripts that use:
- Multi-strategy locators with automatic fallback
- Self-healing driver for robust element location
- Centralized configuration management
- Proper logging (fixing the logger import bug)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SelfHealingAppiumGenerator:
    """Generate self-healing Appium test scripts from locator JSON."""
    
    def __init__(self, project_root: Optional[Path | str] = None):
        """Initialize enhanced Appium generator.
        
        Args:
            project_root: Project root directory path
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).resolve().parents[1]
        
        self.input_dir = self.project_root / "artifacts" / "locator_output"
        self.output_dir = self.project_root / "artifacts" / "generated_appium_scripts"
    
    def generate_scripts_from_directory(
        self,
        input_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """Generate all test scripts from locator JSON files.
        
        Args:
            input_dir: Input directory with locator JSON files
            output_dir: Output directory for generated scripts
        
        Returns:
            List of generated script file paths
        """
        source_dir = Path(input_dir) if input_dir else self.input_dir
        dest_dir = Path(output_dir) if output_dir else self.output_dir
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        if not source_dir.exists():
            logger.error(f"Locator directory not found: {source_dir}")
            return []
        
        locator_files = list(source_dir.glob("*.json"))
        if not locator_files:
            logger.warning(f"No locator files found in {source_dir}")
            return []
        
        logger.info(f"Found {len(locator_files)} locator files to process")
        
        generated_scripts = []
        
        for locator_file in locator_files:
            try:
                locator_data = json.loads(locator_file.read_text(encoding="utf-8"))
                script_content = self.generate_script(locator_data)
                
                screen_name = locator_data.get("screen", "unknown")
                script_filename = self._to_script_name(screen_name)
                script_path = dest_dir / script_filename
                
                script_path.write_text(script_content, encoding="utf-8")
                
                logger.info(f"✓ Generated self-healing script: {script_filename}")
                generated_scripts.append(script_path)
                
            except Exception as e:
                logger.error(f"Failed to generate script from {locator_file.name}: {e}")
                continue
        
        logger.info(f"Successfully generated {len(generated_scripts)} self-healing test scripts")
        return generated_scripts
    
    def generate_script(self, locator_payload: Dict[str, Any]) -> str:
        """Generate a single self-healing test script.
        
        Args:
            locator_payload: Locator JSON data with multi-strategy locators
        
        Returns:
            Generated Python test script content
        """
        screen_name = locator_payload.get("screen", "Unknown")
        elements = locator_payload.get("elements", [])
        
        if not elements:
            raise ValueError(f"No elements found in locator payload for {screen_name}")
        
        class_name = self._to_class_name(screen_name)
        test_name = self._to_test_name(screen_name)
        
        # Generate test steps
        test_steps = self._generate_test_steps(screen_name, elements)
        
        # Generate full script
        script = self._build_script_template(
            screen_name=screen_name,
            class_name=class_name,
            test_name=test_name,
            test_steps=test_steps
        )
        
        return script
    
    def _build_script_template(
        self,
        screen_name: str,
        class_name: str,
        test_name: str,
        test_steps: str
    ) -> str:
        """Build the complete self-healing test script template."""
        
        return f'''"""Self-healing Appium test for {screen_name} screen.

Generated with multi-strategy locators and automatic fallback.
Uses centralized configuration and proper logging.
"""

import logging
from typing import Any, Dict, List
from pathlib import Path

# Import self-healing utilities
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.self_healing import SelfHealingDriver, LocatorStrategy, HealingRepository
from services.enhanced_config import get_config

# Configure logging
logger = logging.getLogger(__name__)


class {class_name}:
    """Self-healing test class for {screen_name} screen."""
    
    def setup_method(self) -> None:
        """Initialize Appium driver with self-healing capabilities."""
        config = get_config()
        
        # Prepare desired capabilities from config
        desired_caps = {{
            "platformName": config.platform_name,
            "automationName": config.automation_name,
            "deviceName": config.device_name,
            "app": str(config.app_path),
            "appPackage": config.app_package,
            "appActivity": config.app_activity,
            "noReset": True,
        }}
        
        # Create Appium driver
        self.driver = self._create_driver(desired_caps, config.appium_server_url)
        
        # Wrap with self-healing driver
        healing_config = {{
            "max_retries": config.healing_max_retries,
            "ai_vision_healing": config.ai_vision_healing,
            "explicit_wait_timeout": config.explicit_wait_timeout,
        }}
        
        self.healing_driver = SelfHealingDriver(
            driver=self.driver,
            config=healing_config
        )
        
        logger.info(f"✓ Test setup complete for {screen_name}")
    
    def teardown_method(self) -> None:
        """Clean up after test execution."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            logger.info("✓ Test teardown complete")
    
    def _create_driver(self, desired_caps: Dict[str, Any], server_url: str) -> Any:
        """Create Appium driver instance."""
        from appium import webdriver
        from appium.options.android import UiAutomator2Options
        
        options = UiAutomator2Options().load_capabilities(desired_caps)
        return webdriver.Remote(server_url, options=options)
    
    {test_name}(self) -> None:
        """Execute {screen_name} screen test with self-healing."""
        logger.info("=" * 60)
        logger.info(f"Starting test: {{test_name}}")
        logger.info("=" * 60)
        
{test_steps}
        
        logger.info("=" * 60)
        logger.info(f"✓ Test completed successfully: {test_name}")
        logger.info("=" * 60)
'''
    
    def _generate_test_steps(self, screen_name: str, elements: List[Dict[str, Any]]) -> str:
        """Generate test step code with multi-strategy locators.
        
        Args:
            screen_name: Name of the screen
            elements: List of element locator entries
        
        Returns:
            Indented Python code for test steps
        """
        steps = []
        step_number = 1
        
        for element_entry in elements:
            element_name = element_entry.get("element", "unknown")
            action = element_entry.get("action", "verify")
            step_desc = element_entry.get("step_description", "")
            
            # Build locator strategies list
            strategies_code = self._build_strategies_code(element_entry)
            
            # Generate action code based on action type
            if action == "tap":
                step_code = f'''        # Step {step_number}: Tap {element_name}
        logger.info("Step {step_number}: Tapping '{element_name}'")
        strategies = {strategies_code}
        self.healing_driver.tap_element(strategies, screen_name="{screen_name}")
        logger.info("✓ Step {step_number} complete")
'''
            
            elif action == "type":
                step_code = f'''        # Step {step_number}: Type into {element_name}
        logger.info("Step {step_number}: Typing into '{element_name}'")
        strategies = {strategies_code}
        self.healing_driver.type_text(strategies, "test_value", screen_name="{screen_name}")
        logger.info("✓ Step {step_number} complete")
'''
            
            elif action == "verify":
                step_code = f'''        # Step {step_number}: Verify {element_name} is present
        logger.info("Step {step_number}: Verifying '{element_name}'")
        strategies = {strategies_code}
        element = self.healing_driver.find_element(strategies, screen_name="{screen_name}")
        assert element is not None, "{element_name} not found"
        logger.info("✓ Step {step_number} complete - {element_name} verified")
'''
            
            elif action == "scroll":
                step_code = f'''        # Step {step_number}: Scroll to {element_name}
        logger.info("Step {step_number}: Scrolling to '{element_name}'")
        strategies = {strategies_code}
        self.healing_driver.find_element(strategies, screen_name="{screen_name}")
        logger.info("✓ Step {step_number} complete")
'''
            
            else:
                # Generic action
                step_code = f'''        # Step {step_number}: Interact with {element_name}
        logger.info("Step {step_number}: Action '{action}' on '{element_name}'")
        strategies = {strategies_code}
        self.healing_driver.find_element(strategies, screen_name="{screen_name}")
        logger.info("✓ Step {step_number} complete")
'''
            
            steps.append(step_code)
            step_number += 1
        
        return "\n".join(steps)
    
    def _build_strategies_code(self, element_entry: Dict[str, Any]) -> str:
        """Build Python list code for locator strategies.
        
        Args:
            element_entry: Element locator entry with strategies
        
        Returns:
            Python code string for list of LocatorStrategy objects
        """
        element_name = element_entry.get("element", "unknown")
        
        # Get multi-strategy data
        primary = element_entry.get("primary_strategy")
        fallbacks = element_entry.get("fallback_strategies", [])
        
        # Fallback to legacy format if multi-strategy not available
        if not primary:
            primary = {{
                "type": element_entry.get("locator_strategy", "text"),
                "value": element_entry.get("locator_value", element_name),
                "priority": 5,
                "reliability": 0.5
            }}
        
        all_strategies = [primary] + fallbacks
        
        # Build Python code for LocatorStrategy objects
        strategy_lines = []
        for strategy in all_strategies:
            strategy_lines.append(
                f'            LocatorStrategy('
                f'"{strategy["type"]}", '
                f'"{strategy["value"]}", '
                f'priority={strategy.get("priority", 5)}, '
                f'reliability={strategy.get("reliability", 0.5)}, '
                f'element_name="{element_name}")'
            )
        
        return "[\n" + ",\n".join(strategy_lines) + "\n        ]"
    
    def _to_class_name(self, screen_name: str) -> str:
        """Convert screen name to class name (e.g., 'Login' → 'TestLogin')."""
        clean_name = screen_name.replace(" ", "").replace("_", "")
        return f"Test{clean_name}"
    
    def _to_test_name(self, screen_name: str) -> str:
        """Convert screen name to test method name (e.g., 'Login' → 'def test_login')."""
        clean_name = screen_name.lower().replace(" ", "_").replace("-", "_")
        return f"def test_{clean_name}"
    
    def _to_script_name(self, screen_name: str) -> str:
        """Convert screen name to script filename (e.g., 'Login' → 'test_login_screen.py')."""
        clean_name = screen_name.lower().replace(" ", "_").replace("-", "_")
        return f"test_{clean_name}_screen.py"
