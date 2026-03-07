"""dosctring"""

from bs4 import BeautifulSoup  # TODO: NOT SURE IF I DOWNLOADED THIS OR NOT, SO SAY THAT IN THE WRITEUP IF NEEDED
import requests

from course_tree import CourseTree
from string_methods import *


class AcademicCalendarReader:
    """Docstring"""
    def __init__(self):
        pass

    @staticmethod
    def __is_at_end(prerequisite_string, i):
        # Strings that mark the end of the prerequisites
        ending_strings = [". ", "Notes:", "Prerequisite for Faculty", "For FASE"]

        # Check against ending_strings:
        for string in ending_strings:
            # Verify that there are enough characters left in the string to index
            if len(prerequisite_string) - i > len(string) - 1:
                # Check if the subsequent string is the ending string
                if prerequisite_string[i:i + len(string)] == string:
                    return True

        return False

    @staticmethod
    def __get_current_and_previous_token(prerequisite_string, sanitized, i) -> tuple[str, str]:
        # Determine what the current token is
        current = ""
        if prerequisite_string[i] in {"/", ",", "(", ")"}:
            current = prerequisite_string[i]
        # Check whether the subsequent string is a course code
        # Verify that there are enough characters left in the string to index
        if len(prerequisite_string) - i > 7:
            if is_course_code(prerequisite_string[i:i + 8]):
                current = "CODE"

        # Determine what the previous token is
        if sanitized == "":
            previous = "START"
        elif sanitized[-1] in {"/", ",", "(", ")"}:
            previous = sanitized[-1]
        else:
            # It's in the string so it must be legal, and the only other thing it could be is a code
            previous = "CODE"

        return current, previous

    @staticmethod
    def _search_for_grade(prerequisite_string: str, i: int) -> int:
        previous_connective_i = prerequisite_string.replace(",", "/").rfind("/", 0, i)
        if previous_connective_i == -1:
            previous_connective_i = 0
        next_connective_i = prerequisite_string.replace(",", "/").find("/", i)
        if next_connective_i == -1:
            next_connective_i = len(prerequisite_string)  # we don't subtract one because of reasons

        percent_i = prerequisite_string.find("%", previous_connective_i, next_connective_i)
        if percent_i == -1:
            return -1

        return int(prerequisite_string[percent_i-2:percent_i])

    @staticmethod
    def sanitize_prerequisites(prerequisite_string_old: str) -> str:
        """docstring"""
        prerequisite_string_old = prerequisite_string_old.strip()
        prerequisite_string_old = prerequisite_string_old.replace(";", ",")
        prerequisite_string_old = prerequisite_string_old.replace("[", "(")
        prerequisite_string_old = prerequisite_string_old.replace("]", ")")
        prerequisite_string = prerequisite_string_old.replace(" and ", ",")  # Have to do it this way because of CSC311

        sanitized = ""

        # A dictionary containing tokens and what can precede them
        can_precede = {
            "/": {")", "CODE"},
            ",": {")", "CODE"},
            "(": {"/", ",", "(", "START"},
            ")": {"/", ",", "(", ")", "CODE"},  # Needs to be able to follow everything to prevent unbalanaced brackets
            "CODE": {"/", ",", "(", "START"}
        }

        i = 0  # REMEMBER TO INCREMENT EVERYWHERE IT NEEDS TO BE INCREMENTED
        while i < len(prerequisite_string):
            if AcademicCalendarReader.__is_at_end(prerequisite_string, i):
                break

            current, previous = AcademicCalendarReader.__get_current_and_previous_token(
                prerequisite_string, sanitized, i
            )

            length_of_current = 8 if current == "CODE" else 1

            if current == "":
                # The current token is invalid, so we move onto the next token
                pass
            else:
                # The current token is valid, so we check if it can follow the previous token
                if previous in can_precede[current]:
                    # The current token can follow the previous token, so we add it to the sanitized string
                    if current == "CODE":
                        sanitized += prerequisite_string[i:i+8]
                        sanitized += f"[{(
                            AcademicCalendarReader._search_for_grade(
                                prerequisite_string_old.replace(" and ", "#"), i  # replace so indices align
                            )
                        )}]"
                    else:
                        sanitized += current
                else:
                    # The current token cannot follow the previous token, so we do not add it*.
                    # If the current token is an open bracket, so we must skip to the matching closed bracket because
                    # nothing in between belongs
                    if current == "(":
                        i = prerequisite_string.find(")", i)  # Remember that we increment by 1 again at the end

                    # Special case: if the current token is a comma and the previous token is a slash, then the comma
                    # takes precendent over the slash
                    if current == "," and previous == "/":
                        sanitized = sanitized[:-1] + current

            i += length_of_current

        # Remove any instances of empty brackets within the prerequisites string
        # Also remove any connectives directly preceding empty brackets
        while "()" in sanitized:
            index = sanitized.find("()")
            sanitized = sanitized[:index] + sanitized[index+2:]

            if index > 0 and sanitized[index - 1] in {",", "/"}:
                sanitized = sanitized[:index-1] + sanitized[index:]

        # Remove any trailing connectives that are a result of written prerequisites at the end
        # Note: these might not all be at the end of the string
        if sanitized != "":
            i = 0
            while i < len(sanitized):
                char = sanitized[i]
                is_connective = char in {',', '/'}
                if is_connective and i >= len(sanitized) - 1:  # There are some cases (e.g. MAT244H1) where i is greater
                    sanitized = sanitized[:-1]
                elif is_connective and sanitized[i + 1] == ")":
                    sanitized = sanitized[:i] + sanitized[i+1:]
                else:
                    i += 1  # we don't increment i in the other cases because they mutated the string

        return sanitized

    @staticmethod
    def load_course_prerequisites(program: str) -> dict[str, str]:
        """Docstring"""
        page_count = AcademicCalendarReader.get_number_of_pages(program)
        course_dictionary = {}
        for i in range(page_count):
            program = program.replace(" ", "+")
            url = f"https://artsci.calendar.utoronto.ca/search-courses?field_section_value={program}&page={i}"
            webpage = requests.get(url)
            soup = BeautifulSoup(webpage.text, features='html.parser')

            course_menu = soup.find("div", class_="view-content")
            course_divs = course_menu.find_all("div", class_="views-row", recursive=False)
            for course_div in course_divs:
                course_name = course_div.find("div", attrs={"aria-label": True}).text.strip()[0:8]
                prerequisite_span = course_div.find("span", class_="views-field views-field-field-prerequisite")
                if prerequisite_span:
                    prerequisites = prerequisite_span.find("span", class_="field-content").text
                    # TODO: I don't like how I have to run two passes on it...
                    prerequisites = AcademicCalendarReader.sanitize_prerequisites(prerequisites)
                    if prerequisites == "":
                        prerequisites = "N/A"

                else:
                    prerequisites = "N/A"
                course_dictionary[course_name] = prerequisites

        return course_dictionary

    @staticmethod
    def get_number_of_pages(program: str) -> int:
        """Docstring"""
        url = f"https://artsci.calendar.utoronto.ca/search-courses?field_section_value={program.replace(" ", "+")}"
        webpage = requests.get(url)
        soup = BeautifulSoup(webpage.text, features='html.parser')

        last_page_a = soup.find("a", title="Go to last page")

        if not last_page_a:
            # There was no last page button found, so there is only one page
            return 1
        else:
            last_page_url = last_page_a.get("href")
            index = last_page_url.rfind("=")
            page_amount = int(last_page_url[index+1:]) + 1
            return page_amount

    @staticmethod
    def convert_to_tree(prerequisite_dict: dict[str, str]) -> dict[str, CourseTree]:
        """Docstring"""
        return {
            course_code: CourseTree.generate_course_tree(prerequisite_dict[course_code], course_code)
            for course_code in prerequisite_dict
        }


if __name__ == "__main__":
    ...
