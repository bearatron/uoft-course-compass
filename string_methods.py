"""Various string methods useful for parsing course codes"""


def has_unnested(string: str, char: str) -> bool:
    """Return whether the given string has an instance of char that is not nested within parentheses

    >>> has_unnested("Hello, World!", ",")
    True
    >>> has_unnested("(,)", ",")
    False
    """
    bracket_depth = 0
    for character in string:
        if character == "(":
            bracket_depth += 1
        elif character == ")":
            bracket_depth -= 1
        elif character == char and bracket_depth == 0:
            return True
    return False


def unnested_split(string: str, split_char: str) -> list[str]:
    """Split the given string at all unnested instances of the provided char
    split_char must be of length 1 and must not be "(" or ")"

    >>> unnested_split("csc111,csc112,(mat136,mat137)", ",")
    ['csc111', 'csc112', '(mat136,mat137)']
    """
    bracket_depth = 0
    current_item = ""
    all_items = []
    for char in string:
        if char == "(":
            bracket_depth += 1
        elif char == ")":
            bracket_depth -= 1
        if char == split_char and bracket_depth == 0:
            all_items.append(current_item)
            current_item = ""
        else:
            current_item += char
    all_items.append(current_item)  # add on the last item, because it wasn't followed by a comma
    return all_items


def is_course_code(string: str) -> bool:
    """Return whether a given string is a valid course code
    should probably explain what that is...

    >>> is_course_code("MAT137Y1")
    True
    >>> is_course_code("STA130")
    False
    >>> is_course_code("MAT137Z4")
    False
    """
    if len(string) != 8:
        return False
    if not string[0:3].isalpha():
        return False
    if string[-1] != "1":
        return False
    if string[3] not in {"1", "2", "3", "4"}:
        return False
    if string[6] not in {"Y", "H"}:
        return False
    return True


def is_graded_course_code(string: str) -> bool:
    """Return whether a given string is a valid graded course code
        should probably explain what that is...
    """
    if len(string) != 12:
        return False
    if not string[0:3].isalpha():
        return False
    if string[7] != "1":
        return False
    if string[3] not in {"1", "2", "3", "4"}:
        return False
    if string[6] not in {"Y", "H"}:
        return False
    if string[8] != "[" or string[11] != "]":
        return False
    return True
