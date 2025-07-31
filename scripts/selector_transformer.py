"""
A minimal, extensible utility to convert generic mobile selectors into
framework-specific locators for Appium and UIAutomator2.
"""
from __future__ import annotations

from typing import Dict, Tuple, Union, Callable, Any

# Public interface -----------------------------------------------------------
__all__ = [
    "MobileSelectorTransformer",
    "UnifiedElementFinder",
]

# Type aliases
AppiumLocator = Tuple[str, str]
UiAutomator2Locator = Dict[str, str]
Locator = Union[AppiumLocator, UiAutomator2Locator]


class MobileSelectorTransformer:
    """Transforms *generic* selector names into framework-specific locators.

    Example
    -------
    >>> t = MobileSelectorTransformer()
    >>> t.transform_selector("id", "com.example:id/login", "appium")
    ('id', 'com.example:id/login')
    >>> t.transform_selector("text", "Settings", "uiautomator2")
    {'text': 'Settings'}
    """

    # Internal mapping table -------------------------------------------------
    # key: generic selector; value: mapping per framework
    # The mapping value is a tuple (target_key, value_transform_fn)
    _MAPPING: Dict[str, Dict[str, Tuple[str, Callable[[str], str]]]] = {
        "id": {
            "appium": ("id", lambda v: v),
            "uiautomator2": ("resourceId", lambda v: v),
        },
        "xpath": {
            "appium": ("xpath", lambda v: v),
            "uiautomator2": ("xpath", lambda v: v),
        },
        "text": {
            "appium": (
                "xpath",
                lambda v: f"//*[@text='{v}' or @label='{v}' or @name='{v}']",
            ),
            "uiautomator2": ("text", lambda v: v),
        },
        "text_contains": {
            "appium": (
                "xpath",
                lambda v: f"//*[contains(@text, '{v}') or contains(@label, '{v}') or contains(@name, '{v}')]",
            ),
            "uiautomator2": ("textContains", lambda v: v),
        },
        "text_starts_with": {
            "appium": (
                "xpath",
                lambda v: f"//*[starts-with(@text, '{v}') or starts-with(@label, '{v}') or starts-with(@name, '{v}')]",
            ),
            "uiautomator2": ("textStartsWith", lambda v: v),
        },
        "class": {
            "appium": ("class name", lambda v: v),
            "uiautomator2": ("className", lambda v: v),
        },
        "accessibility_id": {
            "appium": ("accessibility id", lambda v: v),
            "uiautomator2": ("description", lambda v: v),
        },
        # Boolean state selectors -------------------------------------------
        "clickable": {
            "appium": (
                "xpath",
                lambda v: f"//*[@clickable='{str(v).lower()}']",
            ),
            "uiautomator2": ("clickable", lambda v: str(v).lower()),
        },
        "enabled": {
            "appium": (
                "xpath",
                lambda v: f"//*[@enabled='{str(v).lower()}']",
            ),
            "uiautomator2": ("enabled", lambda v: str(v).lower()),
        },
        "checked": {
            "appium": (
                "xpath",
                lambda v: f"//*[@checked='{str(v).lower()}']",
            ),
            "uiautomator2": ("checked", lambda v: str(v).lower()),
        },
        "focused": {
            "appium": (
                "xpath",
                lambda v: f"//*[@focused='{str(v).lower()}']",
            ),
            "uiautomator2": ("focused", lambda v: str(v).lower()),
        },
        "selected": {
            "appium": (
                "xpath",
                lambda v: f"//*[@selected='{str(v).lower()}']",
            ),
            "uiautomator2": ("selected", lambda v: str(v).lower()),
        },
        # iOS-specific (Appium only) ----------------------------------------
        "ios_predicate": {
            "appium": ("-ios predicate string", lambda v: v),
            "uiautomator2": ("_unsupported", lambda v: v),
        },
        "ios_class_chain": {
            "appium": ("-ios class chain", lambda v: v),
            "uiautomator2": ("_unsupported", lambda v: v),
        },
        # Image selector (Appium only) --------------------------------------
        "image": {
            "appium": ("image", lambda v: v),
            "uiautomator2": ("_unsupported", lambda v: v),
        },
    }

    # Public API -------------------------------------------------------------
    def transform_selector(
        self, selector_type: str, selector_value: str, framework: str
    ) -> Locator:
        """Convert *selector_type* and *selector_value* into the desired format.

        Parameters
        ----------
        selector_type : str
            One of the *generic* selector names (e.g. "id", "text", "xpath").
        selector_value : str
            The actual locator string / value.
        framework : str
            Either "appium" or "uiautomator2" (case-insensitive).

        Returns
        -------
        Locator
            *Appium*  – (`by`, `value`) tuple compatible with
            ``driver.find_element``.
            
            *UIAutomator2* – kwargs dict for ``d(**kwargs)`` **or** a special
            dict `{ "xpath": <expr> }` when using XPath.
        """
        framework = framework.lower()
        selector_type_lc = selector_type.lower()

        if framework not in {"appium", "uiautomator2"}:
            raise ValueError(f"Unsupported framework: {framework}")

        if selector_type_lc not in self._MAPPING:
            raise ValueError(f"Unsupported selector type: {selector_type}")

        target_key, transform_fn = self._MAPPING[selector_type_lc][framework]

        if target_key == "_unsupported":
            raise ValueError(
                f"Selector '{selector_type}' is not available for framework '{framework}'"
            )

        transformed_value = transform_fn(selector_value)

        if framework == "appium":
            return target_key, transformed_value  # type: ignore[return-value]

        # UIAutomator2 branch -------------------------------------------------
        if target_key == "xpath":
            return {"xpath": transformed_value}
        return {target_key: transformed_value}

    # ---------------------------------------------------------------------
    def add_selector(
        self,
        generic_name: str,
        *,
        appium_config: Tuple[str, Callable[[str], str]] | None = None,
        uiautomator2_config: Tuple[str, Callable[[str], str]] | None = None,
    ) -> None:
        """Register a *new* generic selector at runtime.

        Parameters
        ----------
        generic_name : str
            Name of the new generic selector.
        appium_config, uiautomator2_config : tuple or None
            Mapping for each framework.  Each tuple must be of the form
            ``(target_key, transform_fn)`` where ``transform_fn`` accepts the
            raw *selector_value* and returns a *string* that will be used as
            the final locator value.
        """
        if generic_name in self._MAPPING:
            raise ValueError(f"Selector '{generic_name}' already exists.")

        self._MAPPING[generic_name] = {}
        if appium_config:
            self._MAPPING[generic_name]["appium"] = appium_config
        if uiautomator2_config:
            self._MAPPING[generic_name]["uiautomator2"] = uiautomator2_config


class UnifiedElementFinder:
    """Sugar-coated wrapper that hides framework differences entirely.

    Example
    -------
    >>> finder = UnifiedElementFinder(driver, 'appium')
    >>> finder.find_element('id', 'com.example:id/login').click()
    >>> finder = UnifiedElementFinder(device, 'uiautomator2')
    >>> finder.find_element('text', 'Logout').click()
    """

    def __init__(
        self, backend: Any, framework: str, *, transformer: MobileSelectorTransformer | None = None
    ) -> None:
        self.backend = backend
        self.framework = framework.lower()
        self.transformer = transformer or MobileSelectorTransformer()

        if self.framework not in {"appium", "uiautomator2"}:
            raise ValueError(f"Unsupported framework: {framework}")

        # Attempt to import Selenium/Appium "By" enum lazily ----------------
        if self.framework == "appium":
            try:
                from appium.webdriver.common.appiumby import AppiumBy as _By # type: ignore
            except Exception:  # pragma: no cover
                try:
                    from selenium.webdriver.common.by import By as _By  # type: ignore # fallback
                except Exception as exc:  # pragma: no cover
                    raise ImportError("Could not import Appium/Selenium By class") from exc
            self._By = _By

    # ------------------------------------------------------------------
    def find_element(self, selector_type: str, selector_value: str):
        """Find one element using a *generic* selector."""
        loc = self.transformer.transform_selector(selector_type, selector_value, self.framework)
        if self.framework == "appium":
            by, value = loc  # type: ignore[misc]
            by_enum = getattr(self._By, by.upper().replace(" ", "_"))
            return self.backend.find_element(by_enum, value)
        # UIAutomator2 branch
        if "xpath" in loc:  # type: ignore[arg-type]
            return self.backend.xpath(loc["xpath"])
        return self.backend(**loc)  # type: ignore[arg-type]

    def find_elements(self, selector_type: str, selector_value: str):
        """Find *all* matching elements using a *generic* selector."""
        loc = self.transformer.transform_selector(selector_type, selector_value, self.framework)
        if self.framework == "appium":
            by, value = loc  # type: ignore[misc]
            by_enum = getattr(self._By, by.upper().replace(" ", "_"))
            return self.backend.find_elements(by_enum, value)
        # UIAutomator2
        if "xpath" in loc:  # type: ignore[arg-type]
            return self.backend.xpath(loc["xpath"]).all()
        return self.backend(**loc).all()
