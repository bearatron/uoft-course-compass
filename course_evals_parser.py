"""University of Toronto Course Evaluation Scraper.

This module provides the `CourseEvalsParser` class, an automated web scraper
built with Selenium WebDriver. It is designed to navigate the UofT course
evaluations portal, interact with search filters and dropdowns, handle
paginated data tables, and extract historical course ratings and metrics
into a structured CSV format for further analysis.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from web_element_helper import WebElementHelper
import time
import csv


class CourseEvalsParser:
    """A class for parsing the course evals website

    This class contains all static methods.
    """
    # Static Attributes:
    #   - LINK: a string storing the URL of UofT's course evals website
    LINK = ("https://course-evals.utoronto.ca/BPI/fbview.aspx?blockid=OjzZ9-LrM-peMm6q2u&userid=cYQTzF-3fo2ufLLGH26rS"
            "-YRliCjyxiGeI8T&lng=en")

    def __init__(self) -> None:
        pass

    @staticmethod
    def parse_all() -> None:
        """Scrapes the entire course evals table and outputs the result in a csv file
        WARNING: This will take an extremely long time to execute because there are ~4500 pages (~45,000 rows) of data
        This method is for demonstration purposes only and is not called anywhere
        """

        # create a webdriver and go to the link
        driver = webdriver.Chrome()
        driver.get(CourseEvalsParser.LINK)

        # output will be stored in all_courses.csv
        CourseEvalsParser._parse_table(driver, "all_courses")

        print("Full parse completed!")
        driver.quit()  # close the browser after we're done

    @staticmethod
    def parse_department(dept_name: str) -> None:
        """Scrapes all course eval data under the department specified by dept_name
        The scraper enters dept_name into the department name field and selects the first result from the dropdown menu

        Preconditions
            - dept_name is a valid department name and is present in the dropdown menu
        """
        # create a new webdriver and go to the link
        driver = webdriver.Chrome()
        driver.get(CourseEvalsParser.LINK)

        # an object representing the maximum amount of seconds to wait before timing out
        wait = WebDriverWait(driver, 10)

        # course eval table should be in view before scraping it
        course_eval_table = WebElementHelper(
            By.ID,
            "fbvGrid",
            "course eval table",
            wait
        )

        find_course_eval_table = course_eval_table.find_on_page(check_stale=False)

        if not find_course_eval_table.success:
            driver.quit()
            return

        # the department input text field should be in view
        dept_input = WebElementHelper(
            By.ID,
            "txtFbvSubjectsValues",
            "department input field",
            wait
        )

        find_dept_input = dept_input.find_on_page(check_stale=False)
        if not find_dept_input:
            driver.quit()
            return

        dept_input.web_element.clear()  # clear the text inside the department text field
        dept_input.web_element.send_keys(dept_name)  # type the department name in the text field
        dept_input.web_element.click()  # click on the text field so the dropdown loads

        # short pause to let the dropdown load into view
        time.sleep(2)

        # ensure the first result of the dropdown is loaded
        dept_dropdown_first_result = WebElementHelper(
            By.ID,
            dept_name,
            "first result of department dropdown",
            wait
        )

        find_dept_dropdown_first_result = dept_dropdown_first_result.find_on_page(check_stale=False)
        if not find_dept_dropdown_first_result.success:
            driver.quit()
            return

        # click the first result in the dropdown
        # this will filter the course eval table to only include the courses in the department we want
        dept_dropdown_first_result.web_element.click()
        print("Department dropdown clicked")

        # small pause to let table load into view
        time.sleep(2)

        print("Parsing table")
        CourseEvalsParser._parse_table(driver, dept_name.lower().replace(" ", "_"))

        print(f"Parse for {dept_name} department completed!")
        driver.quit()  # close the browser after we're done

    @staticmethod
    def _parse_table(driver: webdriver.chrome.webdriver.WebDriver, output_filename: str) -> None:
        """Parse the course eval table given a webdriver.
        Results will be stored in a csv with output_filename as the file name
        driver does NOT quit after function execution

        Preconditions:
            - driver.get(CourseEvalsParser.LINK) has been called
        """
        # wait object representing a timeout of 10 seconds
        wait = WebDriverWait(driver, 10)

        # make sure the course eval table is present before parsing it
        course_eval_table = WebElementHelper(
            By.ID,
            "fbvGrid",
            "course eval table",
            wait
        )

        find_course_eval_table = course_eval_table.find_on_page(check_stale=False)

        if not find_course_eval_table.success:
            driver.quit()
            return

        # record the number of pages that need to be parsed
        page_count = WebElementHelper(
            By.CSS_SELECTOR,
            "#fbvGridPagingContentHolderLvl1 > table.gPaging > tbody > tr > td:nth-child(n+5):nth-child(-n+5)",
            "page count element",
            wait
        )

        find_page_count = page_count.find_on_page(check_stale=False)
        if not find_page_count.success:
            driver.quit()
            return

        # the number of pages is stored as a string, we want an int
        num_pages = int(page_count.web_element.text)

        for i in range(num_pages):
            print(f"Parsing page {i+1}/{num_pages}")
            CourseEvalsParser._parse_page(driver, wait, course_eval_table, output_filename)

    @staticmethod
    def _parse_page(
            driver: webdriver.chrome.webdriver.WebDriver,
            wait: WebDriverWait,
            course_eval_table: WebElementHelper,
            output_filename: str
    ) -> None:
        """Parse a page in the course eval table

        Preconditions:
            - driver.get(CourseEvalsParser.LINK) has been called
        """

        # find the WebElements of each row in the table
        rows = driver.find_elements(By.CSS_SELECTOR, "#fbvGrid tr.gData")

        for row in rows:
            new_data_row = []  # this stores the columns of the current row in the table as strings

            # finds the WebElements of all the columns in the current row
            cols = row.find_elements(By.XPATH, ".//td")

            for col in cols:
                new_data_row.append(col.text)  # only append plaintext data to new_data_row

            print(new_data_row)

            # append the new row to the csv file (if it exists)
            # if the csv file has not been created, it will automatically be created and the row appended
            with open(f"{output_filename}.csv", "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(new_data_row)

        # make sure the next page button is visible so we can click it
        next_page_button = WebElementHelper(
            By.CSS_SELECTOR,
            "#fbvGridSearchBarLvl1 #fbvGridPagingContentHolderLvl1 input[value='>']",
            "next page button",
            wait
        )

        find_next_page_button = next_page_button.find_on_page(check_stale=False)
        if not find_next_page_button.success:
            driver.quit()
            return

        # navigate to the next page
        next_page_button.web_element.click()

        # upon loading the next page, the current one will be stale (since it has been removed from the DOM)
        # so we must update our reference to it
        course_eval_table.find_on_page(check_stale=True)

    @staticmethod
    def demo():
        """A demo function that showcases the parse's capabilities
        Scrapes the first two pages of the course eval table
        Stores the result in demo.csv
        """
        print("Demo started")

        # create a webdriver and go to the link
        driver = webdriver.Chrome()
        driver.get(CourseEvalsParser.LINK)

        # wait object representing a timeout of 10 seconds
        wait = WebDriverWait(driver, 10)

        # make sure the course eval table is present before parsing it
        course_eval_table = WebElementHelper(
            By.ID,
            "fbvGrid",
            "course eval table",
            wait
        )

        find_course_eval_table = course_eval_table.find_on_page(check_stale=False)

        if not find_course_eval_table.success:
            driver.quit()
            return

        # clear the contents of the demo file
        with open("demo.csv", 'w') as file:
            pass

        # parse only the first two pages for demonstration purposes
        for i in range(2):
            CourseEvalsParser._parse_page(driver, wait, course_eval_table, "demo")

        print("Demo parse completed!")
        driver.quit()


if __name__ == "__main__":
    CourseEvalsParser.demo()
    # CourseEvalsParser.parse_department("Computer Science")
    # CourseEvalsParser.parse_department("Statistical Sciences")
    # CourseEvalsParser.parse_department("Mathematics")
    # CourseEvalsParser.parse_department("Economics")
    # CourseEvalsParser.parse_department("Physics")

    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': [],
        'disable': ['static_type_checker'],
    })
