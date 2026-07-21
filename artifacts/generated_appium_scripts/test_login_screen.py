"""Generated Appium pytest script for Login."""

import os
from typing import Any, Dict, Tuple

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestLogin:
    """Example Appium test class for the Login screen."""

    def setup_method(self) -> None:
        """Create the Appium driver and explicit wait before each test."""
        # Read configuration from environment
        platform = os.getenv("PLATFORM_NAME", "Android")
        platform_version = os.getenv("PLATFORM_VERSION", "14.0")
        device_name = os.getenv("DEVICE_NAME", "Android Emulator")
        app_path = os.getenv("APP_PATH", "")
        appium_server = os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723")
        
        desired_caps = {
            "platformName": platform,
            "deviceName": device_name,
            "app": app_path,
            "noReset": True,
        }
        
        # Platform-specific capabilities
        if platform.lower() == "ios":
            desired_caps["automationName"] = "XCUITest"
            # platformVersion is optional for iOS and can cause SDK mismatch issues
            # iOS-specific XCUITest options for better stability
            desired_caps["wdaLaunchTimeout"] = 180000  # 3 minutes for WDA launch
            desired_caps["wdaConnectionTimeout"] = 180000  # 3 minutes for WDA connection
            desired_caps["isHeadless"] = False  # Run with UI (already pre-booted)
            desired_caps["usePrebuiltWDA"] = True  # Use prebuilt WDA if available
        else:  # Android
            desired_caps["automationName"] = "UiAutomator2"
            desired_caps["platformVersion"] = platform_version
            # Let Appium auto-detect appPackage and appActivity from APK manifest
            # This is more reliable than hardcoding activity names
            # Android-specific options for better app startup
            desired_caps["autoGrantPermissions"] = True  # Auto-grant runtime permissions
            desired_caps["appWaitActivity"] = "*"  # Wait for any activity to start
            desired_caps["appWaitDuration"] = 60000  # Wait up to 60 seconds for app to start
            desired_caps["androidInstallTimeout"] = 90000  # 90 seconds for app installation
        
        self.driver = self._create_driver(desired_caps, appium_server)
        self.wait = WebDriverWait(self.driver, 10) if WebDriverWait is not None else None
        self.platform = platform
        
        # Dismiss Android compatibility popups (16 KB page size warning)
        if platform.lower() == "android":
            self._dismiss_android_popups()

    def teardown_method(self) -> None:
        """Quit the Appium session after the test finishes."""
        if getattr(self, "driver", None):
            self.driver.quit()

    def tap(self, locator_strategy: str, locator_value: str) -> None:
        """Tap an element using a platform-appropriate locator and an explicit wait."""
        locator = self._build_locator(locator_strategy, locator_value)
        if self.wait is not None and EC is not None:
            element = self.wait.until(EC.element_to_be_clickable(locator))
        else:
            element = self.driver.find_element(*locator)
        element.click()

    def type(self, locator_strategy: str, locator_value: str, text: str) -> None:
        """Type text into an editable field using a platform-appropriate locator."""
        locator = self._build_locator(locator_strategy, locator_value)
        if self.wait is not None and EC is not None:
            element = self.wait.until(EC.element_to_be_clickable(locator))
        else:
            element = self.driver.find_element(*locator)
        element.clear()
        element.send_keys(text)

    def scroll(self, locator_strategy: str, locator_value: str) -> None:
        """Scroll until a target element is visible (Android only)."""
        if self.platform.lower() == "android":
            selector = self._build_uiautomator_selector(locator_strategy, locator_value)
            scroll_command = (
                f"new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView({self._build_uiautomator_selector(locator_strategy, locator_value)})"
            )
            self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, scroll_command)
        if self.wait is not None and EC is not None:
            self.wait.until(EC.visibility_of_element_located(self._build_locator(locator_strategy, locator_value)))

    def _create_driver(self, desired_caps: Dict[str, Any], server_url: str) -> Any:
        """Create the Appium driver with platform-appropriate options."""
        from appium import webdriver
        
        platform = desired_caps.get("platformName", "Android")
        
        if platform.lower() == "ios":
            from appium.options.ios import XCUITestOptions
            options = XCUITestOptions().load_capabilities(desired_caps)
        else:  # Android
            from appium.options.android import UiAutomator2Options
            options = UiAutomator2Options().load_capabilities(desired_caps)

        return webdriver.Remote(server_url, options=options)

    def _build_locator(self, locator_strategy: str, locator_value: str) -> Tuple[str, str]:
        """Convert a logical locator into an Appium locator tuple."""

        if locator_strategy == "resource_id":
            return (AppiumBy.ID, locator_value)

        if locator_strategy == "accessibility_id":
            return (AppiumBy.ACCESSIBILITY_ID, locator_value)

        # Fallback for Android
        if self.platform.lower() == "android":
            return (
                AppiumBy.ANDROID_UIAUTOMATOR,
                self._build_uiautomator_selector(locator_strategy, locator_value),
            )
        else:
            # iOS fallback to name or accessibility_id
            return (AppiumBy.NAME, locator_value)

    def _build_uiautomator_selector(self, locator_strategy: str, locator_value: str) -> str:
        """Create a UiAutomator2 selector string without using fragile XPath (Android only)."""
        strategy = (locator_strategy or "text").strip().lower()
        if strategy == "accessibility_id":
            return f'new UiSelector().description("{locator_value}")'
        if strategy == "resource_id":
            return f'new UiSelector().resourceId("{locator_value}")'
        return f'new UiSelector().text("{locator_value}")'

    def _dismiss_android_popups(self) -> None:
        """Dismiss common Android system popups (16KB compatibility warning, permissions, etc.)."""
        import time
        time.sleep(2)  # Wait for popup to appear
        
        # List of button texts to try clicking (in order of preference)
        dismiss_buttons = [
            "Don't Show Again",  # Suppress future warnings
            "OK",                # Standard dismiss
            "Allow",             # Permissions
            "Accept",            # Generic accept
            "Continue",          # Generic continue
            "Got it",            # Tutorial/help screens
        ]
        
        for button_text in dismiss_buttons:
            try:
                # Try to find and click button using text
                button_locator = (
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{button_text}")'
                )
                button = self.driver.find_element(*button_locator)
                if button.is_displayed():
                    button.click()
                    print(f"✓ Dismissed popup by clicking '{button_text}'")
                    time.sleep(1)  # Wait for popup to close
                    return
            except Exception:
                # Button not found, try next one
                continue
        
        # No popup found or already dismissed
        print("✓ No Android system popups detected")

    def test_login(self) -> None:
        """Exercise the screen actions discovered by the locator agent."""
        import time
        
        # Step 1: Tap hamburger menu button to open drawer
        time.sleep(3)  # Wait for app to fully load
        
        # Try multiple strategies to find and tap the hamburger menu
        hamburger_tapped = False
        strategies = [
            ('accessibility_id', 'open menu'),
            ('accessibility_id', 'menu'),
            ('accessibility_id', 'Navigate up'),
            ('xpath', '//android.view.ViewGroup[@content-desc="open menu"]'),
            ('xpath', '//android.widget.ImageView[contains(@content-desc, "menu")]'),
            ('xpath', '//*[@content-desc="open menu"]'),
        ]
        
        for strategy_type, strategy_value in strategies:
            try:
                print(f"Trying {strategy_type}: {strategy_value}")
                if strategy_type == 'accessibility_id':
                    element = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, strategy_value)
                else:  # xpath
                    element = self.driver.find_element(AppiumBy.XPATH, strategy_value)
                element.click()
                print(f"✓ Hamburger menu tapped using {strategy_type}: {strategy_value}")
                hamburger_tapped = True
                break
            except Exception as e:
                print(f"✗ Failed with {strategy_type}: {strategy_value} - {str(e)[:100]}")
                continue
        
        if not hamburger_tapped:
            # Last resort: dump page source for debugging
            print("\n=== PAGE SOURCE FOR DEBUGGING ===")
            print(self.driver.page_source[:2000])  # Print first 2000 chars
            raise Exception("Could not find hamburger menu with any strategy")
        
        # Step 2: Tap Login menu item in the drawer
        time.sleep(1)  # Wait for menu to open
        self.tap('accessibility_id', 'menu item log in')
        
        # Step 3: Type Username
        time.sleep(1)  # Wait for login screen
        self.type('accessibility_id', 'Username input field', 'bob@example.com')
        
        # Step 4: Type Password
        self.type('accessibility_id', 'Password input field', '10203040')
        
        # Step 5: Tap Login Button
        self.tap('accessibility_id', 'Login button')

