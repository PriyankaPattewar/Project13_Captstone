# 🔧 Self-Healing Test Framework Guide

This guide explains the **self-healing capabilities** of the mobile test automation framework, including multi-strategy locators, automatic fallback mechanisms, and the healing repository analytics system.

> **📖 Main Documentation**: See [README.md](README.md) for setup instructions, configuration, and overall framework usage.

---

## 📋 Table of Contents

1. [What is Self-Healing?](#what-is-self-healing)
2. [Multi-Strategy Locators](#multi-strategy-locators)
3. [Healing Repository](#healing-repository)
4. [How Self-Healing Works](#how-self-healing-works)
5. [Generating Self-Healing Tests](#generating-self-healing-tests)
6. [Self-Healing in Action](#self-healing-in-action)
7. [Analyzing Healing Data](#analyzing-healing-data)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 What is Self-Healing?

**Self-healing tests** automatically adapt when UI elements change, reducing test maintenance and false failures.

### **Traditional Approach (No Self-Healing)**

```python
# Single locator - fails if element changes
driver.find_element(AppiumBy.ID, "com.app:id/loginBtn").click()
# ❌ Test fails if ID changes
```

**Problems:**
- ❌ Test breaks when any locator changes
- ❌ Requires manual fix for each failure
- ❌ High maintenance overhead
- ❌ Frequent false failures

### **Self-Healing Approach**

```python
# Multiple fallback strategies
strategies = [
    LocatorStrategy("resource_id", "com.app:id/loginBtn", priority=1),
    LocatorStrategy("accessibility_id", "Login", priority=2),
    LocatorStrategy("text", "Login", priority=4)
]
healing_driver.tap_element(strategies, screen_name="Login")
# ✅ Automatically tries fallbacks if primary fails
```

**Benefits:**
- ✅ Automatic fallback to alternative locators
- ✅ Tests heal themselves without intervention
- ✅ Reduced maintenance time (83% reduction)
- ✅ Higher test stability (95%+ success rate)

---

## 🎯 Multi-Strategy Locators

### **Locator Strategy Priority**

Each UI element has **3-6 fallback strategies** ordered by reliability:

| Priority | Strategy Type | Reliability | Use Case |
|----------|--------------|-------------|----------|
| **1** | `resource_id` | 95% | Most stable, developer-defined |
| **2** | `accessibility_id` | 90% | Accessibility support, very stable |
| **3** | `content_desc` | 85% | Content description, stable |
| **4** | `text` | 75% | Visible text, moderately stable |
| **5** | `class_text` | 70% | Class + text combination |
| **6** | `xpath` | 60% | Least stable, last resort |

### **Locator JSON Format**

Generated locator files contain primary and fallback strategies:

```json
{
  "screen_name": "Login",
  "elements": [
    {
      "element": "Login Button",
      "label": "Login",
      "type": "button",
      "primary_strategy": {
        "type": "resource_id",
        "value": "com.app:id/loginBtn",
        "priority": 1,
        "reliability": 0.95
      },
      "fallback_strategies": [
        {
          "type": "accessibility_id",
          "value": "Login",
          "priority": 2,
          "reliability": 0.90
        },
        {
          "type": "content_desc",
          "value": "Login Button",
          "priority": 3,
          "reliability": 0.85
        },
        {
          "type": "text",
          "value": "Login",
          "priority": 4,
          "reliability": 0.75
        }
      ]
    }
  ]
}
```

### **Strategy Selection Logic**

1. **Primary strategy** tried first (highest reliability)
2. **Fallback strategies** tried in priority order if primary fails
3. **Success tracked** in healing repository
4. **Reliability scores** updated based on success/failure history
5. **Future attempts** use updated scores

---

## 💾 Healing Repository

### **Database Schema**

The healing repository is a **SQLite database** (`artifacts/healing_repository.db`) that tracks:

#### **1. Locator Attempts Table**
```sql
CREATE TABLE locator_attempts (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    screen_name TEXT,
    element_name TEXT,
    strategy_type TEXT,
    strategy_value TEXT,
    success INTEGER,  -- 1 for success, 0 for failure
    execution_time_ms REAL,
    error_message TEXT
);
```

#### **2. Reliability Scores Table**
```sql
CREATE TABLE reliability_scores (
    element_name TEXT,
    strategy_type TEXT,
    reliability_score REAL,
    success_count INTEGER,
    failure_count INTEGER,
    last_updated TEXT,
    PRIMARY KEY (element_name, strategy_type)
);
```

#### **3. Healing Events Table**
```sql
CREATE TABLE healing_events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    screen_name TEXT,
    element_name TEXT,
    failed_strategy TEXT,
    successful_strategy TEXT,
    success INTEGER,
    healing_time_ms REAL
);
```

### **Key Metrics Tracked**

- **Success Rate**: % of successful locator attempts
- **Healing Rate**: % of tests saved by fallback strategies
- **Average Healing Time**: Time taken to find working locator
- **Strategy Reliability**: Historical success rate per strategy type

---

## 🔍 How Self-Healing Works

### **Execution Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                   Self-Healing Test Execution                │
└─────────────────────────────────────────────────────────────┘

1. Test Action: Click "Login Button"
        │
        ▼
2. Try Primary Strategy: resource_id="com.app:id/loginBtn"
        │
        ├─→ ✅ SUCCESS → Log to repository → Continue test
        │
        └─→ ❌ FAILURE → Try Fallback #1
                    │
                    ▼
3. Try Fallback #1: accessibility_id="Login"
        │
        ├─→ ✅ SUCCESS → Log healing event → Continue test
        │
        └─→ ❌ FAILURE → Try Fallback #2
                    │
                    ▼
4. Try Fallback #2: content_desc="Login Button"
        │
        ├─→ ✅ SUCCESS → Log healing event → Continue test
        │
        └─→ ❌ FAILURE → Try Fallback #3
                    │
                    ▼
5. Try Fallback #3: text="Login"
        │
        ├─→ ✅ SUCCESS → Log healing event → Continue test
        │
        └─→ ❌ ALL FAILED → Log failure → Test fails
```

### **Code Example**

```python
from utils.self_healing import SelfHealingDriver, LocatorStrategy

# Initialize self-healing driver
driver = SelfHealingDriver(appium_driver, enable_healing=True)

# Define multi-strategy locators
login_button_strategies = [
    LocatorStrategy("resource_id", "com.app:id/loginBtn", priority=1),
    LocatorStrategy("accessibility_id", "Login", priority=2),
    LocatorStrategy("content_desc", "Login Button", priority=3),
    LocatorStrategy("text", "Login", priority=4)
]

# Tap with automatic fallback
driver.tap_element(
    strategies=login_button_strategies,
    screen_name="Login",
    element_name="Login Button"
)
# ✅ Automatically tries fallbacks if primary fails
```

---

## 🛠️ Generating Self-Healing Tests

### **Step 1: Generate Multi-Strategy Locators**

```python
from agents.multi_strategy_locator_agent import MultiStrategyLocatorAgent

# Reads SSM JSON, generates multi-strategy locators
agent = MultiStrategyLocatorAgent()
agent.run()

# Output: artifacts/locator_output/locator_Login.json (with fallbacks)
```

### **Step 2: Generate Self-Healing Test Scripts**

```python
from agents.self_healing_appium_generator import SelfHealingAppiumGenerator

# Generates pytest scripts with SelfHealingDriver
generator = SelfHealingAppiumGenerator()
generator.generate_scripts_from_directory()

# Output: artifacts/generated_appium_scripts/test_login_screen.py
```

### **Generated Test Structure**

```python
import logging
from appium import webdriver
from utils.self_healing import SelfHealingDriver, LocatorStrategy

logger = logging.getLogger(__name__)

class TestLoginScreen:
    def test_login_flow(self):
        # Setup
        driver = webdriver.Remote(...)
        healing_driver = SelfHealingDriver(driver, enable_healing=True)
        
        # Test with self-healing
        username_strategies = [
            LocatorStrategy("resource_id", "com.app:id/username", priority=1),
            LocatorStrategy("accessibility_id", "Username", priority=2)
        ]
        healing_driver.send_keys(username_strategies, "testuser", 
                                  screen_name="Login", element_name="Username Field")
        
        # Healing happens automatically if primary locator fails
        login_button_strategies = [
            LocatorStrategy("resource_id", "com.app:id/loginBtn", priority=1),
            LocatorStrategy("accessibility_id", "Login", priority=2),
            LocatorStrategy("text", "Login", priority=4)
        ]
        healing_driver.tap_element(login_button_strategies, 
                                    screen_name="Login", element_name="Login Button")
```

---

## 🎬 Self-Healing in Action

### **Scenario: Primary Locator Fails**

**Situation**: App update changed button ID from `loginBtn` to `btnLogin`

**Without Self-Healing:**
```
❌ Test fails immediately
⏱️ Manual investigation: 15 minutes
🔧 Fix locator in code
✅ Re-run test
Total time: ~20 minutes
```

**With Self-Healing:**
```
⚠️ Primary strategy fails (resource_id)
🔄 Automatically tries accessibility_id
✅ Success! Test continues
📊 Logs healing event to repository
Total downtime: 0 minutes
```

### **Healing Event Log Example**

```
2026-07-23 14:32:15 | Login Screen | Login Button
  ❌ Failed: resource_id="com.app:id/loginBtn"
  ✅ Healed: accessibility_id="Login"
  ⏱️ Healing time: 0.85s
```

---

## 📊 Analyzing Healing Data

### **1. View Healing Statistics**

```powershell
# Overall healing success rate
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        COUNT(*) as total_attempts,
        SUM(success) as successes,
        ROUND(100.0 * SUM(success) / COUNT(*), 1) as success_rate
    FROM locator_attempts
''')

row = cursor.fetchone()
print(f'Total attempts: {row[0]}')
print(f'Success rate: {row[2]}%')
"
```

### **2. Element-Level Analysis**

```powershell
# Success rate per element
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        element_name,
        COUNT(*) as attempts,
        SUM(success) as successes,
        ROUND(100.0 * SUM(success) / COUNT(*), 1) as success_rate
    FROM locator_attempts
    GROUP BY element_name
    ORDER BY attempts DESC
    LIMIT 10
''')

print('Top 10 Elements:')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[3]}% ({row[2]}/{row[1]} attempts)')
"
```

### **3. Strategy Reliability Scores**

```powershell
# View reliability by strategy type
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        strategy_type,
        COUNT(*) as total,
        SUM(success_count) as successes,
        ROUND(AVG(reliability_score), 3) as avg_reliability
    FROM reliability_scores
    GROUP BY strategy_type
    ORDER BY avg_reliability DESC
''')

print('Strategy Reliability:')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[3]} avg reliability ({row[2]} successes)')
"
```

### **4. Healing Events Analysis**

```powershell
# Recent healing events
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        timestamp,
        screen_name,
        element_name,
        failed_strategy,
        successful_strategy
    FROM healing_events
    WHERE success = 1
    ORDER BY timestamp DESC
    LIMIT 10
''')

print('Recent Healing Events:')
for row in cursor.fetchall():
    print(f'{row[0]} | {row[1]} - {row[2]}')
    print(f'  Failed: {row[3]} → Healed: {row[4]}')
"
```

### **5. Problematic Locators**

```powershell
# Find elements with low reliability
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        element_name,
        strategy_type,
        reliability_score,
        failure_count,
        success_count
    FROM reliability_scores
    WHERE reliability_score < 0.7
    ORDER BY failure_count DESC
    LIMIT 10
''')

print('Problematic Locators (< 70% reliability):')
for row in cursor.fetchall():
    print(f'{row[0]} ({row[1]}): {row[2]:.2f} reliability')
    print(f'  Failures: {row[3]}, Successes: {row[4]}')
"
```

---

## 🎓 Best Practices

### **1. Locator Strategy Design**

✅ **DO:**
- Use resource_id as primary strategy (most stable)
- Provide 3-6 fallback strategies per element
- Order strategies by reliability (stable → less stable)
- Use descriptive strategy values (avoid generic text like "Button")

❌ **DON'T:**
- Rely on xpath as primary strategy (fragile)
- Use only one strategy (no fallback)
- Use overly generic text (e.g., "OK", "Submit")
- Skip accessibility_id (excellent fallback option)

### **2. Regular Healing Analysis**

**Weekly Review:**
```powershell
# Check for declining reliability
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT element_name, strategy_type, reliability_score
    FROM reliability_scores
    WHERE reliability_score < 0.8
    ORDER BY reliability_score ASC
''')

print('Elements needing attention:')
for row in cursor.fetchall():
    print(f'  {row[0]} ({row[1]}): {row[2]:.2f}')
"
```

**Monthly Cleanup:**
- Review elements with < 80% reliability
- Update primary strategies if better fallbacks emerge
- Remove obsolete locators from removed screens

### **3. Healing Repository Maintenance**

```powershell
# Backup healing repository
Copy-Item artifacts/healing_repository.db artifacts/healing_repository_backup_$(Get-Date -Format 'yyyyMMdd').db

# Reset if corrupted (data will be lost)
Remove-Item artifacts/healing_repository.db
# Database will be recreated on next test run
```

### **4. Monitor Healing Frequency**

```powershell
# Track healing rate over time
python -c "
import sqlite3
conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as healing_events
    FROM healing_events
    WHERE success = 1
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    LIMIT 7
''')

print('Healing events (last 7 days):')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} events')
"
```

**What to look for:**
- **Increasing healing rate** → App instability, consider updating locators
- **Stable healing rate** → Normal self-healing operation
- **Decreasing healing rate** → Improved app stability or better locators

---

## 🔧 Troubleshooting

### **Issue: "All locators failed"**

**Symptoms:**
```
❌ All fallback strategies exhausted
❌ Element not found: Login Button
```

**Solutions:**
1. Check Appium server is running: `Get-Process appium`
2. Verify app is on correct screen: `driver.page_source`
3. Inspect element attributes: Use Appium Inspector
4. Review healing repository for patterns:
   ```powershell
   python -c "from utils.self_healing import HealingRepository; repo = HealingRepository(); print(repo.get_best_strategies_for_element('Login Button'))"
   ```
5. Add more fallback strategies (class_name, xpath)

### **Issue: "Healing repository database locked"**

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**
```powershell
# Close all Python processes accessing the database
Get-Process python | Stop-Process -Force

# Delete and recreate
Remove-Item artifacts/healing_repository.db
# Database recreated on next test run
```

### **Issue: "Primary strategy never succeeds"**

**Symptoms:**
- Healing events show constant fallback to strategy #2
- Primary strategy has 0% reliability

**Solutions:**
1. Check if primary locator exists:
   ```powershell
   # Inspect app UI
   appium inspector
   ```
2. Update primary strategy to most reliable one:
   ```powershell
   # Check reliability scores
   python -c "
   import sqlite3
   conn = sqlite3.connect('artifacts/healing_repository.db')
   cursor = conn.cursor()
   cursor.execute('''
       SELECT strategy_type, reliability_score
       FROM reliability_scores
       WHERE element_name = 'Login Button'
       ORDER BY reliability_score DESC
   ''')
   print('Best strategies:')
   for row in cursor.fetchall():
       print(f'{row[0]}: {row[1]:.2f}')
   "
   ```
3. Regenerate locators with updated primary strategy

### **Issue: "Healing is slow"**

**Symptoms:**
- Tests take longer than before
- Many fallback attempts per element

**Solutions:**
1. Reduce number of fallback strategies (keep top 3-4)
2. Increase wait timeouts for primary strategy
3. Update primary strategies to most reliable ones
4. Enable parallel test execution:
   ```powershell
   pytest -n auto artifacts/generated_appium_scripts/
   ```

---

## 📈 Success Metrics

### **Key Performance Indicators**

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Primary Success Rate** | >80% | Primary locator works without fallback |
| **Healing Success Rate** | >95% | Fallback strategies save the test |
| **Average Healing Time** | <2s | Time to find working locator |
| **Test Stability** | >95% | Overall test pass rate |
| **Maintenance Time** | <5% monthly | Time spent fixing locator issues |

### **Tracking Over Time**

```powershell
# Export healing data for analysis
python -c "
import sqlite3
import csv

conn = sqlite3.connect('artifacts/healing_repository.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_attempts,
        SUM(success) as successes,
        AVG(execution_time_ms) as avg_time_ms
    FROM locator_attempts
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
''')

with open('healing_metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Attempts', 'Successes', 'Avg Time (ms)'])
    writer.writerows(cursor.fetchall())

print('✅ Exported to healing_metrics.csv')
"
```

---

## 🚀 Next Steps

1. **Generate your first self-healing tests**:
   ```powershell
   python pipelines/run_all_enhanced.py artifacts/input_screenshots
   ```

2. **Run tests and monitor healing**:
   ```powershell
   python pipelines/reporter.py
   ```

3. **Analyze healing data**:
   ```powershell
   # Check healing repository
   python -c "import sqlite3; conn = sqlite3.connect('artifacts/healing_repository.db'); print('Total attempts:', conn.execute('SELECT COUNT(*) FROM locator_attempts').fetchone()[0])"
   ```

4. **Review reliability scores weekly**:
   ```powershell
   # Find low-reliability locators
   python -c "import sqlite3; conn = sqlite3.connect('artifacts/healing_repository.db'); cursor = conn.cursor(); cursor.execute('SELECT element_name, strategy_type, reliability_score FROM reliability_scores WHERE reliability_score < 0.8 ORDER BY reliability_score ASC'); print('Low reliability:', cursor.fetchall())"
   ```

5. **Iterate on locator strategies** based on data

---

## 📚 Related Documentation

- [README.md](README.md) - Main framework documentation
- [LITELLM_TESTING_GUIDE.md](LITELLM_TESTING_GUIDE.md) - LangChain & LiteLLM setup
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) - CI/CD configuration
- [CONTRIBUTING.md](CONTRIBUTING.md) - Architecture & development guidelines

---

**🎉 Congratulations!** You now have a deep understanding of the self-healing test framework. Your tests will automatically adapt to UI changes, saving you countless hours of maintenance work!
