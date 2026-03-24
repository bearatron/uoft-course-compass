"""Various string methods that are useful for parsing course codes"""


def has_unnested(string: str, char: str) -> bool:
    """Return whether the given string has an instance of the given char that is not nested within parentheses

    Preconditions:
        - len(char) == 1 and char not in {'(', ')'}

    >>> has_unnested('CSC110Y1,MAT137Y1', ',')
    True
    >>> has_unnested('CSC110Y1/(MAT137Y1,MAT223H1)', ',')
    False
    """
    bracket_depth = 0

    # Loop through each character in the string, trying to find an unnested instance of the given character
    for character in string:
        # If the current character is an open bracket, increase the bracket depth
        if character == '(':
            bracket_depth += 1
        # If the current character is a closed bracket, decrease the bracket depth
        elif character == ')':
            bracket_depth -= 1
        # If the current character matches, and it is not nested within any parentheses, then return True
        elif character == char and bracket_depth == 0:
            return True

    # No instance of the character was found that was not nested
    return False


def unnested_split(string: str, split_char: str) -> list[str]:
    """Split the given string at all unnested instances (instances not within parentheses) of the provided char and
    return a list of all the strings.

    Preconditions:
        - len(split_char) == 1 and split_char not in {'(', ')'}

    >>> unnested_split('CSC110Y1,CSC111H1,(MAT137Y1,MAT223H1)', ',')
    ['CSC110Y1', 'CSC111H1', '(MAT137Y1,MAT223H1)']
    """
    bracket_depth = 0
    current_substring = ''
    all_items = []

    # Loop through each character in the string
    for char in string:
        # If the current character is an open bracket, increase the bracket depth
        if char == '(':
            bracket_depth += 1
        # If the current character is a closed bracket, decrease the bracket depth
        elif char == ')':
            bracket_depth -= 1

        # If the current character matches, and it is not nested within parentheses, append the current substring to the
        # list and begin a new current substring
        if char == split_char and bracket_depth == 0:
            all_items.append(current_substring)
            current_substring = ''
        # Otherwise, add the current character to the current substring
        else:
            current_substring += char

    # Add the last substring to the list, because it wasn't followed by a comma
    all_items.append(current_substring)
    return all_items


def is_course_code(string: str) -> bool:
    """Return whether the given string is a valid Course Code

    A valid Course Code is any string in the format XYZ###W1, where all the following are satisfied:
        - X, Y, and Z are any capital letters
        - ### is any three-digit code beginning with '1', '2', '3', or '4'
        - W is one of {'Y', 'H'}

    Note: this definition purposefully excludes codes for courses not offered at the St. George campus

    >>> is_course_code('CSC111H1')
    True
    >>> is_course_code('sta130')
    False
    >>> is_course_code('MATA37Y5')
    False
    """
    # Check that the length of the string is correct
    if len(string) != 8:
        return False
    # Check that the three-letter code is formatted correctly
    if not string[0:3].isalpha() or not string[0:3].isupper():
        return False
    # Check that the three-digit code is formatted correctly
    if not string[3:6].isnumeric() or string[3] not in {'1', '2', '3', '4'}:
        return False
    # Check that the second-last character is one of 'Y' or 'H'
    if string[6] not in {'Y', 'H'}:
        return False
    # Check that the last character is '1'
    if string[7] != '1':
        return False

    # The string passed all the required checks, so it is a valid Course Code
    return True


def is_graded_course_code(string: str) -> bool:
    """Return whether the given string is a valid Graded Course Code. A Graded Course Code is used to store a
    prerequisite Course Code along with information about grade requirements.

    A valid Graded Course Code is any string in the format XYZ###W1[%%], where all the following are satisfied:
        - XYZ###W1 is a valid Course Code, as described in the method above
        - %% is either a 2-digit number or '-1'

    >>> is_graded_course_code('CSC111H1[85]')
    True
    >>> is_graded_course_code('MAT137Y1[-1]')
    True
    >>> is_graded_course_code('STA237Y1')
    False
    """
    # Check that the length of the string is correct
    if len(string) != 12:
        return False
    # Check that the beginning of the string is a Course Code
    if not is_course_code(string[0:8]):
        return False
    # Check that the string has brackets in the right places
    if string[8] != '[' or string[11] != ']':
        return False
    # Check that the string has the grade requirement formatted correctly
    if not string[9:11].isdigit() and string[9:11] != '-1':
        return False

    # The string passed all the required checks, so it is a valid Graded Course Code
    return True


if __name__ == '__main__':
    pass
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['static_type_checker'],
    # })
