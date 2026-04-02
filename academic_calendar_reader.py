"""A collection of methods used to load and parse information from the U of T Academic Calendar website

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from bs4 import BeautifulSoup
import requests
import json

from course_tree import CourseTree
import string_methods


# A dictionary mapping tokens to the tokens that can precede them
CAN_PRECEDE = {
    '/': {')', 'CODE'},
    ',': {')', 'CODE'},
    '(': {'/', ',', '(', 'START'},
    ')': {'/', ',', '(', ')', 'CODE'},
    'CODE': {'/', ',', '(', 'START'}
}


def _is_at_end(prerequisite_string: str, i: int) -> bool:
    """Return whether the given index marks the end of the prerequiste string. The end of the prerequisites is not
    necessarily the last character of the string

    >>> prereq = '... Prerequisite for Faculty of Applied Science and Engineering students: ECE421H1/ ROB313H1'
    >>> _is_at_end(prereq, 4)
    True
    >>> prereq = '... Notes: students enrolled in ASMAJ1446A who have ...'
    >>> _is_at_end(prereq, 4)
    True
    >>> prereq = '... Notes: students enrolled in ASMAJ1446A who have ...'
    >>> _is_at_end(prereq, 3)
    False
    """

    ending_strings = ['. ', 'Notes', 'Prerequisite for Faculty', 'For FASE']

    # Check against ending_strings:
    for string in ending_strings:
        # Check if the subsequent string is one of the ending strings
        if prerequisite_string[i:i + len(string)] == string:
            return True

    # The index does not mark the beginning of one of the ending strings, so it is not at the end
    return False


def _get_curr_and_prev_token(prerequisite_string: str, sanitized: str, i: int) -> tuple[str, str, int]:
    """Given the prerequisite string and the current sanitized version so far, return a tuple containing what the
    current and previous token types are, and the length of the current token in that order.
    Each token is one of {'/', ',', '(', ')', 'CODE', 'START', ''}.
    The length of each token is 1, except the length for 'CODE' is 8.

    >>> _get_curr_and_prev_token('Prerequisites: CSC110Y1/CSC111H1', '', 15)
    ('CODE', 'START', 8)
    >>> _get_curr_and_prev_token('Prerequisites: CSC110Y1/CSC111H1', '', 0)
    ('', 'START', 1)
    >>> _get_curr_and_prev_token('Prerequisites: CSC110Y1/CSC111H1', 'CSC110Y1', 23)
    ('/', 'CODE', 1)
    """
    # Determine what the current token is
    current = ''
    if prerequisite_string[i] in {'/', ',', '(', ')'}:
        current = prerequisite_string[i]
    # Check whether the subsequent string is a course code
    elif string_methods.is_course_code(prerequisite_string[i:i + 8]):
        current = 'CODE'

    # Determine what the previous token is
    if sanitized == '':
        # There is no previous token, it is at the start
        previous = 'START'
    elif sanitized[-1] in {'/', ',', '(', ')'}:
        previous = sanitized[-1]
    else:
        # The previous token is in the string so it must be legal. The only other thing it could be is a Course Code
        previous = "CODE"

    # Determine what the length of the current token is
    if current == 'CODE':
        length_of_current = 8
    else:
        length_of_current = 1

    return current, previous, length_of_current


def _search_for_grade(prerequisite_string: str, i: int) -> int:
    """Given a prerequisite string and an index, search for a grade requirement between in the section described by the
    previous and next connectives and return that requirement, or -1 if none were found

    Preconditions:
        - 0 <= i < len(prerequisite_string)

    >>> _search_for_grade('... /CSC110Y1 (70%)/ ...', 5)
    70
    >>> _search_for_grade('... ,MAT137Y1 with a minimum grade of 85%, ...', 5)
    85
    >>> _search_for_grade('... /at least 80% in PHY152H1/ ...', 5)
    80
    >>> _search_for_grade('... /PHY152H1/ ...', 5)
    -1
    """
    # Determine the location of the previous connective in the prerequisite string, determined by the index i
    previous_connective_index = prerequisite_string.replace(',', '/').rfind('/', 0, i)
    if previous_connective_index == -1:
        # No previous connective was found, so the starting search location is the start of the string
        previous_connective_index = 0

    # Determine the location of the next connective in the prerequisite string, determined by the index i
    next_connective_index = prerequisite_string.replace(',', '/').find('/', i)
    if next_connective_index == -1:
        # No next connective was found, so the ending search location is the end of the string
        next_connective_index = len(prerequisite_string)

    # Determine the location of a percent between the previous_ and next_connective_index
    percent_index = prerequisite_string.find('%', previous_connective_index, next_connective_index)
    # No percent was found, so there is no prerequisite grade requirement
    if percent_index == -1:
        return -1

    # The grade requirement is given by the two digits immediately preceding the percentage sign
    grade_requirement = int(prerequisite_string[percent_index - 2:percent_index])

    return grade_requirement


def _sanitize_prerequisites(prerequisite_string_raw: str) -> str:
    """Given the raw prerequisite string, return a properly formatted prerequisite string (as described in the project
    report)

    >>> prereq = 'CSC110Y1 (with a minimum mark of at least 85%) / CSC165H1 (with a minimum mark of at least 85%)'
    >>> _sanitize_prerequisites(prereq)
    'CSC110Y1[85]/CSC165H1[85]'
    >>> prereq = 'CSC436H1/ CSCD37H3/ 75% or greater in CSC336H1 / 75% or greater in CSC338H5/ 75% or greater in ' + \
                 'CSCC37H3/ equivalent mathematical background; CSC209H1/ proficiency in C, C++, or Fortran'
    >>> _sanitize_prerequisites(prereq)
    'CSC436H1[-1]/CSC336H1[75],CSC209H1[-1]'
    """
    # Standardize the notation used in the prerequisite strings
    prerequisite_string_raw = prerequisite_string_raw.strip() \
        .replace(';', ',') \
        .replace('[', '(') \
        .replace(']', ')') \
        .replace(' and ', '&')

    # We have to draw a distinction between these two strings for courses that say something like '77% in MAT135H1 and
    # MAT136H1'. If we naively replace ' and ' with ',' then we lose the prerequisite grade information for MAT136H1. We
    # keep two copies of the string so that one can be used when parsing the string and the other can be used when
    # searching for grade prerequisites.
    prerequisite_string = prerequisite_string_raw.replace('&', ',')

    sanitized = ''

    index = 0
    while index < len(prerequisite_string):
        # Check if the index is at the end of the prerequisite string and there is no more information to parse
        if _is_at_end(prerequisite_string, index):
            break

        # Get the current token and the previous token that was parsed, and the length of the current token
        current, previous, length_of_current = _get_curr_and_prev_token(prerequisite_string, sanitized, index)

        if current == '':
            # The current token is invalid, so we continue on to the next iteration
            index += length_of_current
            continue

        # The current token is valid, so we check if it can follow the previous token
        if previous in CAN_PRECEDE[current]:
            # The current token can follow the previous token, so we add it to the sanitized string
            if current == 'CODE':
                # Get the associated course's grade requirement (with the raw string for the reason described above)
                grade_requirement = _search_for_grade(prerequisite_string_raw, index)

                # Generate the properly formatted course code and append it to the sanitized string
                course_code = f'{prerequisite_string[index:index + 8]}[{grade_requirement}]'
                sanitized += course_code
            else:
                # The current token is not a course code so we just add it as is
                sanitized += current
        else:
            # The current token cannot follow the previous token, so we do not necessarily add it. There are two
            # special cases we must handle:
            # Case 1: If the current token is an open bracket, we must skip to the matching closed bracket because
            # nothing in between belongs
            if current == "(":
                index = prerequisite_string.find(")", index)

            # Case 2: if the current token is a comma and the previous token is a slash, then the comma
            # takes precendent over the slash
            if current == "," and previous == "/":
                sanitized = sanitized[:-1] + current

        # Increment the index for the next iteration by the length of the current token
        index += length_of_current

    # Remove any instances of empty brackets within the prerequisites string and any extra connectives
    # Also remove any connectives directly preceding empty brackets
    sanitized = _remove_extra_connectives(_remove_empty_brackets(sanitized))

    return sanitized


def _remove_empty_brackets(prerequisite_string: str) -> str:
    """Remove any instances of empty brackets from a prerequisite string. Empty brackets are those that contain only
    connectives and more brackets.

    Preconditions:
        - All parentheses are balanced

    >>> _remove_empty_brackets('CSC111H1/(),MAT137Y1')
    'CSC111H1/,MAT137Y1'
    >>> _remove_empty_brackets('(),MAT137Y1,((),/(),)/CSC111H1')
    ',MAT137Y1,/CSC111H1'
    >>> _remove_empty_brackets('(MAT137Y1,(/()))')
    '(MAT137Y1,)'
    """
    # Loop through every character in the prerequisite string
    index = 0
    while index < len(prerequisite_string):
        # Continue to the next character if the current character is not '('
        if prerequisite_string[index] != '(':
            index += 1
            continue

        # Determine whether the set of parentheses corresponding to the '(' at the current index are empty
        j = index + 1
        empty = True
        depth = 1
        while depth != 0:
            # Adjust the current depth value depending on whether there are nested parentheses
            if prerequisite_string[j] == '(':
                depth += 1
            elif prerequisite_string[j] == ')':
                depth -= 1

            # If there is a character that is not '(', ',', '/', or ')' then the parentheses are not empty
            if prerequisite_string[j] not in {'(', ',', '/', ')'}:
                empty = False

            j += 1

        if empty:
            # Then we know that j is the end parenthesis
            prerequisite_string = prerequisite_string[:index] + prerequisite_string[j:]
        else:
            index += 1

    return prerequisite_string


def _remove_extra_connectives(prerequisite_string: str) -> str:
    """Remove any extra connectives that are no longer contributing anything to the prerequisite string. These are due
    to connectives appearing in parts of the raw prerequisite string that are not in the properly formatted prerequisite
    string.

    >>> _remove_extra_connectives('MAT137Y1//CSC111H1')
    'MAT137Y1/CSC111H1'
    >>> _remove_extra_connectives('MAT137Y1,CSC111H1,')
    'MAT137Y1,CSC111H1'
    """
    if prerequisite_string != "":
        index = len(prerequisite_string) - 1
        while index >= 0:
            # Get the information about the current character
            char = prerequisite_string[index]
            is_connective = char in {',', '/'}

            # If it is not a connective, move on to the next character
            if not is_connective:
                index -= 1
                continue

            # There should be no connectives at the beginning or at the end
            if index == 0:
                prerequisite_string = prerequisite_string[1:]
                index -= 1
                continue
            elif index == len(prerequisite_string) - 1:
                prerequisite_string = prerequisite_string[:-1]
                index -= 1
                continue

            # Get the characters directly preceding and succeeding the current index
            # The characters are not at the beginning or the end so there are no worries with indices overflowing
            prev_char = prerequisite_string[index - 1]
            next_char = prerequisite_string[index + 1]

            # There should be no connectives after an open bracket or before a closed bracket
            if prev_char == '(' or next_char == ')':
                prerequisite_string = prerequisite_string[:index] + prerequisite_string[index + 1:]
                index -= 1
                continue

            # There should be no connectives adjacent to one another (we don't check next because we are looping back)
            if prev_char == ',':
                # The previous character takes priority so we remove the current character
                prerequisite_string = prerequisite_string[:index] + prerequisite_string[index + 1:]
                index -= 1
                continue
            elif prev_char == '/':
                # Since the previous character doesn't take priority we can remove it and keep the current character
                prerequisite_string = prerequisite_string[:index - 1] + prerequisite_string[index:]
                index -= 1
                continue

            index -= 1

    return prerequisite_string


def load_course_information(program: str) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """Return a tuple of two dictionaries: one mapping course codes to their properly formatted prerequisite strings for
    all courses in the specified program, the other mapping course codes to their full name and description

    Preconditions:
        - program is the name of a program on the U of T Academic Calendar
    """
    page_count = _get_number_of_pages(program)
    prerequisite_dictionary = {}
    information_dictionary = {}

    # Loop through all pages of courses for the given program
    for i in range(page_count):
        # Format the program name properly to be inserted into the url
        program = program.replace(' ', '+')

        # Load the webpage and extract the html data for the given program
        url = f'https://artsci.calendar.utoronto.ca/search-courses?field_section_value={program}&page={i}'
        webpage = requests.get(url)
        soup = BeautifulSoup(webpage.text, features='html.parser')

        # Find the section of the html corresponding to the list of courses on the current page
        course_divs = soup.find('div', class_='view-content') \
            .find_all('div', class_='views-row', recursive=False)
        # Loop through each course in the list of courses on the current page
        for course_div in course_divs:
            # Extract the course code and name
            course_name = course_div.find('div', attrs={'aria-label': True}).text.strip()
            course_code = course_name[0:8]
            # Extract the course description
            description = course_div.find('div', class_='views-field views-field-body') \
                .find('div', class_='field-content').text

            # Extract the prerequisite string
            prerequisite_span = course_div.find('span', class_='views-field views-field-field-prerequisite')
            if prerequisite_span:
                # A list of prerequisites was found for the current course, so extract and sanitize the data
                prerequisites = prerequisite_span.find('span', class_='field-content').text
                prerequisites = _sanitize_prerequisites(prerequisites)
            else:
                # No prerequistes were found for the given course
                prerequisites = ''

            # Add the course code and corresponding prerequisite string to the prerequisite dictionary
            prerequisite_dictionary[course_code] = prerequisites

            # Add the course code and corresponding name and description to the information dictionary
            information_dictionary[course_code] = (course_name, description)

    return prerequisite_dictionary, information_dictionary


def _get_number_of_pages(program: str) -> int:
    """Return the number of pages of courses a given program has in the academic calendar
    """
    # Format the program name properly to be inserted into the url
    program = program.replace(' ', '+')

    # Load the webpage and extract the html data for the given program
    url = f"https://artsci.calendar.utoronto.ca/search-courses?field_section_value={program}"
    webpage = requests.get(url)
    soup = BeautifulSoup(webpage.text, features='html.parser')

    # Find the button that links to the last page
    last_page = soup.find("a", title="Go to last page")

    if not last_page:
        # There was no last page button found, so there is only one page
        return 1
    else:
        # Get the number of pages from the url for the last page
        last_page_url = last_page.get("href")
        index = last_page_url.rfind("=")
        page_amount = int(last_page_url[index + 1:]) + 1

        return page_amount


def convert_to_tree(prerequisite_dict: dict[str, str]) -> dict[str, CourseTree]:
    """Return a dictionary mapping courses to course trees generated from the prerequisite string corresponding to the
    given course

    Preconditions:
        - Every prerequisite string in prerequisite_dict is properly formatted prerequisite string (as described in the
        project report)
    """
    return {
        course_code: CourseTree.generate_course_tree(prerequisite_dict[course_code], course_code)
        for course_code in prerequisite_dict
    }


class CourseNotFoundError(Exception):
    """Exception raised when attempting to access information about a non-existent course"""
    def __str__(self) -> str:
        """Return a string representation of this error."""
        return 'The course you are trying to access does not exist'


class PrerequisiteTreeLoader:
    """A class for loading information about courses from the Academic Calendar
    """
    # Private Instance Attributes:
    #   - _prerequisite_strings:
    #       The dictionary mapping course codes to their corresponding prerequisite strings
    #   - _prerequisite_trees:
    #       The dictionary mapping course codes to their corresponding prerequisite trees
    #   - _course_information:
    #       The dictionary mapping course codes to their corresponding full titles and descriptions
    _prerequisite_strings: dict[str, str]
    _prerequisite_trees: dict[str, CourseTree]
    _course_information: dict[str, tuple[str, str]]

    def __init__(self) -> None:
        # Initialize the dictionaries used to store course information
        self._prerequisite_strings = {}
        self._prerequisite_trees = {}
        self._course_information = {}

    def load_from_programs(self, programs: list[str]) -> None:
        """Load information and generate a prerequisite tree for every course in the given programs

        Preconditions:
            - Every program in programs is a program in the Academic Calendar
        """
        # Loop through every provided program and load the corresponding information for that program
        for program in programs:
            prerequisite_dictionary, information_dictionary = load_course_information(program)
            self._prerequisite_strings.update(prerequisite_dictionary)

            # Update the dictionaries to contain the new information
            self._prerequisite_trees.update(convert_to_tree(self._prerequisite_strings))
            self._course_information.update(information_dictionary)

        # Loop through every course and recursively add on prerequisites of prerequisites, etc.
        for course_code in self._prerequisite_trees:
            course_tree = self._prerequisite_trees[course_code]
            leaves = course_tree.get_course_leaves()
            for leaf in leaves:
                if leaf.get_root() in self._prerequisite_trees:
                    leaf.set_subtrees(self._prerequisite_trees[leaf.get_root()].get_subtrees())

    def get_prerequisite_tree(self, course_code: str) -> CourseTree:
        """Return the prerequisite tree that corresponds to the given course_code
        """
        if course_code not in self._prerequisite_trees:
            raise CourseNotFoundError

        return self._prerequisite_trees[course_code]

    def get_postrequisite_tree(self, course_code: str) -> CourseTree:
        """Return the postrequisite tree that corresponds to the given course_code
        """
        postrequisite_list = []
        for course in self._prerequisite_trees:
            tree = self._prerequisite_trees[course]
            if tree.is_prerequisite(course_code):
                postrequisite_list.append(CourseTree(course, -1, []))

        postrequisite_tree = CourseTree(course_code, -1, postrequisite_list)

        return postrequisite_tree

    def get_name_and_description(self, course_code: str) -> tuple[str, str]:
        """Return the name and description that correspond to the given course_code
        """
        if course_code not in self._course_information:
            raise CourseNotFoundError

        return self._course_information[course_code]

    def save_to_file(self, file_name: str) -> None:
        """Save all the data to a json file to be reloaded at a later time

        Preconditions:
            - file_name is a valid json file name
        """
        save_data = {
            "course_information": self._course_information,
            "prerequisite_strings": self._prerequisite_strings
        }
        with open(file_name, "w") as f:
            json.dump(save_data, f, indent=4)

    def load_from_file(self, file_name: str) -> None:
        """Load all data from a json file

        Preconditions:
            - file_name is a valid json file name corresponding to a file with properly formatted data
        """
        with open(file_name, "r") as f:
            save_data = json.load(f)

        self._course_information = save_data["course_information"]
        self._prerequisite_strings = save_data["prerequisite_strings"]

        # Load prerequisite trees from all prerequisite strings
        self._prerequisite_trees.update(convert_to_tree(self._prerequisite_strings))

        # Loop through every course and add on prerequisites of prerequisites, etc.
        for course_code in self._prerequisite_trees:
            course_tree = self._prerequisite_trees[course_code]
            leaves = course_tree.get_course_leaves()
            for leaf in leaves:
                if leaf.get_root() in self._prerequisite_trees:
                    leaf.set_subtrees(self._prerequisite_trees[leaf.get_root()].get_subtrees())


if __name__ == '__main__':
    # pass
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': [],
        'disable': ['static_type_checker'],
    })
