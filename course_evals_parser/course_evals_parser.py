import time

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from web_element_helper import WebElementHelper
import csv


class CourseEvalsParser:
    """ <class description>

    Representation Invariants
        - ...
    """
    # Static Attributes:
    #   - ...
    LINK = ("https://course-evals.utoronto.ca/BPI/fbview.aspx?blockid=OjzZ9-LrM-peMm6q2u&userid=cYQTzF-3fo2ufLLGH26rS"
            "-YRliCjyxiGeI8T&lng=en")

    def __init__(self) -> None:
        pass

    @staticmethod
    def parse_all() -> None:
        """Scrapes all courses and outputs the result in a csv file
        WARNING: This will take a reeaally long time because the scraper will go page by page and there are ~4500 pages
        """

        # create a webdriver and go to the link
        driver = webdriver.Chrome()
        driver.get(CourseEvalsParser.LINK)

        CourseEvalsParser.parse_table(driver, "all_courses")

        driver.quit()

    @staticmethod
    def parse_department(dept_name: str) -> None:
        """Scrapes all courses in the department specified by dept_name
        The scraper enters dept_name into the department name field and selects the first result from the dropdown menu

        Preconditions
            - dept_name is a valid department name
        """
        driver = webdriver.Chrome()
        driver.get(CourseEvalsParser.LINK)
        wait = WebDriverWait(driver, 10)

        course_eval_table = WebElementHelper(
            By.ID,
            "fbvGrid",
            "course eval table",
            wait
        )

        find_course_eval_table = course_eval_table.find_on_page(check_stale=False)

        if not find_course_eval_table.success:
            return

        dept_input = WebElementHelper(
            By.ID,
            "txtFbvSubjectsValues",
            "department input field",
            wait
        )

        find_dept_input = dept_input.find_on_page(check_stale=False)
        if not find_dept_input:
            return

        dept_input.web_element.clear()
        dept_input.web_element.send_keys(dept_name)
        dept_input.web_element.click()

        # small pause to let dropdown load into view
        time.sleep(2)

        dept_dropdown_first_result = WebElementHelper(
            By.ID,
            dept_name,
            "first result of department dropdown",
            wait
        )

        find_dept_dropdown_first_result = dept_dropdown_first_result.find_on_page(check_stale=False)
        if not find_dept_dropdown_first_result.success:
            return

        dept_dropdown_first_result.web_element.click()
        print("Department dropdown clicked")

        # small pause to let table load into view
        time.sleep(2)

        print("Parsing table")
        CourseEvalsParser.parse_table(driver, dept_name.lower().replace(" ", "_"))

        driver.quit()

    @staticmethod
    def parse_table(driver: webdriver.chrome.webdriver.WebDriver, output_filename: str) -> None:
        """Parse the course eval table given a webdriver.
        Results will be stored in output_filename.csv
        driver does NOT quit after function execution

        Preconditions:
            - driver object has been initialized
            - driver.get(CourseEvalsParser.LINK) has been called
        """

        wait = WebDriverWait(driver, 10)

        course_eval_table = WebElementHelper(
            By.ID,
            "fbvGrid",
            "course eval table",
            wait
        )

        find_course_eval_table = course_eval_table.find_on_page(check_stale=False)

        if not find_course_eval_table.success:
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
            return

        num_pages = int(page_count.web_element.text)

        data = []  # this will store the course eval data

        for i in range(num_pages):
            print(f"Parsing page {i+1}/{num_pages}")

            # find the WebElements of each row in the table
            rows = driver.find_elements(By.CSS_SELECTOR, "#fbvGrid tr.gData")

            for row in rows:
                new_data_row = []  # this will store the plaintext data corresponding to the row data for each course

                cols = row.find_elements(By.XPATH, ".//td")  # finds all the columns in each row's data as WebElements

                for col in cols:
                    new_data_row.append(col.text)  # only append plaintext data to new_data_row

                print(new_data_row)
                data.append(new_data_row)

                # append new row to csv
                # TODO: add a "seen" set and only append rows if they have not been seen to avoid duplicates
                with open(f"{output_filename}.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(new_data_row)

            next_page_button = WebElementHelper(
                By.CSS_SELECTOR,
                "#fbvGridSearchBarLvl1 #fbvGridPagingContentHolderLvl1 input[value='>']",
                "next page button",
                wait
            )

            find_next_page_button = next_page_button.find_on_page(check_stale=False)
            if not find_next_page_button.success:
                return

            next_page_button.web_element.click()

            course_eval_table.find_on_page(check_stale=True)

    @staticmethod
    def driver_init():
        ...


if __name__ == "__main__":
    pass
    # CourseEvalsParser.parse_all()
    # CourseEvalsParser.parse_department("Computer Science")
    # CourseEvalsParser.parse_department("Statistical Sciences")
    # CourseEvalsParser.parse_department("Mathematics")
    # CourseEvalsParser.parse_department("Economics")
    # CourseEvalsParser.parse_department("Physics")
