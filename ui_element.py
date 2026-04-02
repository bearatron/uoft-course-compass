"""
Pygame UI framework and interactive course visualization.

This module provides standard UI components (`Button`, `TextField`, `VisualizerInfoBox`)
to handle Pygame rendering and events. It also features `Tree` and `TreeController`
classes for dynamically visualizing and navigating hierarchical academic course networks.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from __future__ import annotations
from typing import Callable, Optional
import webbrowser
import link_of_course
from academic_calendar_reader import PrerequisiteTreeLoader, CourseNotFoundError
from course_tree import CourseTree
from operator import sub
from dataclasses import dataclass
from text_manipulation import display_multiline_text, trim_name
import json
import pygame


class UIElement:
    """
    An abstract class representing a generic UI element.

    UIElement objects define a common interface for all interactive and
    drawable UI components in the program, such as buttons, text fields,
    trees, and info boxes.
    """

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """
        Handle a pygame event related to this UI element.
        """
        raise NotImplementedError

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        Draw or update the UI element on the given screen surface.
        """
        raise NotImplementedError


@dataclass
class _BoundingBox:
    """Stores the position and rectangular area of a UI element.

    Instance Attributes:
        - top_left_cord: Top-left coordinate of the element.
        - bottom_right_cord: Bottom-right coordinate of the element.
        - rect: Rectangular pygame region representing the element.

    Representation Invariants:
        - self.top_left_cord[0] < self.bottom_right_cord[0]
        - self.top_left_cord[1] < self.bottom_right_cord[1]
        - self.rect.left == self.top_left_cord[0]
        - self.rect.top == self.top_left_cord[1]
        - self.rect.right == self.bottom_right_cord[0]
        - self.rect.bottom == self.bottom_right_cord[1]
    """
    top_left_cord: tuple[int, int]
    bottom_right_cord: tuple[int, int]
    rect: pygame.Rect


class TextField(UIElement):
    """
    Represents a text input field. This field enables users to
     type text and it visually updates based on input.

    Instance Attributes:
        - default_text: the placeholder/default text shown initially
        - font_size: font size used for rendering the text
        - bounds: stores the pygame rectangle and coordinates defining the field area through a dataclass

    Private Attributes:
        - _input_text: the current text entered by the user
        - _is_active: whether the text field is currently focused
    """
    default_text: str
    _input_text: str
    font_size: int
    _is_active: bool
    bounds: _BoundingBox

    def __init__(self, default_text: str, font_size: int, top_left_cord: tuple[int,int],
                 bottom_right_cord: tuple[int,int]) -> None:
        """
        Initializes a TextField and sets up the bounding box so that TextField is in its default state.
        """
        self.default_text = default_text
        self.font_size = font_size
        self._is_active = False
        self.clear_default_value = False
        self._input_text = default_text

        # creating parameters of pygame rect
        width = bottom_right_cord[0] - top_left_cord[0]
        height = bottom_right_cord[1] - top_left_cord[1]
        rect = pygame.Rect(top_left_cord[0], top_left_cord[1], width, height)

        # storing the relevant coordinates and rect object in respective data class
        self.bounds = _BoundingBox(top_left_cord, bottom_right_cord, rect)

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """
        Handle user interactions with the text field.
        """
        if ui_event.type == pygame.KEYDOWN and self._is_active:
            # Clear default text if it is still present
            if self.default_text in self._input_text:
                self._input_text = ""
            # Handle backspace to remove last character
            if ui_event.key == pygame.K_BACKSPACE:
                self._input_text = self._input_text[:-1]
            # Store other characters (ignoring RETURN)
            elif ui_event.key != pygame.K_RETURN:
                self._input_text += ui_event.unicode

        # Activate field if click is inside bounds, otherwise deactivate
        if ui_event.type == pygame.MOUSEBUTTONDOWN:
            if self.bounds.rect.collidepoint(ui_event.pos):
                self._is_active = True
            else:
                self._is_active = False

    def update_visually(self, ui_screen) -> None:
        """
        Draw the current text on the UI surface.
        """
        font = pygame.font.Font("FjallaOne-Regular.ttf", self.font_size)

        # change text colour depending on if field is focused
        if self._is_active:
            color = (0, 0, 200)
        else:
            color = (0, 0, 0)

        text_surface = font.render(self._input_text, True, color)
        # Center text vertically within the field rectangle
        center_of_rect = self.bounds.rect.center
        # Ensure it is in justified text format
        justified_text_format = (self.bounds.top_left_cord[0], center_of_rect[1] - self.font_size // 2)

        # display text to screen
        ui_screen.blit(text_surface, justified_text_format)

    def get_input_text(self) -> str:
        """Return the current user input."""
        return self._input_text


class Button(UIElement):
    """
    A clickable button UI element that responds to mouse interactions.

    Instance Attributes:
        - bounds: Stores the top-left, bottom-right coordinates and
          the pygame.Rect representing the button area.
        - on_click: Callback function triggered when the button is clicked.

    Private Attributes:
        - _is_pressed: Internal state indicating if the button is currently pressed.
    """
    bounds: _BoundingBox
    _is_pressed: bool
    on_click: Callable[[], None]

    def __init__(self,
                 top_left_cord: tuple[int, int],
                 bottom_right_cord: tuple[int, int],
                 on_click: Callable[[], None]) -> None:
        """Initialize the Button"""
        self._is_pressed = False
        self.on_click = on_click

        # creating parameters of pygame rect
        width = bottom_right_cord[0] - top_left_cord[0]
        height = bottom_right_cord[1] - top_left_cord[1]
        rect = pygame.Rect(top_left_cord[0], top_left_cord[1], width, height)

        # storing the relevant coordinates and rect object in respective data class
        self.bounds = _BoundingBox(top_left_cord, bottom_right_cord, rect)

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """Update button state based on user mouse interactions and call callable function when clicked"""

        if ui_event.type == pygame.MOUSEBUTTONDOWN and ui_event.button == 1:
            if self.bounds.rect.collidepoint(ui_event.pos):
                self._is_pressed = True

        # If left mouse button released, trigger on_click if previously pressed
        elif ui_event.type == pygame.MOUSEBUTTONUP and ui_event.button == 1:
            if self._is_pressed:
                self.on_click()
            self._is_pressed = False

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        This method exists because Button as a UIElement is part of a UIManager, and the manager
        iterates over all its elements and calls `update_visually` on each.
        For buttons, no visual update is needed by default, so this method is
        intentionally left empty to allow the UIManager to skip it without errors.
        """
        return


class Checkbox(Button):
    """
    A Checkbox UI element
    """
    # Static instance attributes:
    #   - CHECKBOX_FILEPATH: a str representing the filepath to the checkbox image
    #   - WIDTH_TO_HEIGHT: a float that is the ratio between checkbox image's width and height
    CHECKBOX_FILEPATH: str = "check_mark.png"
    WIDTH_TO_HEIGHT: float = 100 / 125
    # Instance Attributes:
    #   - width: an int representing the checkbox width
    #   - height: an int representing the checkbox height
    #   - checked: a bool representing whether the checkbox is checked
    width: int
    height: int
    checked: bool

    def __init__(self, top_left_coord, width) -> None:
        self.width = width
        self.height = int(self.width * Checkbox.WIDTH_TO_HEIGHT)
        self.checked = False

        x, y = top_left_coord
        bottom_right_coord = (x + self.width, y + self.height)
        super().__init__(
            top_left_coord,
            bottom_right_coord,
            lambda: self.toggle_checkbox()
        )

    def toggle_checkbox(self) -> None:
        """
        Toggle checked state
        """
        self.checked = not self.checked

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        Display checkbox if checked
        """
        if self.checked:
            img = pygame.image.load(Checkbox.CHECKBOX_FILEPATH)
            surface = pygame.transform.smoothscale(img, (self.width, self.height))
            ui_screen.blit(surface, self.bounds.top_left_cord)


@dataclass
class _PanelCourseInfo:
    """
    Stores all course-related information for the info panel.

    Instance Attributes:
        - course_code: The unique identifier for the course.
        - course_title: The full title of the course.
        - course_description: Description of the course content.
        - quality_score: Average quality rating of the course.
        - workload_score: Average workload rating of the course.
        - assessment_score: Average assessment rating of the course.
        - number_of_reviews: Number of student reviews for the course.
        - top_3_profs: list containing names of top 3 rated profs

    Representation Invariants:
        - (self.quality_score >= 0 and self.quality_score <= 5) or self.quality_score == -1
        - (self.workload_score >= 0 and self.workload_score <= 5) or self.workload_score == -1
        - (self.assessment_score >= 0 and self.assessment_score <= 5) or self.assessment_score == -1
        - self.number_of_reviews >= 0 or self.number_of_reviews == -1
        value -1 indicates data not available
    """
    course_code: str
    course_title: str
    course_description: str
    quality_score: int
    workload_score: int
    assessment_score: int
    number_of_reviews: int
    top_3_profs: list[str]


class VisualizerInfoBox(UIElement):
    """
    UI info box that displays detailed information about a selected course.

    Instance Attributes:
        - x_pos: x position of the info box
        - y_pos: y position of the info box.
        - course_info: CourseInfo dataclass storing all course-related data.
        - is_enabled: Whether the info box is enabled to display information.
        - is_open: Whether the info box is currently open (expanded) on screen.
        - images: List of pygame.Surface objects used for UI rendering.
        - buttons: List of Button objects for interacting with the info box.

    Representation Invariants:
        - len(self.images) ==  3     (background, star image, shield background)
        - len(self.buttons) == 2     (panel toggle and read more)
    """
    x_pos: int
    y_pos: int
    course_info: _PanelCourseInfo
    is_enabled: bool
    is_open: bool
    images: list[pygame.Surface]
    buttons: list[Button]

    def __init__(self, x_pos: int, y_pos: int) -> None:
        """Initialize the visualizer info box"""

        # Initialize constants
        PANEL_SIZE = (453, 750)
        STAR_SIZE = (30, 30)
        SHIELD_SIZE = (455, 778)

        OPEN_BTN_OFFSET_TOPLEFT = (45, 0)
        OPEN_BTN_OFFSET_BOTTOMRIGHT = (350, 45)

        READ_MORE_TOPLEFT = (159, 393)
        READ_MORE_BOTTOMRIGHT = (318, 414)

        self.x_pos = x_pos
        self.y_pos = y_pos
        self._initialize_course_info()

        # Defualt settings for info box state
        self.is_enabled = False
        self.is_open = False

        # loading all relevant images and storing in list
        background_image = pygame.transform.smoothscale(pygame.image.load("info_panel_cc_v3.png"), PANEL_SIZE)
        filled_star_image = pygame.transform.smoothscale(pygame.image.load(
            "ui_star_course_compass.png"), STAR_SIZE)
        background_shield = pygame.transform.smoothscale(pygame.image.load("info_box_shield.png"), SHIELD_SIZE)
        self.images = [background_image, filled_star_image, background_shield]

        # creating both buttons and storing the in list
        panel_open_button = Button(
            (x_pos + OPEN_BTN_OFFSET_TOPLEFT[0],
             y_pos + OPEN_BTN_OFFSET_TOPLEFT[1]),
            (x_pos + OPEN_BTN_OFFSET_BOTTOMRIGHT[0],
             y_pos + OPEN_BTN_OFFSET_BOTTOMRIGHT[1]),
            self.change_state
        )

        read_more_button = Button(
            READ_MORE_TOPLEFT,
            READ_MORE_BOTTOMRIGHT,
            self.read_more
        )

        self.buttons = [panel_open_button, read_more_button]


    def _initialize_course_info(self) -> None:
        """
        Private helper for setting up the default value for self.course_info
        """
        course_title = ""
        course_description = ""
        selected_course_code = ""
        quality_score = -1
        workload_score = -1
        assessment_score = -1
        number_of_reviews = -1
        top_3_profs = []
        # Storing data in dataclass
        self.course_info = _PanelCourseInfo(selected_course_code,
                                            course_title, course_description, quality_score,
                                            workload_score, assessment_score, number_of_reviews, top_3_profs)

    def update_information(self, selected_course_code: str, course_title: str, course_description: str) -> None:
        """
        Update the information stored in the info box for the selected course.

        This includes basic course details (code, title, description) and,
        if the info box is enabled, additional computed stats loaded from
        a local JSON file (e.g., ratings, review count, top professors).

         Preconditions:
            - selected_course_code is a course code present in course_data_computed.json
            - "course_data_computed.json" exists and follows the expected structure
        """
        # Update info with all passed values
        self.course_info.course_code = selected_course_code
        self.course_info.course_title = course_title
        self.course_info.course_description = course_description

        if self.is_enabled:
            with open("course_data_computed.json", "r") as file:
                data = json.load(file)
            # grab all relevant stats from the JSON file
            course_quality = data[selected_course_code]["grouped_metrics"]["course_quality"]
            workload = data[selected_course_code]["grouped_metrics"]["workload"]
            assessment_quality = data[selected_course_code]["grouped_metrics"]["assessment_quality"]
            num_reviews = data[selected_course_code]["num_responses"]
            top_3_profs = data[selected_course_code]["profs_by_rating"][:3]
            # update course_info data class
            self.course_info.quality_score = course_quality
            self.course_info.workload_score = workload
            self.course_info.assessment_score = assessment_quality
            self.course_info.number_of_reviews = num_reviews
            self.course_info.top_3_profs = top_3_profs

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """
        Delegate interaction handling to all buttons in the info box.
        """
        for button in self.buttons:
            button.handle_interaction(ui_event)

    def change_state(self) -> None:
        """
       Toggle the open/closed state of the info box.
       """
        if self.is_enabled:
            if self.is_open:
                self.is_open = False
            else:
                self.is_open = True

    def read_more(self) -> None:
        """
        Open the course webpage in a browser if the info box is active and open.

        Preconditions:
        - self.course_info.course_code is a valid course code
        - link_of_course.course_link_generate returns a valid URL
        """
        if self.is_enabled and self.is_open:
            webbrowser.open(link_of_course.course_link_generate(self.course_info.course_code))

    def update_visually(self, ui_screen) -> None:
        """
        Display the info box UI onto the given screen.
        Displays either the open or collapsed state.
        """
        # image index
        PANEL_IMG = 0
        SHIELD_IMG = 2
        # button index
        OPEN_BUTTON_INDEX = 0
        # layout offsets
        OPEN_SHIELD_Y_OFFSET = -20
        OPEN_BUTTON_OFFSET = (45, 0)
        CLOSED_SHIELD_Y_OFFSET = 800
        CLOSED_PANEL_Y_OFFSET = 700
        CLOSED_BUTTON_OFFSET = (45, 700)

        if self.is_enabled and self.is_open:
            # Open state, fully visible info panel

            # Draw background and panel
            # Draw shield (slightly above panel) NOTE: shield is what blurs the background
            ui_screen.blit(self.images[SHIELD_IMG], (self.x_pos, self.y_pos + OPEN_SHIELD_Y_OFFSET))
            ui_screen.blit(self.images[PANEL_IMG], (self.x_pos, self.y_pos))
            # Update toggle button position relative to panel
            self.buttons[OPEN_BUTTON_INDEX].bounds.rect.topleft = (self.x_pos + OPEN_BUTTON_OFFSET[0], self.y_pos + OPEN_BUTTON_OFFSET[1])

            # Draw all UI sections
            self._display_course_title_description(ui_screen)
            self._display_stars(ui_screen)
            self._display_prof_ranking(ui_screen)
            self._display_review_number(ui_screen)

        elif self.is_enabled and not self.is_open:
            # Closed state, collapsed panel
            # Draw background and panel but further down since its collapsed
            ui_screen.blit(self.images[SHIELD_IMG], (self.x_pos, self.y_pos + CLOSED_SHIELD_Y_OFFSET))
            ui_screen.blit(self.images[PANEL_IMG], (self.x_pos, self.y_pos + CLOSED_PANEL_Y_OFFSET ))
            # Reposition button for collapsed view
            self.buttons[0].bounds.rect.topleft = (self.x_pos + CLOSED_BUTTON_OFFSET[0], self.y_pos + CLOSED_BUTTON_OFFSET[1])

    def _display_course_title_description(self, ui_screen: pygame.Surface) -> None:
        """
        Private helper to display the course title and description text.
        """
        BODY_FONT_SIZE = 12
        HEADING_FONT_SIZE = 25
        # text layout offsets
        HEADING_OFFSET = (40, 60)
        DESCRIPTION_OFFSET = (40, 140)
        font_text = pygame.font.Font("RobotoMono-VariableFont_wght.ttf", BODY_FONT_SIZE)
        font_heading = pygame.font.Font("FjallaOne-Regular.ttf", HEADING_FONT_SIZE)

        # Draw course title (heading)
        heading_x = self.x_pos + HEADING_OFFSET[0]
        heading_y = self.y_pos + HEADING_OFFSET[1]
        display_multiline_text("Heading", self.course_info.course_title, (heading_x, heading_y), font_heading,
                               ui_screen, None)

        # Draw course description (body text)
        text_x = self.x_pos + DESCRIPTION_OFFSET[0]
        text_y = self.y_pos + DESCRIPTION_OFFSET[1]
        display_multiline_text("Body", self.course_info.course_description, (text_x, text_y), font_text, ui_screen,
                               None)

    def _display_stars(self, ui_screen: pygame.Surface):
        """
        Private helper to display rating stars for course quality, workload, and assessment
        """
        # Image indices
        STAR_IMG = 1

        # Star layout (y positions - based on screen)
        QUALITY_STAR_Y = 449
        WORKLOAD_STAR_Y = 513
        ASSESSMENT_STAR_Y = 588

        _score_visualizer(round(self.course_info.quality_score), QUALITY_STAR_Y, self.images[STAR_IMG], ui_screen)
        _score_visualizer(round(self.course_info.workload_score), WORKLOAD_STAR_Y, self.images[STAR_IMG], ui_screen)
        _score_visualizer(round(self.course_info.assessment_score), ASSESSMENT_STAR_Y, self.images[STAR_IMG], ui_screen)

    def _display_prof_ranking(self, ui_screen: pygame.Surface) -> None:
        """
        Private helper to display the top 3 professors for the course
        """
        PROF_X_POS = 275
        PROF_Y_START = 652
        PROF_Y_SPACING = 18
        PROF_NAME_MAX_LENGTH = 30
        PROF_NAME_COLOR = (35, 68, 119)
        PROF_FONT_SIZE = 12

        font_text_styled = pygame.font.Font("FjallaOne-Regular.ttf", PROF_FONT_SIZE)
        # Render each professor name with formatting
        for i in range(len(self.course_info.top_3_profs)):
            name = trim_name(self.course_info.top_3_profs[i], PROF_NAME_MAX_LENGTH)
            text_surface = font_text_styled.render(name, True, PROF_NAME_COLOR)
            ui_screen.blit(text_surface, (PROF_X_POS, PROF_Y_START + i * PROF_Y_SPACING))

    def _display_review_number(self, ui_screen: pygame.Surface):
        """
        Display the number of course reviews
        """
        REVIEWS_FONT_SIZE = 12
        REVIEWS_BORDER_X1 = 171
        REVIEWS_BORDER_Y1 = 726
        REVIEWS_BORDER_X2 = 307
        REVIEWS_BORDER_Y2 = 733
        REVIEWS_COLOR = (0, 0, 0)

        font_text = pygame.font.Font("RobotoMono-VariableFont_wght.ttf", REVIEWS_FONT_SIZE)
        # Define bounding box for centering text
        reviews_border_rect = pygame.Rect(REVIEWS_BORDER_X1, REVIEWS_BORDER_Y1,
                                          REVIEWS_BORDER_X2 - REVIEWS_BORDER_X1, REVIEWS_BORDER_Y2 - REVIEWS_BORDER_Y1)
        # Display review count text
        text_surface = font_text.render(str(self.course_info.number_of_reviews) + " reviews", True, REVIEWS_COLOR)
        text_rect = text_surface.get_rect(center=reviews_border_rect.center)
        ui_screen.blit(text_surface, text_rect)

    def get_course_title(self) -> str:
        """
        Return the currently selected course title.
        """
        return self.course_info.course_title


class TextDisplayer(UIElement):
    """
    A UI element that displays multiline text at a fixed position on the screen.

    Instance Attributes:
    - display_text: The text to display on the screen.
    - x_pos: The x-coordinate of the top left corner of the text.
    - y_pos: The y-coordinate of the top left corner of the text.
    - color: The RGB color of the text. Defaults to black (0, 0, 0).

    Representation Invariants:
    - self.x_pos and self.y_pos are non-negative integers representing pixel positions
    """

    display_text: str
    x_pos: int
    y_pos: int
    color: Optional[tuple[int, int, int]]

    def __init__(self, display_text: str, x_pos: int, y_pos: int, color: Optional[tuple[int, int, int]] = None) -> None:
        """
        Initialize a TextDisplayer.
        """
        self.display_text = display_text
        self.x_pos = x_pos
        self.y_pos = y_pos

        if color is None:
            # set color to black as default if no colour is specified
            self.color = (0, 0, 0)
        else:
            self.color = color

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        Display the text onto the screen
        """
        FONT_SIZE = 25
        font = pygame.font.Font("FjallaOne-Regular.ttf", FONT_SIZE)
        display_multiline_text(
            "Body",
            self.display_text,
            (self.x_pos, self.y_pos),
            font,
            ui_screen,
            self.color
        )

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """
        This method exists because TextDisplayer as a UIElement is part of a UIManager, and the manager
        iterates over all its elements and calls `handle_interaction` on each.
        For TextDisplayer, no interaction handling is needed by default, so this method is
        intentionally left empty to allow the UIManager to skip it without errors.
        """
        return


def _score_visualizer(score: int, y_pos: int, star_image, ui_screen) -> None:
    """
    Display a horizontal row of star images representing score.

    Preconditions:
     - self.score <= 5 and self.score >= 0
    """
    STAR_START_X = 261
    STAR_SPACING = 36
    for i in range(score):
        ui_screen.blit(star_image, (STAR_START_X + STAR_SPACING * i, y_pos))


class TreeController(UIElement):
    """
    A class responsible for controlling the viewing position and interaction
    of the course tree visualization.

    The TreeController handles:
        - dragging the tree around the screen
        - zooming in and out
        - detecting node clicks
        - updating the course info box when a node is clicked

    Instance Attributes:
        - x_pos_tree: the x-coordinate offset of the tree on the screen
        - y_pos_tree: the y-coordinate offset of the tree on the screen
        - dragging: whether the user is currently dragging the tree
        - zoom_factor: the current zoom multiplier applied to the tree
        - previous_mouse_pos: the previous mouse position during dragging
        - node_course_code_map: a list mapping pygame.Rect nodes to course codes
        - code_clicked: the course code of the node currently being clicked
        - initial_mouse_down_pos: the mouse position when the click began
        - course_info_box: the info box UI element associated with the tree
        - rect: the bounding box where zooming and dragging works


    Representation Invariants:
        - self.zoom_factor > 0
        - self.x_pos_tree >= 0
        - self.y_pos_tree >= 0
     """
    top_left_coord: tuple[int, int]
    bottom_right_coord: tuple[int, int]
    x_pos_tree: int
    y_pos_tree: int
    dragging: bool
    zoom_factor: int
    previous_mouse_pos: tuple[int,int] | None
    node_course_code_map: list[tuple[pygame.Rect, str]]
    code_clicked: str | None
    initial_mouse_down_pos: tuple[int, int] | None
    course_info_box: VisualizerInfoBox
    loader: PrerequisiteTreeLoader
    rect: pygame.Rect

    def __init__(self,
                 course_info_box: VisualizerInfoBox,
                 loader: PrerequisiteTreeLoader,
                 top_left_coord: tuple[int, int],
                 bottom_right_coord: tuple[int, int]) -> None:
        """
        Initializes an instance of TreeCamera

        Preconditions
            - top_left_coord is None == bottom_right_coord is None
        """
        width, height = tuple(map(sub, bottom_right_coord, top_left_coord))
        self.rect = pygame.Rect(top_left_coord[0], top_left_coord[1], width, height)

        self.x_pos_tree = top_left_coord[0] + (width // 2) - (Tree.NODE_WIDTH // 2)
        self.y_pos_tree = top_left_coord[1] + 70

        self.dragging = False
        self.zoom_factor = 1
        self.previous_mouse_pos = None
        self.initial_mouse_down_pos = None
        self.node_course_code_map = []
        self.code_clicked = None
        self.course_info_box = course_info_box
        self.loader = loader

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        Empty because TreeController does not need to display anything
        This method is required to be implemented as per UIElement abstract class
        """
        return

    def handle_interaction(self, mouse_event: pygame.event.Event) -> None:
        """
        Handle zooming and dragging of the tree in its bounding rectangle
        """
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if mouse_event.type == pygame.MOUSEWHEEL:
                if mouse_event.y > 0:
                    self.zoom_factor *= 1.1
                elif mouse_event.y < 0:
                    self.zoom_factor *= 0.9
            if mouse_event.type == pygame.MOUSEBUTTONDOWN and mouse_event.button == 1:
                self.dragging = True
                mouse_position = pygame.mouse.get_pos()
                self.previous_mouse_pos = mouse_position
                self.initial_mouse_down_pos = mouse_position

                # check if a node is being clicked on:
                for item in self.node_course_code_map:
                    node = item[0]
                    node_course_code = item[1]
                    if node.collidepoint(mouse_event.pos):
                        self.code_clicked = node_course_code
            # the actual mouse dragging movement
            if mouse_event.type == pygame.MOUSEMOTION and self.dragging:
                current_mouse_pos = pygame.mouse.get_pos()
                displacement_x = current_mouse_pos[0] - self.previous_mouse_pos[0]
                displacement_y = current_mouse_pos[1] - self.previous_mouse_pos[1]

                # zoom-aware movement
                self.x_pos_tree += displacement_x
                self.y_pos_tree += displacement_y

                self.previous_mouse_pos = current_mouse_pos
            # the end of mouse drag based tree movement
            if mouse_event.type == pygame.MOUSEBUTTONUP:
                if mouse_event.button == 1:
                    self.dragging = False
                    current_mouse_pos = pygame.mouse.get_pos()
                    if self.code_clicked is not None:
                        displacement_x = current_mouse_pos[0] - self.initial_mouse_down_pos[0]
                        displacement_y = current_mouse_pos[1] - self.initial_mouse_down_pos[1]

                        if displacement_x < 2 and displacement_y < 2:
                            self.course_info_box.is_enabled = True
                            self.update_info_box()
                        self.code_clicked = None
                    # if x_pos is on the white space, and its clicking outside a course, info pannel closes
                    elif current_mouse_pos[0] >= 475:
                        self.course_info_box.is_enabled = False

    def reset_camera(self) -> None:
        """
        Reset the camera to the original position
        """
        self.__init__(self.course_info_box, self.loader, self.rect.topleft, self.rect.bottomright)

    def update_info_box(self) -> None:
        """
        Update info box with the course title and description
        """
        selected_course_code = self.code_clicked
        try:
            course_title, description = self.loader.get_name_and_description(self.code_clicked)
        except CourseNotFoundError:
            # Check if the info box is currently not displaying anything
            if self.course_info_box.get_course_title() == "":
                # The info box is not displaying anything, so it shouldn't pop up
                self.course_info_box.is_enabled = False
            return
        self.course_info_box.update_information(selected_course_code, course_title, description)


class CourseDifference(TreeController):
    """
    A class for displaying the Course Difference tree

    It will be displayed as three columns. From left to right, the columns contain:
        1. The postreq courses exclusive to course1_to_compare
        2. The postreq courses shared by course1_to_compare and course2_to_compare
        3. The postreq courses exclusive to course2_to_compare
    """
    course1_to_compare: str
    course2_to_compare: str
    course1_exclusive: set[str]
    course2_exclusive: set[str]
    same_to_both: set[str]
    info_box: VisualizerInfoBox

    def __init__(self, course_info_box: VisualizerInfoBox, loader: PrerequisiteTreeLoader) -> None:
        """
        Initialize an instance of CourseDifference tree
        """
        super().__init__(course_info_box, loader, (480, 30), (1400, 750))
        # initially, set the following attributes to default values
        # to display a course difference tree, access the below attributes and set them to their corresponding values
        self.course1_to_compare = ""
        self.course2_to_compare = ""
        self.course1_exclusive = set()
        self.course2_exclusive = set()
        self.same_to_both = set()
        self.info_box = course_info_box

    def reset_camera(self) -> None:
        """
        Reset the positioning of the tree
        """
        self.top_left_coord = (480, 30)
        self.bottom_right_coord = (1400, 750)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        Draw the course differences to the screen
        """
        # clear previous nodes that have been drawn
        self.node_course_code_map.clear()

        # spacing constants that scale as the user zooms
        HORIZONTAL_SPACING = int(400 * self.zoom_factor)
        VERTICAL_SPACING = int(150 * self.zoom_factor)

        # title is displayed slightly closer to the course nodes
        TITLE_OFFSET_FACTOR = 50

        # ############## Display the three columns ################### #
        # display the first column showing postreq courses exclusive to course 1

        # column heading text
        font_size = max(12, int(24 * self.zoom_factor))
        font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
        text = font.render(f"Courses Exclusive To {self.course1_to_compare}:", True, (35, 68, 119))
        ui_screen.blit(text, (self.x_pos_tree - HORIZONTAL_SPACING,  self.y_pos_tree))

        for idx, course_code in enumerate(self.course1_exclusive):
            self.draw_node(
                (course_code, ""),
                (self.x_pos_tree - HORIZONTAL_SPACING,
                 self.y_pos_tree + (idx+1) * VERTICAL_SPACING - TITLE_OFFSET_FACTOR),
                self.zoom_factor,
                [],
                ui_screen
            )

        # display the second column showing postreq courses shared by both course 1 and course 2
        text = font.render("Courses Mutual to Both:", True, (35, 68, 119))
        ui_screen.blit(text, (self.x_pos_tree, self.y_pos_tree))
        for idx, course_code in enumerate(self.same_to_both):
            self.draw_node(
                (course_code, ""),
                (self.x_pos_tree,
                 self.y_pos_tree + (idx+1) * VERTICAL_SPACING - TITLE_OFFSET_FACTOR),
                self.zoom_factor,
                [],
                ui_screen
            )

        # display the third column showing postreq courses exclusive to course 2
        text = font.render(f"Courses Exclusive To {self.course2_to_compare}:", True, (35, 68, 119))
        ui_screen.blit(text, (self.x_pos_tree + HORIZONTAL_SPACING, self.y_pos_tree))
        for idx, course_code in enumerate(self.course2_exclusive):
            self.draw_node(
                (course_code, ""),
                (self.x_pos_tree + HORIZONTAL_SPACING,
                 self.y_pos_tree + (idx+1) * VERTICAL_SPACING - TITLE_OFFSET_FACTOR),
                self.zoom_factor,
                [],
                ui_screen
            )

    def handle_interaction(self, mouse_event: pygame.event.Event) -> None:
        """Handle dragging and zooming; this is the same behavior as the default implementation in TreeController"""
        super().handle_interaction(mouse_event)

    def draw_node(self, display_vals: tuple[str, str], position: tuple[int, int], screen_zoom_factor: int,
                  node_course_code_map: list[tuple[pygame.Rect, str]], target_screen: pygame.Surface) -> None:
        """
        Draw a node on point (x_pos, y_pos) with text, display_val

        Preconditions:
        - screen_zoom_factor > 0
        """
        # Define rectangle size with respect to the screen_zoom_factor which scales the
        # Rectangle based on how zoomed in or out the user is
        rect_width = int(200 * screen_zoom_factor)
        rect_height = int(50 * screen_zoom_factor)

        x_pos = position[0]
        y_pos = position[1]

        COURSE_CODE_INDEX = 0
        COURSE_MARK_INDEX = 1

        # Node is a pygame rect so that it can be drawn and interacted with later on
        node = pygame.Rect(x_pos,
                           y_pos,
                           rect_width,
                           rect_height)

        # Adding node to a tuple list that maps node object with course code (display_val)
        node_course_code_map.append((node, display_vals[COURSE_CODE_INDEX]))

        # Drawing rect to screen
        pygame.draw.rect(target_screen,
                         (161, 202, 246),
                         node,
                         border_radius=int(15 * screen_zoom_factor))

        # Creating the node text font
        font_size = max(12, int(24 * screen_zoom_factor))
        node_font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
        # Creating node text
        text_to_display = display_vals[COURSE_CODE_INDEX] + " " + display_vals[COURSE_MARK_INDEX]
        text_img = node_font.render(text_to_display, True, [0, 0, 0])
        # Get text rect so that text can be centered in the rect
        text_rect = text_img.get_rect()
        # Setting the text to the center of the node
        text_rect.center = (x_pos + rect_width // 2, y_pos + rect_height // 2)

        # Displaying the node text
        target_screen.blit(text_img, text_rect)


class Tree(UIElement):
    """
    The UI element for Course Difference tree
    """
    # Static Variables (constants for tree layout):
    #   - NODE_WIDTH: node's width
    #   - NODE_HEIGHT: node's height
    #   - VERTICAL_SPACING: vertical space between each node
    #   - LINE_THICKNESS: thickness of the line connecting two nodes
    #   - LINE_COLOR: color of the lines connecting two nodes
    NODE_WIDTH = 200
    NODE_HEIGHT = 50
    VERTICAL_SPACING = 150
    LINE_THICKNESS = 4
    LINE_COLOR = (0, 0, 0)

    # Instance attributes:
    #   - tree_camera: a TreeController to be used to control user interactions with the tree
    #   - course_tree: a CourseTree to be displayed
    tree_camera: TreeController
    course_tree: CourseTree

    def __init__(self, tree_camera: TreeController, course_tree: CourseTree) -> None:
        """Initialize tree element"""
        super().__init__()
        self.tree_camera = tree_camera
        self.course_tree = course_tree

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """Handle drag, move element"""
        self.tree_camera.handle_interaction(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """Draw the tree to the screen"""
        self.tree_camera.node_course_code_map.clear()

        self.draw_tree_visualization(self.course_tree, (self.tree_camera.x_pos_tree,
                                                        self.tree_camera.y_pos_tree), 300,
                                     self.tree_camera.zoom_factor,
                                     self.tree_camera.node_course_code_map, ui_screen)

    def draw_tree_visualization(self, tree: CourseTree, positions: tuple[int, int], spacing_factor: int,
                                tree_zoom_factor: int,
                                node_course_code_map: list[tuple[pygame.Rect, str]],
                                target_screen: pygame.Surface) -> None:
        """
            Draw a CourseTree onto the screen as a hierarchical tree diagram. The function traverses the provided tree
            recursively, drawing the current node and then its subtrees below it.

            Preconditions:
            - spacing_factor > 0
            - tree_zoom_factor > 0
            """
        if tree.is_empty():
            return
        else:
            # Extract x,y positions from tuple
            x_pos = positions[0]
            y_pos = positions[1]
            # Draw the node using the root value of the tree
            self.draw_node((tree.get_root(), tree.get_grade_requirement()), positions, tree_zoom_factor,
                           node_course_code_map, target_screen)
            # Determine total horizontal space needed for all children
            total_spacing = self.tree_width(tree) * spacing_factor * tree_zoom_factor
            # Start by placing children from the leftmost position so they are centered under the parent node
            start_x_pos = x_pos - total_spacing // 2

            for subtree in tree.get_subtrees():
                # Each subtree is given horizontal space based on its width
                subtree_width = self.tree_width(subtree) * spacing_factor * tree_zoom_factor
                # Place child node in center of its allocated space
                child_x = start_x_pos + subtree_width // 2

                # Draw line from parent to child
                pygame.draw.line(
                    target_screen, Tree.LINE_COLOR,
                    (x_pos + int(Tree.NODE_WIDTH / 2 * tree_zoom_factor),
                     y_pos + int(Tree.NODE_HEIGHT * tree_zoom_factor)),
                    (child_x + int(Tree.NODE_WIDTH / 2 * tree_zoom_factor),
                     y_pos + int(Tree.VERTICAL_SPACING * tree_zoom_factor)),
                    max(1, int(Tree.LINE_THICKNESS * tree_zoom_factor))
                )

                self.draw_tree_visualization(subtree, (child_x, y_pos + int(Tree.VERTICAL_SPACING * tree_zoom_factor)),
                                             spacing_factor, tree_zoom_factor,
                                             node_course_code_map, target_screen)

                # Move to the next horizontal space for the next subtree
                start_x_pos += subtree_width

    def draw_node(self, display_vals: tuple[str, str], position: tuple[int, int], screen_zoom_factor: int,
                  node_course_code_map: list[tuple[pygame.Rect, str]], target_screen: pygame.Surface) -> None:
        """
        Draw a node on point (x_pos, y_pos) with text, display_val

        Preconditions:
        - screen_zoom_factor > 0
        """
        # Define rectangle size with respect to the screen_zoom_factor which scales the
        # Rectangle based on how zoomed in or out the user is
        rect_width = int(200 * screen_zoom_factor)
        rect_height = int(50 * screen_zoom_factor)

        x_pos = position[0]
        y_pos = position[1]

        COURSE_CODE_INDEX = 0
        COURSE_MARK_INDEX = 1

        # Node is a pygame rect so that it can be drawn and interacted with later on
        node = pygame.Rect(x_pos, y_pos, rect_width, rect_height)

        # Adding node to a tuple list that maps node object with course code (display_val)
        node_course_code_map.append((node, display_vals[COURSE_CODE_INDEX]))

        # Drawing rect to screen
        pygame.draw.rect(target_screen,
                         (161, 202, 246),
                         node,
                         border_radius=int(15 * screen_zoom_factor))

        # Creating the node text font
        font_size = max(12, int(24 * screen_zoom_factor))
        node_font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
        # Creating node text
        text_to_display = display_vals[COURSE_CODE_INDEX] + " " + display_vals[COURSE_MARK_INDEX]
        text_img = node_font.render(text_to_display, True, [0, 0, 0])
        # Get text rect so that text can be centered in the rect
        text_rect = text_img.get_rect()
        # Setting the text to the center of the node
        text_rect.center = (x_pos + rect_width // 2, y_pos + rect_height // 2)

        # Displaying the node text
        target_screen.blit(text_img, text_rect)

    def tree_width(self, tree: CourseTree) -> int:
        """
        Recursively return width of tree (width of the lowest layer of all subtrees)
        """
        if tree.is_empty():
            return 0
        elif not tree.get_subtrees():
            return 1
        else:
            width_so_far = 0
            for subtree in tree.get_subtrees():
                width_so_far += self.tree_width(subtree)
            return width_so_far


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
