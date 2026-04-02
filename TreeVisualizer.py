"""Main Application Window and Event Loop.

This module provides the `TreeVisualizer` class, which serves as the core
window manager and event loop runner for the Pygame application. It handles
display initialization, asset loading (via `_TreeVisualizerImages`), and
state management to navigate between the start screen, course selection
menu, and the main visualizer interface.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

import pygame

from dataclasses import dataclass

from ui_manager import UIManager, CourseManager, MainScreenUI
from ui_element import TextField, Button


@dataclass
class _TreeVisualizerImages:
    """
    A data class that stores all image assets used by the application.

    Instance Attributes:
        - start_page: Background image for the startup screen.
        - course_selection_page: Background image for the course selection screen.
        - course_spec_slider1: First course factor slider image.
        - course_spec_slider2: Second course factor slider image.
        - course_spec_slider3: Third course factor slider image.
        - course_tree_type_slider_image: list of images used to toggle between prerequisite
          and postrequisite tree modes.
        - selection_check_mark: Check mark image used for selections.

    Representation Invariants:
        - len(self.course_tree_type_slider_image) == 2
          The list contains exactly two images, one for each slider button state.
    """
    start_page: pygame.Surface
    course_selection_page: pygame.Surface
    course_spec_slider1: pygame.Surface
    course_spec_slider2: pygame.Surface
    course_spec_slider3: pygame.Surface
    course_tree_type_slider_image: list[pygame.Surface]
    selection_check_mark: pygame.Surface


@dataclass
class _UIManagers:
    """
    Data class stores all UI managers used across screens.

    Instance Attributes:
        - start_screen_ui: UI manager for the startup screen.
        - course_selection_ui: UI manager for the course selection screen.
        - main_screen_ui: UI manager for the main visualization screen.
    """
    start_screen_ui: UIManager
    course_selection_ui: UIManager
    main_screen_ui: MainScreenUI


@dataclass
class _UIElements:
    """
    Data class that stores ui elements used on screens before the main screen

    Instance Attributes:
        - taken_course_field: Text field used to enter a course code.
        - grade_mark_field: Text field used to enter a course grade.
        - add_course_button: Button used to add a course to the course list.
    """
    taken_course_field: TextField
    grade_mark_field: TextField
    add_course_button: Button


class TreeVisualizer:
    """
    A class that manages the application and its app events.

    Instance Attributes:
        - screen: Main pygame display surface.
        - font: Font used for rendering text.
        - screen_mode: Current screen being displayed.
        - course_manager: Stores user entered course and grade information.
        - images: Stores all loaded image assets.
        - ui_managers: Stores all UI managers.
        - ui_elements: Stores all UI elements before main screen.

    Representation Invariants:
        - self.screen_mode in {"start_screen", "course_selection", "main"}
    """
    screen: pygame.Surface
    font: pygame.font.Font
    screen_mode: str
    course_manager: CourseManager
    images: _TreeVisualizerImages
    ui_managers: _UIManagers
    ui_elements: _UIElements

    def __init__(self):
        """Initializes an instance of TreeVisualizer"""
        self._initialize_pygame()
        self._initialize_images()
        self._initialize_ui_components()

    def _initialize_images(self) -> None:
        """Private helper that loads and scales all image assets used by the application."""

        # Tuple represents size (Length x Width)

        start_page = pygame.image.load(
            "course_compass_start_ui_screen.png")
        start_page = pygame.transform.smoothscale(start_page, (1440, 780))

        course_selection_page = pygame.image.load(
            "course_compass_course_selection_screen.png")
        course_selection_page = pygame.transform.smoothscale(course_selection_page, (1440, 780))

        course_spec_slider1 = pygame.image.load(
            "course_spec_slider1.png")
        course_spec_slider1 = pygame.transform.smoothscale(course_spec_slider1, (384, 47))

        course_spec_slider2 = pygame.image.load(
            "course_spec_slider2.png")
        course_spec_slider2 = pygame.transform.smoothscale(course_spec_slider2, (384, 47))

        course_spec_slider3 = pygame.image.load(
            "course_spec_slider3.png")
        course_spec_slider3 = pygame.transform.smoothscale(course_spec_slider3, (384, 47))

        course_tree_type_slider1 = pygame.image.load(
            "pre_post_req_slider1.png")
        course_tree_type_slider1 = pygame.transform.smoothscale(course_tree_type_slider1, (330, 47))

        course_tree_type_slider2 = pygame.image.load(
            "pre_post_req_slider2.png")
        course_tree_type_slider2 = pygame.transform.smoothscale(course_tree_type_slider2, (330, 47))

        course_tree_type_slider_image = [course_tree_type_slider1, course_tree_type_slider2]

        selection_check_mark = pygame.image.load(
            "check_mark.png")
        selection_check_mark = pygame.transform.smoothscale(selection_check_mark, (41, 33))

        # Store all loaded images inside the tree visualizer images dataclass
        self.images = _TreeVisualizerImages(start_page,
                                            course_selection_page,
                                            course_spec_slider1,
                                            course_spec_slider2,
                                            course_spec_slider3,
                                            course_tree_type_slider_image,
                                            selection_check_mark)

    def _initialize_ui_components(self) -> None:
        """Private helper that creates and organizes all UI managers and UI elements."""

        # Text Field Constants
        COURSE_CODE_PLACEHOLDER = "Course Code"
        COURSE_CODE_FONT_SIZE = 20
        COURSE_CODE_TOP_LEFT = (492, 208)
        COURSE_CODE_BOTTOM_RIGHT = (610, 230)

        GRADE_PLACEHOLDER = "###"
        GRADE_FONT_SIZE = 20
        GRADE_TOP_LEFT = (704, 203)
        GRADE_BOTTOM_RIGHT = (740, 237)

        # Button Constants
        ADD_COURSE_BUTTON_TOP_LEFT = (801, 167)
        ADD_COURSE_BUTTON_BOTTOM_RIGHT = (971, 260)

        # Create ui managers
        self.course_manager = CourseManager()

        start_screen_ui = UIManager()
        main_screen_ui = MainScreenUI(self.course_manager)
        course_selection_ui = UIManager()

        # Create ui elements
        taken_course_field = TextField(
            COURSE_CODE_PLACEHOLDER,
            COURSE_CODE_FONT_SIZE,
            COURSE_CODE_TOP_LEFT,
            COURSE_CODE_BOTTOM_RIGHT
        )

        grade_mark_field = TextField(
            GRADE_PLACEHOLDER,
            GRADE_FONT_SIZE,
            GRADE_TOP_LEFT,
            GRADE_BOTTOM_RIGHT
        )

        add_course_button = Button(
            ADD_COURSE_BUTTON_TOP_LEFT,
            ADD_COURSE_BUTTON_BOTTOM_RIGHT,
            lambda: self._add_course_to_list()
        )

        # Add ui elements to respective manager
        course_selection_ui.add(taken_course_field)
        course_selection_ui.add(grade_mark_field)
        course_selection_ui.add(add_course_button)

        # Store ui elements and manager to respective data classes
        self.ui_elements = _UIElements(
            taken_course_field,
            grade_mark_field,
            add_course_button
        )

        self.ui_managers = _UIManagers(
            start_screen_ui,
            course_selection_ui,
            main_screen_ui
        )

    def _initialize_pygame(self) -> None:
        """ Private helper that initialize pygame and configures the main application window."""
        pygame.init()
        # screen settings
        screen_width = 1440
        screen_height = 780
        size = (screen_width, screen_height)
        self.screen = pygame.display.set_mode(size)
        self.font = pygame.font.Font("FjallaOne-Regular.ttf", 12)
        # for visual look of app window
        pygame.display.set_caption("U of T Course Compass")
        # set the screen the app starts on
        self.screen_mode = "start_screen"

    def _add_course_to_list(self) -> None:
        """Add the entered course code and grade to the course manager."""
        taken_course_code = self.ui_elements.taken_course_field.get_input_text()
        course_grade = int(self.ui_elements.grade_mark_field.get_input_text())

        self.course_manager.add_course(taken_course_code, course_grade)

    def run_simulation(self) -> None:
        """Run the main pygame event loop."""
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    # Everytime user clicks enter, the screen mode is changed
                    # until app reaches main screen
                    if event.key == pygame.K_RETURN:
                        if self.screen_mode == "start_screen":
                            self.screen_mode = "course_selection"
                        else:
                            self.screen_mode = "main"

                # Each ui manager for each respective screen handles pygame events
                if self.screen_mode == "start_screen":
                    self.ui_managers.start_screen_ui.handle_event(event)
                elif self.screen_mode == "course_selection":
                    self.ui_managers.course_selection_ui.handle_event(event)
                elif self.screen_mode == "main":
                    self.ui_managers.main_screen_ui.handle_event(event)
            # Visually update in appearance the current screen
            if self.screen_mode == "start_screen":
                self.screen.blit(self.images.start_page, (0, 0))

            elif self.screen_mode == "course_selection":
                self.screen.blit(self.images.course_selection_page, (0, 0))
                self.ui_managers.course_selection_ui.update_visually(self.screen)
                course_dict = self.course_manager.get_courses()
                course_list = list(course_dict.items())
                self._display_added_courses(course_list)

            elif self.screen_mode == "main":
                self.screen.fill((255, 255, 255))
                self.ui_managers.main_screen_ui.update_visually(self.screen)

            pygame.display.flip()
        pygame.quit()

    def _display_added_courses(self, course_list: list) -> None:
        """Private helper that displays all entered courses and grades on the course selection screen."""
        for i in range(len(course_list)):
            course, grade = course_list[i]
            text = self.font.render(f"{course}: {grade}", True, (35, 68, 119))
            x = 392
            y = 409 + i * 18
            self.screen.blit(text, (x, y))


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
