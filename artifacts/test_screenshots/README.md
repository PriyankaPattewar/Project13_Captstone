# Test Failure Screenshots

This directory contains **automated screenshots** captured when Appium tests fail.

## 📸 What's Captured

- **Failure Screenshots**: Automatically captured when test assertions fail or elements cannot be found
- **Timestamp**: Each screenshot includes a timestamp in the filename
- **Platform**: Filename indicates whether it's iOS or Android
- **Test Name**: Filename includes the test class and method name

## 📁 Filename Format

```
test_login_screen_TestLogin_test_login_Android_20260721_170230.png
│                  │         │          │        │
│                  │         │          │        └─ Timestamp (YYYYMMDD_HHMMSS)
│                  │         │          └─ Platform (iOS/Android)
│                  │         └─ Test method
│                  └─ Test class
└─ Test file
```

## 🔍 Where to Find Screenshots

### GitHub Actions CI/CD

1. Go to the **Actions** tab in GitHub
2. Click on the failed workflow run
3. Scroll to **Artifacts** section at the bottom
4. Download **failure-screenshots-iOS** or **failure-screenshots-Android**
5. Extract the ZIP file to view screenshots

### HTML Test Report

Screenshots are **embedded directly** in the HTML test report:

1. Download **appium-test-reports-iOS** or **appium-test-reports-Android** artifact
2. Open `test_report_login_*.html` in a browser
3. Failed tests will show embedded screenshots below the error message

## 🎯 Benefits

- **Visual Debugging**: See exactly what the app looked like when the test failed
- **Faster Triage**: Identify UI issues, missing elements, or wrong screens quickly
- **Historical Record**: Screenshots archived with test artifacts for investigation
- **No Manual Work**: Automatically captured on every test failure

## 🧹 Local Cleanup

Screenshots are **not committed** to git (ignored in .gitignore).

To clean up local screenshots:

```bash
# PowerShell
Remove-Item artifacts/test_screenshots/*.png

# Bash
rm artifacts/test_screenshots/*.png
```

---

**Note**: This directory is automatically created during test execution. Screenshots older than the current run may be overwritten.
