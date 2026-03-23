import time

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

class CourseEvalsParser:
    # Static Variables
    LINK = "https://course-evals.utoronto.ca/BPI/fbview.aspx?blockid=OjzZ9-LrM-peMm6q2u&userid=cYQTzF-3fo2ufLLGH26rS-YRliCjyxiGeI8T&lng=en"

    def __init__(self):
        pass

    @staticmethod
    def parse_all() -> None:
        """Scrapes all courses and outputs the result in a csv file
        WARNING: This will take a reeaally long time because the scraper will go page by page
        """

        # create a webdriver and go to the link
        driver = webdriver.Chrome()
        driver.get(CourseEvalsParser.LINK)
        wait = WebDriverWait(driver, 10)

        # make sure the course eval table loads before parsing it
        try:
            # wait till the table element appears
            table_element = wait.until(
                EC.visibility_of_element_located((By.ID, "fbvGrid"))
            )
        except TimeoutException:
            print("Course eval table took too long to load")
            return
        else:
            print("Course eval table found!")

        # record the number of pages that need to be parsed
        pages_selector = "#fbvGridPagingContentHolderLvl1 table.gPaging tbody tr td:nth-child(n+5):nth-child(-n+5)"
        num_pages = int(driver.find_element(By.CSS_SELECTOR, pages_selector).text)

        data = []  # this will store the course eval data

        # Use below for testing
        # for i in range(10):

        for i in range(num_pages):
            print(f"Parsing page {i+1}/{num_pages}")

            # find the WebElement of all the rows in the table
            # a WebElement is Selenium's way of representing an HTML element
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
                with open("course_evals.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(new_data_row)

            next_button_selector = "#fbvGridPagingContentHolderLvl1 table.gPaging tbody tr td input"
            next_button = driver.find_element(By.CSS_SELECTOR, next_button_selector)
            next_button.click()

            # make sure the course eval table loads before parsing it
            try:
                # wait till the table element is removed from the DOM before searching for it again
                wait.until(
                    EC.staleness_of(table_element)
                )

                # search for the new table
                table_element = wait.until(
                    EC.visibility_of_element_located((By.ID, "fbvGrid"))
                )

            except TimeoutException:
                print(f"Course eval table on page {i+2} took too long to load")
            else:
                print(f"Course eval table on page {i+2} found")

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

        try:
            # wait till the course table element appears
            table_element = wait.until(
                EC.visibility_of_element_located((By.ID, "fbvGrid"))
            )

            # wait till the dept input element appears
            dept_input_id = "txtFbvSubjectsValues"

            dept_input = wait.until(
                EC.visibility_of_element_located((By.ID, dept_input_id))
            )
        except TimeoutException:
            print("Course eval table or department input field took too long to load")
            return
        else:
            print("Course eval table and department input field found!")

        dept_input.clear()
        dept_input.send_keys(dept_name)
        time.sleep(2)

        try:
            # wait till the first element of the department dropdown appears
            dept_dropdown_first_elem = wait.until(
                EC.visibility_of_element_located((By.ID, dept_name))
            )
        except TimeoutException:
            print("Department dropdown took too long to load, or department name is invalid")
            return
        else:
            print("Department dropdown found!")

        dept_dropdown_first_elem.click()
        print("clicked")

        print("zzz")
        time.sleep(5)

        CourseEvalsParser.parse_table(driver, dept_name.lower().replace(" ", "_"))

        driver.quit()

    @staticmethod
    def parse_table(driver: webdriver.chrome.webdriver.WebDriver, output_filename: str) -> None:
        """Parse the course eval table given a webdriver.
        Results will be stored in output_filename.csv
        driver does NOT quit after function execution

        Preconditions:
            - driver.get(CourseEvalsParser.LINK) has been called
        """

        wait = WebDriverWait(driver, 10)

        # make sure the course eval table loads before parsing it
        try:
            # wait till the table element appears
            table_element = wait.until(
                EC.visibility_of_element_located((By.ID, "fbvGrid"))
            )
        except TimeoutException:
            print("Course eval table took too long to load")
            return
        else:
            print("Course eval table found!")

        # record the number of pages that need to be parsed
        pages_selector = "#fbvGridPagingContentHolderLvl1 table.gPaging tbody tr td:nth-child(n+5):nth-child(-n+5)"
        num_pages = int(driver.find_element(By.CSS_SELECTOR, pages_selector).text)

        data = []  # this will store the course eval data

        for i in range(num_pages):
            print(f"Parsing page {i+1}/{num_pages}")

            # find the WebElement of all the rows in the table
            # a WebElement is Selenium's way of representing an HTML element
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

            next_button_selector = "#fbvGridPagingContentHolderLvl1 table.gPaging tbody tr td input"
            next_button = driver.find_element(By.CSS_SELECTOR, next_button_selector)
            next_button.click()

            # make sure the course eval table loads before parsing it
            try:
                # wait till the table element is removed from the DOM before searching for it again
                wait.until(
                    EC.staleness_of(table_element)
                )

                # search for the new table
                table_element = wait.until(
                    EC.visibility_of_element_located((By.ID, "fbvGrid"))
                )

            except TimeoutException:
                print(f"Course eval table on page {i+2} took too long to load")
            else:
                print(f"Course eval table on page {i+2} found")




    @staticmethod
    def driver_init():
        ...


if __name__ == "__main__":
    # CourseEvalsParser.parse_all()
    CourseEvalsParser.parse_department("Computer Science")
