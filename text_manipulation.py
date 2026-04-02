"""
Text manipulation and rendering utilities.

This module provides helper functions to format, wrap, and display text
within the Pygame UI. It abstracts complex layout tasks such as multiline
text wrapping with automatic truncation for headings and body paragraphs,
as well as string trimming to ensure names and long strings fit cleanly
inside predefined visual boundaries.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""
import pygame
from typing import Optional
import textwrap


def display_multiline_text(
        text_type: str,
        text: str,
        position: tuple[int, int],
        font: pygame.font.Font,
        ui_screen,
        color: Optional[tuple[int, int, int]]) -> None:
    """
    Display wrapped multiline text on the screen.

    Preconditions:
        - text_type in {"Heading", "Body"}
        - position[0] >= 0
        - position[1] >= 0
        - if color is not None, each value in color is between 0 and 255 inclusive
    """

    VERTICAL_OFFSET_FOR_HEADER = 15

    #Text Settings
    line_spacing = 0.5
    if text_type == "Heading":
        max_lines = 2
        max_chars_per_line = 38
        if color is None:
            color = (35, 68, 119)
    else:
        max_lines = 13
        max_chars_per_line = 55
        if color is None:
            color = (0, 0, 0)

    #location to place multiline text
    text_x = position[0]
    text_y = position[1]

    # wrap text using library
    wrapped_lines = textwrap.wrap(text, width=max_chars_per_line)
    num_lines = len(wrapped_lines)

    #if there are more lines of text than ui can handle, cut it off
    if num_lines > max_lines:
        wrapped_lines = _truncate_wrapped_lines(wrapped_lines, max_lines, max_chars_per_line)

    #Push headers down more vertically
    if num_lines == 1 and text_type == "Heading":
        text_y += VERTICAL_OFFSET_FOR_HEADER

    #Display each line of the multiline text
    for line in wrapped_lines:
        text_surface = font.render(line, True, color)
        ui_screen.blit(text_surface, (text_x, text_y))
        text_y += text_surface.get_height() + line_spacing

def _truncate_wrapped_lines(wrapped_lines: list[str], max_lines: int, max_chars_per_line: int) -> list[str]:
    """
    Return wrapped lines truncated with an ellipsis if it is too long.

    Preconditions:
        - wrapped_lines != []
        - max_lines > 0
        - max_chars_per_line >= 3
    """
    #only keep text up to the max number of lines
    wrapped_lines = wrapped_lines[:max_lines]
    #split the last line
    last_line_words = wrapped_lines[-1].split()

    # Remove the final word so there is room for "..."
    if len(last_line_words) > 1:
        last_line_words.pop()
        wrapped_lines[-1] = " ".join(last_line_words) + "..."
    else:
        # If the last line is only one long word, cut characters directly
        wrapped_lines[-1] = wrapped_lines[-1][:max_chars_per_line - 3] + "..."

    return wrapped_lines


def trim_name(name: str, max_length: int) -> str:
    """
    Return a shortened version of a name.

    Only the text before the first comma is kept (last name). If the last name
    exceeds the maximum length, it is shortened and ends with "...".

    Preconditions:
        - max_length >= 3
        - name != ""
        -  name is formatted as "last_name, first_name"
    """
    # Keep only the portion of the name before the first comma
    name = name.split(",")[0]
    # Shorten the name if it exceeds the maximum allowed length
    if len(name) > max_length:
        return name[:max_length - 3] + "..."
    return name
