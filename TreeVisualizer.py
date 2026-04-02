"""Docstring  # TODO: insert docstring

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""


import pygame

from dataclasses import dataclass

from ui_manager import UIManager, CourseManager, MainScreenUI
from ui_element import TextField, Button


@dataclass
class _TreeVisualizerImages:
    """docstring"""
    start_page: pygame.Surface
    course_selection_page: pygame.Surface
    course_spec_slider1: pygame.Surface
    course_spec_slider2: pygame.Surface
    course_spec_slider3: pygame.Surface
    course_tree_type_slider_image: list[pygame.Surface]
    selection_check_mark: pygame.Surface


class TreeVisualizer:
    """docstring"""
    screen: pygame.Surface
    font: pygame.font.Font
    screen_mode: str
    images: _TreeVisualizerImages
    start_screen_ui: UIManager
    main_screen_ui: MainScreenUI
    taken_course_field: TextField
    grade_mark_field: TextField
    add_course_button: Button
    course_selection_ui: UIManager

    def __init__(self):
        # ---------------------------------------------------------------------
        # LOAD CANVAS
        # ---------------------------------------------------------------------
        pygame.init()
        screen_width = 1440
        screen_height = 780
        size = (screen_width, screen_height)
        self.screen = pygame.display.set_mode(size)
        self.font = pygame.font.Font("FjallaOne-Regular.ttf", 12)

        # for window visual look
        pygame.display.set_caption("U of T Course Compass")
        icon = pygame.image.load("course_compass_logo.png")
        pygame.display.set_icon(icon)

        self.screen_mode = "main"

        self._initialize_images()

        # ---------------------------------------------------------------------
        # Variables
        # ---------------------------------------------------------------------
        self.start_screen_ui = UIManager()

        self.course_manager = CourseManager()  # TODO: this will come from the other screen

        self.main_screen_ui = MainScreenUI(self.course_manager)

        self.taken_course_field = TextField("Course Code", 20, (492, 208), (610, 230))
        self.grade_mark_field = TextField("###", 20, (704, 203), (740, 237))
        self.add_course_button = Button((801, 167), (971, 260),
                                        lambda: self._add_course_to_list())
        self.course_selection_ui = UIManager()
        self.course_selection_ui.add(self.taken_course_field)
        self.course_selection_ui.add(self.grade_mark_field)
        self.course_selection_ui.add(self.add_course_button)

    def _initialize_images(self):  # TODO: make sure to add return types on ALLLLL your methods and functions
        """docstring"""
        start_page = pygame.image.load(
            "course_compass_startup_screen_v2.png")
        start_page = pygame.transform.smoothscale(start_page, (1440, 780))

        course_selection_page = pygame.image.load(
            "course_compass_course_selection_v3.png")
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

        self.images = _TreeVisualizerImages(start_page,
                                            course_selection_page,
                                            course_spec_slider1,
                                            course_spec_slider2,
                                            course_spec_slider3,
                                            course_tree_type_slider_image,
                                            selection_check_mark)

    def _add_course_to_list(self):
        """docstring"""
        taken_course_code = self.taken_course_field.input_text
        course_grade = int(self.grade_mark_field.input_text)

        self.course_manager.add_course(taken_course_code, course_grade)

    def run_simulation(self):
        """docstring"""
        # ---------------------------------------------------------------------
        # MAIN LOOP
        # ---------------------------------------------------------------------
        done = False
        while not done:
            for event in pygame.event.get():
                # uncomment below for dev mode
                if event.type == pygame.QUIT:
                    done = True
                if self.screen_mode == "start_screen":
                    self.start_screen_ui.handle_event(event)
                elif self.screen_mode == "course_selection":
                    self.course_selection_ui.handle_event(event)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                        screen_mode = "main"  # TODO: REMOVE - TEMP
                elif self.screen_mode == "main":
                    # main_screen_ui.tree_camera.handle_interaction(event) #TODO:redundent
                    self.main_screen_ui.handle_event(event)
                    # TEMPORARLY uses enter key to take input from search bar, eventually this will be a button
                    # TODO: error check input
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            pass

            if self.screen_mode == "start_screen":
                self.screen.blit(self.images.start_page, (0, 0))
            elif self.screen_mode == "course_selection":
                self.screen.blit(self.images.course_selection_page, (0, 0))
                self.course_selection_ui.update_visually(self.screen)

                course_dict = self.course_manager.get_courses()
                course_list = list(course_dict.items())

                for i in range(len(course_list)):
                    course, grade = course_list[i]

                    text = self.font.render(f"{course}: {grade}", True, (35, 68, 119))

                    if i < 19:
                        x = 392
                        y = 409 + i * 18
                    else:
                        x = 392 + 50
                        y = 409 + (i - 19) * 18

                    self.screen.blit(text, (x, y))
            elif self.screen_mode == "main":
                self.screen.fill((255, 255, 255))

                self.main_screen_ui.update_visually(self.screen)

            pygame.display.flip()
        pygame.quit()
