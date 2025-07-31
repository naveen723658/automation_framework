# Cross-Platform Mobile Selector Framework

A lightweight Python utility that lets you write **generic selectors** once and automatically converts them to the proper locator format for **Appium** (Android & iOS) or **UIAutomator2** (Android).

---

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Supported Generic Selectors](#supported-generic-selectors)
4. [Quick Start](#quick-start)
5. [Extending the Framework](#extending-the-framework)
6. [Error Handling](#error-handling)
7. [Project Structure](#project-structure)
8. [License](#license)

---

## Features
* 🔄 **Unified API** – Write a single selector and run it on either framework
* ⚡ **Zero-dependency** – Pure Python (< 200 lines of code)
* 📈 **31 built-in generic selectors** covering the most common use-cases
* 🧩 **Pluggable** – Add your own selectors with one method call
* 🛡️ **Typed & Validated** – Helpful errors when you mistype a selector or framework

## Installation
```bash
pip install mobile-selector-framework   # when published to PyPI
# or
pip install -e .   # from a local clone
```

## Supported Generic Selectors

| Generic | Appium Strategy | UIAutomator2 Kwarg | Notes |
|---------|-----------------|--------------------|-------|
| `id` | `id` | `resourceId` | Element resource-id / name |
| `text` | `xpath` | `text` | Exact text match |
| `text_contains` | `xpath` | `textContains` | Sub-string text match |
| `text_starts_with` | `xpath` | `textStartsWith` | Prefix match |
| `xpath` | `xpath` | `xpath` | Raw XPath (use sparingly) |
| `class` | `class name` | `className` | Widget class |
| `accessibility_id` | `accessibility id` | `description` | Content description / a11y id |
| `clickable` | `xpath` | `clickable` | Boolean state |
| `enabled` | `xpath` | `enabled` | Boolean state |
| `checked` | `xpath` | `checked` | Checkbox / switch state |
| _26 more_ | … | … | See `mobile_selector_framework.py` |

## Quick Start
```python
from mobile_selector_framework import MobileSelectorTransformer, UnifiedElementFinder
from appium.webdriver.common.appiumby import AppiumBy

# --- Appium ---
transformer = MobileSelectorTransformer()
by, value = transformer.transform_selector('id', 'com.example:id/login', 'appium')
print(by, value)   # -> ('id', 'com.example:id/login')

# Plug into Appium driver
el = driver.find_element(getattr(AppiumBy, by.upper().replace(' ', '_')), value)

# --- UIAutomator2 ---
kwargs = transformer.transform_selector('text', 'Login', 'uiautomator2')
print(kwargs)  # -> {'text': 'Login'}

d = u2.connect()
d(**kwargs).click()

# --- UnifiedElementFinder (same code for both) ---
finder = UnifiedElementFinder(driver, 'appium')   # or device & 'uiautomator2'
finder.find_element('accessibility_id', 'Submit').click()
```

## Extending the Framework
```python
t = MobileSelectorTransformer()

t.add_selector(
    'id_contains',
    appium_config=('xpath', lambda v: f"//*[contains(@resource-id, '{v}')]"),
    uiautomator2_config=('resourceIdMatches', lambda v: f'.*{v}.*')
)
```

## Error Handling
* **Unsupported selector** → `ValueError: Unsupported selector type: <name>`
* **Unsupported framework** → `ValueError: Unsupported framework: <name>`

## Project Structure
```
mobile_selector_framework.py   # core library
README.md                      # this file
```

## License
MIT
