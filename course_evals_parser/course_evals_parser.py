from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

class CourseEvalsParser:
    LINK = "https://course-evals.utoronto.ca/BPI/fbview.aspx?blockid=OjzZ9-LrM-peMm6q2u&userid=cYQTzF-3fo2ufLLGH26rS-YRliCjyxiGeI8T&lng=en"
    PAGES = None

    def __init__(self):
        pass

    @staticmethod
    def parse():
        """docstring"""

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
            print("Table found!")

        # record the number of pages that need to be parsed
        pages_selector = "#fbvGridPagingContentHolderLvl1 table.gPaging tbody tr td:nth-child(n+5):nth-child(-n+5)"
        CourseEvalsParser.PAGES = int(driver.find_element(By.CSS_SELECTOR, pages_selector).text)

        data = []  # this will store the course eval data

        # for i in range(CourseEvalsParser.PAGES):
        for i in range(10):
            print(f"Parsing page {i+1}/{CourseEvalsParser.PAGES}")

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

if __name__ == "__main__":
    CourseEvalsParser.parse()
