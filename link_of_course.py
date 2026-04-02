"""
Academic Calendar URL Generation Utilities.

This module provides helper functions to programmatically construct URLs
for the University of Toronto Arts & Science academic calendar. It includes
utilities to format course codes and parse program names into valid web links
for direct access to official course and program descriptions.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""


def course_link_generate(course_name: str) -> str:
    """
    This function takes in the name of the given course and returns a string that is a link to the website
    """
    return f"https://artsci.calendar.utoronto.ca/course/{course_name.lower()}"


def program_link_generate(program_name: str) -> str:
    """
    This function takes in the name of the given program name and returns a string that is a link to the website
    """

    char_index = 0
    edited_program_name = program_name
    while char_index in range(len(program_name)):
        if program_name[char_index] == "(":
            edited_program_name = program_name[char_index+1:len(program_name)-1]
            break
        char_index += 1
    edited_program_name = edited_program_name.replace(" ", "-")

    return f"https://artsci.calendar.utoronto.ca/section/{edited_program_name.lower()}"
