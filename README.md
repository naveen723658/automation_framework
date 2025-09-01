# Mobile Automation Framework

A comprehensive, modular Python-based framework for robust mobile UI automation testing, supporting both UIAutomator2 and Appium drivers with advanced action management, assertions, and reporting capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-Driver Support**: Seamless integration with UIAutomator2 and Appium
- **Modular Actions**: Extensible action classes for gestures, text input, navigation, device control
- **Advanced Assertions**: Comprehensive assertion library with continuous watching capabilities
- **YAML-Driven Tests**: Declarative test definitions with step-based execution
- **Intelligent Locators**: Automatic fallback strategies with self-healing capabilities
- **Rich Artifacts**: Screenshots, videos, logs, and detailed test results

### Advanced Features
- **Viewport-Aware Element Detection**: Ensures elements are truly visible before interaction
- **Fallback Direction Support**: Smart gesture recovery with alternative swipe directions
- **Continuous Element Watching**: Real-time monitoring for dynamic UI changes
- **Device State Management**: Control airplane mode, WiFi, volume, and system settings
- **Network Activity Monitoring**: Wait for network idle states and loading completion
- **Cross-Platform Compatibility**: Works with Android devices and emulators

## 📁 Project Structure

```
mobile-automation-framework/
├── actions/                    # Action modules for different interactions
│   ├── base.py                # Base action class with core functionality
│   ├── device.py              # Device control actions (WiFi, airplane mode, volume)
│   ├── gestures.py            # Swipe and gesture actions with fallback support
│   ├── navigation.py          # System navigation and app management
│   ├── text.py                # Text input and keyboard interactions
│   └── __init__.py            # Unified actions interface
├── assertions/                 # Comprehensive assertion library
│   ├── app_state_assertions.py        # App state and orientation validations
│   ├── attribute_assertions.py        # Element attribute checking
│   ├── count_list_assertions.py       # Element counting and list validations
│   ├── element_state_assertions.py    # Element state (enabled/disabled/selected)
│   ├── event_assertions.py            # Event triggering and log validation
│   ├── position_size_assertions.py    # Element positioning and sizing
│   ├── styling_assertions.py          # Color and styling validations
│   ├── text_assertions.py             # Text content validations
│   ├── visibility_assertions.py       # Element visibility checking
│   └── watching_assertions.py         # Continuous element monitoring
├── artifacts/                  # Test execution artifacts
│   ├── device_logs/           # Device-specific logs per test case
│   ├── logs/                  # Framework and test execution logs
│   ├── results/               # JSON test results and reports
│   ├── screenshots/           # Test screenshots organized by test case
│   └── videos/                # Execution recordings per test case
├── config/                     # Configuration files
│   ├── database.yaml          # Database connection settings
│   ├── framework.yaml         # Framework configuration and settings
│   └── healing_config.yaml    # Self-healing locator configuration
├── core/                       # Core framework components
│   ├── driver_manager.py      # Driver initialization and management
│   ├── executor.py            # Test execution engine
│   └── helpers.py             # Utility functions and artifact management
├── scripts/                    # Utility and helper scripts
│   ├── cpu_helper.py          # CPU monitoring and optimization
│   ├── make_report.py         # Test report generation
│   └── selector_transformer.py # Unified element finder
├── test_suite/                 # Test definitions and data
│   ├── locators/              # Element locators with fallback strategies
│   ├── steps/                 # Reusable step definitions
│   └── test_cases/            # YAML test case definitions
└── utils/                      # Utility modules
    ├── db_connection.py       # Database connectivity
    ├── device_logs.py         # Device log collection
    ├── logger.py              # Logging configuration
    └── yaml_loader.py         # YAML file processing
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- ADB (Android Debug Bridge)
- Android device/emulator
- Java 8+ (for Appium)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd mobile-automation-framework

# Install dependencies
pip install -r requirements.txt

# Configure ADB path (if needed)
export PATH=$PATH:/path/to/android-sdk/platform-tools
```

### Requirements
```bash
appium-python-client>=2.11.1
uiautomator2>=2.16.23
selenium>=4.15.0
pyyaml>=6.0.1
requests>=2.31.0
pillow>=10.0.1
```

## 🚀 Quick Start

### 1. Configure Framework
Edit `config/framework.yaml`:
```yaml
devices:
  - udid: "your_device_serial"
    driver: "uiautomator2"  # or "appium"
    platform: "android"

artifacts:
  screenshots:
    enabled: true
    on_failure: true
  videos:
    enabled: false
  logs:
    level: "INFO"
```

### 2. Define Locators
Create locators in `test_suite/locators/app_locators.yaml`:
```yaml
login_button:
  primary:
    type: "xpath"
    value: "//android.widget.Button[@text='Login']"
  fallback_1:
    type: "id" 
    value: "com.app:id/login_btn"

username_field:
  primary:
    type: "id"
    value: "com.app:id/username"
  fallback_1:
    type: "xpath"
    value: "//android.widget.EditText[@hint='Username']"
```

### 3. Create Test Steps
Define reusable steps in `test_suite/steps/login_steps.yaml`:
```yaml
launch_app:
  name: "Launch Application"
  action: "launch_app"
  parameters:
    app_package: "com.example.app"
  configs:
    force_stop: true

enter_credentials:
  name: "Enter Login Credentials"
  action: "type_text"
  parameters:
    locator_key: "username_field"
    text: "testuser@example.com"
    clear_first: true
  configs:
    hide_keyboard: true
    verify_text: true
```

### 4. Write Test Cases
Create test case in `test_suite/test_cases/TC001.yaml`:
```yaml
test_metadata:
  name: "User Login Test"
  description: "Test successful user login flow"
  tags: ["login", "smoke"]
  priority: "high"

test_steps:
  - step_id: "launch_app"
    configs:
      timeout: 30
  
  - step_id: "enter_credentials"
    configs:
      typing_delay: 0.1
  
  - step_id: "click_login"
    action: "click"
    parameters:
      locator_key: "login_button"
  
  - step_id: "verify_login_success"
    action: "assert"
    parameters:
      assertion_type: "visible"
      locator_key: "dashboard_header"
      timeout: 15
```

### 5. Run Tests
```bash
# Run single test case
python run_framework.py --tc TC001 --env dev

# Run multiple test cases
python run_framework.py --tc TC001,TC002 --env staging

# Run with specific device
python run_framework.py --tc TC001 --device DEVICE_SERIAL
```

## 📚 Usage Examples

### Text Input Actions
```yaml
- step_id: "enter_email"
  action: "type_text"
  parameters:
    locator_key: "email_field"
    text: "user@example.com"
    clear_first: true
  configs:
    typing_delay: 0.1
    hide_keyboard: true
    verify_text: true

- step_id: "clear_search"
  action: "clear_text"
  parameters:
    locator_key: "search_field"
  configs:
    method: "select_all"
```

### Gesture Actions with Fallback
```yaml
- step_id: "find_menu_item"
  action: "swipe_until_visible"
  parameters:
    target: "settings_menu_item"
  configs:
    direction: "down"
    fallback_direction: "up"
    max_swipe: 10
    selector: "menu_scroll_area"

- step_id: "collect_products"
  action: "swipe_and_collect_children"
  parameters:
    parent: "product_list"
    child_selector:
      type: "class"
      value: "product_card"
  configs:
    direction: "down"
    max_swipe: 15
```

### Device Control
```yaml
- step_id: "enable_airplane_mode"
  action: "set_airplane_mode"
  parameters:
    enabled: true

- step_id: "take_screenshot"
  action: "take_screenshot"
  parameters:
    filename: "login_screen.png"
    path: "./artifacts/screenshots"

- step_id: "set_volume"
  action: "set_volume"
  parameters:
    level: 8
    stream: "media"
```

### Advanced Assertions
```yaml
- step_id: "wait_for_loading"
  action: "assert"
  parameters:
    assertion_type: "element_appears"
    locator_key: "loading_spinner"
    wait_timeout: 5
    check_interval: 0.2

- step_id: "verify_content_loaded"
  action: "assert"
  parameters:
    assertion_type: "element_appears_with_text"
    locator_key: "content_area"
    expected_text: "Welcome"
    wait_timeout: 20
    check_interval: 1.0

- step_id: "wait_for_stable_ui"
  action: "assert"
  parameters:
    assertion_type: "element_appears_and_stable"
    locator_key: "main_content"
    stability_duration: 3.0
    wait_timeout: 15
```

## ⚙️ Configuration

### Framework Configuration (`config/framework.yaml`)
```yaml
# Device settings
devices:
  - udid: "emulator-5554"
    driver: "uiautomator2"
    platform: "android"
    app_package: "com.example.app"

# Artifact settings
artifacts:
  screenshots:
    enabled: true
    on_failure: true
    on_step: false
  videos:
    enabled: true
    quality: "medium"
  logs:
    level: "DEBUG"
    max_size: "10MB"

# Execution settings
execution:
  implicit_wait: 10
  page_load_timeout: 30
  script_timeout: 60
  retry_attempts: 2

# Healing settings
healing:
  enabled: true
  fallback_attempts: 3
  screenshot_on_heal: true
```

### Self-Healing Configuration (`config/healing_config.yaml`)
```yaml
healing_strategies:
  - name: "text_similarity"
    enabled: true
    threshold: 0.8
  - name: "xpath_recovery"
    enabled: true
  - name: "id_fallback"
    enabled: true

fallback_selectors:
  priority_order:
    - "id"
    - "xpath"
    - "class"
    - "accessibility_id"
    - "text"
```

## 🔧 Advanced Features

### Viewport-Aware Element Detection
The framework ensures elements are actually visible in the device viewport before interaction:
```python
def _is_element_visible(self, element_key):
    # Checks element existence, visibility flag, and viewport bounds
    # Validates minimum visible area (5x5 pixels)
    # Works with both UIAutomator2 and Appium
```

### Continuous Element Watching
Monitor elements in real-time until conditions are met:
```yaml
- step_id: "monitor_upload_progress"
  action: "assert"
  parameters:
    assertion_type: "element_changes_text"
    locator_key: "progress_label"
    initial_text: "0%"
    wait_timeout: 60
    check_interval: 2.0
```

### Intelligent Locator Fallback
Automatic fallback through multiple locator strategies:
```yaml
submit_button:
  primary:
    type: "id"
    value: "submit_btn"
  fallback_1:
    type: "xpath"
    value: "//android.widget.Button[@text='Submit']"
  fallback_2:
    type: "accessibility_id"
    value: "Submit Button"
```

## 📊 Reporting

### Execution Results
Test results are automatically generated in `artifacts/results/results.json`:
```json
{
  "test_case_id": "TC001",
  "status": "PASSED",
  "execution_time": "45.23s",
  "steps": [
    {
      "step_id": "launch_app",
      "status": "PASSED", 
      "duration": "3.2s",
      "screenshot": "step_1_screenshot.png"
    }
  ],
  "artifacts": {
    "screenshots": ["screenshot1.png", "screenshot2.png"],
    "videos": ["execution.mp4"],
    "logs": ["TC001.log"]
  }
}
```

### Generate Reports
```bash
# Generate HTML report
python scripts/make_report.py --format html --output reports/

# Generate detailed analysis
python scripts/make_report.py --format detailed --include-screenshots
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python run_framework.py --all

# Run specific tags
python run_framework.py --tags smoke,regression

# Run with parallel execution
python run_framework.py --parallel --workers 3

# Debug mode with detailed logging
python run_framework.py --tc TC001 --debug
```

### Debugging
```bash
# Enable debug logging
export FRAMEWORK_LOG_LEVEL=DEBUG

# Take screenshots on every step
export SCREENSHOT_ON_STEP=true

# Record execution video
export RECORD_VIDEO=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 . --max-line-length=120
```

## 📋 Roadmap

- [ ] iOS support with XCUITest driver
- [ ] Web application testing integration
- [ ] AI-powered test generation
- [ ] Cloud device integration (BrowserStack, Sauce Labs)
- [ ] Performance testing capabilities
- [ ] Visual regression testing
- [ ] API testing integration

## 🐛 Troubleshooting

### Common Issues

**Device not found**
```bash
# Check device connection
adb devices

# Restart ADB server
adb kill-server && adb start-server
```

**Element not found**
- Check locators in `test_suite/locators/`
- Enable healing mode in configuration
- Add fallback locators
- Verify app version compatibility

**Execution timeout**
- Increase timeout values in configuration
- Check device performance
- Verify network connectivity

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for robust mobile automation testing**