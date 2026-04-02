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
    #TODO: make considtion s.t. text type can only be body or heading
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
    text_x = position[0]
    text_y = position[1]
    # setting
    line_spacing = 0.5
    # text wrap
    wrapped_lines = textwrap.wrap(text, width=max_chars_per_line)
    num_lines = len(wrapped_lines)
    # text drawed
    if num_lines == 1 and text_type == "Heading":
        text_y += 15
    if num_lines > max_lines:
        wrapped_lines = textwrap.wrap(str(text), width=max_chars_per_line)
        wrapped_lines = wrapped_lines[:max_lines]

        last_line_words = wrapped_lines[-1].split()
        if len(last_line_words) > 1:
            last_line_words.pop()
            wrapped_lines[-1] = " ".join(last_line_words) + "..."
        else:
            wrapped_lines[-1] = wrapped_lines[-1][:max_chars_per_line - 3] + "..."

    num_lines_to_display = min(max_lines, num_lines)
    for i in range(num_lines_to_display):  # max of 13 lines
        line = wrapped_lines[i]
        text_surface = font.render(line, True, color)
        ui_screen.blit(text_surface, (text_x, text_y))
        text_y += text_surface.get_height() + line_spacing


def trim_name(name: str, max_length: int) -> str:
    name = name.split(",")[0]  #takes last name only
    if len(name) > max_length:
        return name[:max_length - 3] + "..."
    return name
