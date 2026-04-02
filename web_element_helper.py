"""Docstring  # TODO: insert docstring

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from dataclasses import dataclass
from typing import Optional
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class ReturnStatus:
    """A custom datatype representing the return status of find_on_page"""
    success: bool
    web_element: Optional[WebElement]


class WebElementHelper:
    """A class containing helpful methods for Selenium WebElements

    Representation Invariants
        - self._locator_type in {By.XPATH, By.ID, By.CSS_SELECTOR}
    """
    # Private Instance Attributes:
    #   - _locator_type: a string representing the selector type (e.g. By.ID)
    #   - _locator_str: a string representing the locator
    #   - _description: a short plaintext description of the element (used for return messages)
    #   - _wait: the wait object required by Selenium
    # Instance Attributes:
    #   - web_element: a Selenium WebElement, will get mutated when find_on_page is called

    _locator_type: str
    _locator_str: str
    _description: str
    _wait: WebDriverWait
    web_element: Optional[WebElement]

    def __init__(self, locator_type: str, locator_str: str, description: str, wait: WebDriverWait):
        """
        Initialize a new SeleniumElement class
        self.web_element starts as None, it gets initialized when find_on_page is called
        """
        self._locator_type = locator_type
        self._locator_str = locator_str
        self._description = description.lower()
        self._wait = wait
        self.web_element = None

    def find_on_page(self, check_stale: bool = False) -> ReturnStatus:
        """
        Find the element on the page using locator_type and locator_str
        Prints a status message to the console before returning
        Returns a ReturnStatus object
        """
        try:
            if check_stale:
                if self.web_element is None:
                    print(f"{self._description.capitalize()} is None, try calling this function with check_stale = "
                          f"False first")
                    return ReturnStatus(False, None)

                # wait till the element is removed from the DOM before searching for it again
                self._wait.until(
                    EC.staleness_of(self.web_element)
                )

            # search for the element on the website
            self.web_element = self._wait.until(
                EC.visibility_of_element_located((self._locator_type, self._locator_str))
            )
        except TimeoutException:
            print(f"{self._description.capitalize()} was not located or took too long to load")
            return ReturnStatus(False, None)
        else:
            print(f"{self._description.capitalize()} found")
            return ReturnStatus(True, self.web_element)
