"""
Pygame UI framework and interactive course visualization.

This module provides standard UI components (`Button`, `TextField`, `VisualizerInfoBox`)
to handle Pygame rendering and events. It also features `Tree` and `TreeController`
classes for dynamically visualizing and navigating hierarchical academic course networks.
"""

from __future__ import annotations
from typing import Callable, Optional
import webbrowser
import link_of_course
from academic_calendar_reader import PrerequisiteTreeLoader, CourseNotFoundError
from course_tree import CourseTree
from operator import sub

from text_manipulation import display_multiline_text, trim_name
import json

import pygame


class UIElement:
    """
    An abstract class representing a generic UI element.

    UIElement objects define the common interface for all interactive and
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


class TextField(UIElement):
    default_text: str
    font_size: int
    input_text: str
    top_left_cord: tuple
    bottom_right_cord: tuple
    is_active: bool
    clear_default_value: bool
    rect: pygame.Rect

    def __init__(self, default_text: str, font_size: int, top_left_cord: tuple, bottom_right_cord: tuple) -> None:
        self.default_text = default_text
        self.font_size = font_size
        self.top_left_cord = top_left_cord
        self.bottom_right_cord = bottom_right_cord

        self.is_active = False
        self.clear_default_value = False

        self.input_text = default_text
        # creating parameters of rect
        width = bottom_right_cord[0] - top_left_cord[0]
        height = bottom_right_cord[1] - top_left_cord[1]
        self.rect = pygame.Rect(top_left_cord[0], top_left_cord[1], width, height)

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        if ui_event.type == pygame.KEYDOWN and self.is_active:
            if self.default_text in self.input_text:
                self.input_text = ""
            if ui_event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif ui_event.key != pygame.K_RETURN:
                self.input_text += ui_event.unicode
        if ui_event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(ui_event.pos):
                self.is_active = True
            else:
                self.is_active = False

    def update_visually(self, ui_screen) -> None:
        font = pygame.font.Font("FjallaOne-Regular.ttf", self.font_size)
        if self.is_active:
            color = (0, 0, 200)
        else:
            color = (0, 0, 0)
        text_surface = font.render(self.input_text, True, color)
        center_of_rect = self.rect.center
        justified_text_format = (self.top_left_cord[0], center_of_rect[1] - self.font_size // 2)

        ui_screen.blit(text_surface, justified_text_format)

    def show_outline_for_debugging(self, ui_screen) -> None:
        # show outline of field
        pygame.draw.rect(ui_screen, (0, 0, 0), self.rect, 2)


class Button(UIElement):
    top_left_cord: tuple
    bottom_right_cord: tuple
    is_pressed: bool
    rect: pygame.Rect
    on_click: Callable[[], None]

    def __init__(self, top_left_cord: tuple, bottom_right_cord: tuple, on_click: Callable[[], None]) -> None:
        self.is_pressed = False
        self.top_left_cord = top_left_cord
        self.bottom_right_cord = bottom_right_cord
        self.on_click = on_click
        # creating parameters of rect
        width = bottom_right_cord[0] - top_left_cord[0]
        height = bottom_right_cord[1] - top_left_cord[1]
        self.rect = pygame.Rect(top_left_cord[0], top_left_cord[1], width, height)

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        if ui_event.type == pygame.MOUSEBUTTONDOWN and ui_event.button == 1:
            if self.rect.collidepoint(ui_event.pos):
                self.is_pressed = True

        elif ui_event.type == pygame.MOUSEBUTTONUP and ui_event.button == 1:
            if self.is_pressed:
                self.on_click()
            self.is_pressed = False

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        return

    def show_outline_for_debugging(self, ui_screen: pygame.Surface) -> None:

        # Color based on state
        if self.is_pressed:
            color = (255, 0, 0)
        else:
            color = (0, 255, 0)

        pygame.draw.rect(ui_screen, color, self.rect, 2)  # outline only

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
            ui_screen.blit(surface, self.top_left_cord)


class VisualizerInfoBox(UIElement):
    x_pos: int
    y_pos: int
    course_code: str
    course_title: str
    course_description: str
    quality_score: int
    workload_score: int
    assessment_score: int
    number_of_reviews: int
    is_enabled: bool
    is_open: bool
    images: list[pygame.Surface]
    buttons: list[Button]

    def __init__(self, x_pos: int, y_pos: int):
        self.course_title = ""
        self.course_description = ""
        self.selected_course_code = ""
        self.quality_score = -1
        self.workload_score = -1
        self.assessment_score = -1
        self.number_of_reviews = -1
        self.is_enabled = False
        self.is_open = False
        self.x_pos = x_pos
        self.y_pos = y_pos
        background_image = pygame.transform.smoothscale(pygame.image.load("info_panel_cc_v3.png"), (453, 750))
        filled_star_image = pygame.transform.smoothscale(pygame.image.load(
            "ui_star_course_compass.png"), (30, 30))
        background_shield = pygame.transform.smoothscale(pygame.image.load("info_box_shield.png"), (455, 778))
        self.images = [background_image, filled_star_image, background_shield]
        panel_open_button = Button((x_pos + 45, y_pos), (x_pos + 350, y_pos + 45), self.change_state)
        read_more_button = Button((159, 393), (318, 414), self.read_more)
        self.buttons = [panel_open_button, read_more_button]

    def update_information(self, selected_course_code: str, course_title: str, course_description: str,
                           quality_score: int, workload_score: int,
                           assessment_score: int, number_of_reviews: int):
        self.selected_course_code = selected_course_code
        self.course_title = course_title
        self.course_description = course_description
        self.quality_score = quality_score
        self.workload_score = workload_score
        self.assessment_score = assessment_score
        self.number_of_reviews = number_of_reviews

    def handle_interaction(self, ui_event: pygame.event.Event):
        for button in self.buttons:
            button.handle_interaction(ui_event)

    def change_state(self):
        if self.is_enabled:
            if self.is_open:
                self.is_open = False
            else:
                self.is_open = True

    def read_more(self):
        if self.is_enabled and self.is_open:
            webbrowser.open(link_of_course.course_link_generate(self.selected_course_code))

    def update_visually(self, ui_screen):
        if self.is_enabled and self.is_open:
            ui_screen.blit(self.images[2], (self.x_pos, self.y_pos - 20))
            ui_screen.blit(self.images[0], (self.x_pos, self.y_pos))
            self.buttons[0].rect.topleft = (self.x_pos + 45, self.y_pos)
            font_text = pygame.font.Font("RobotoMono-VariableFont_wght.ttf", 12)
            font_heading = pygame.font.Font("FjallaOne-Regular.ttf", 25)
            font_text_styled = pygame.font.Font("FjallaOne-Regular.ttf", 12)

            #visual elements of being open:
            #heading
            heading_x = self.x_pos + 40
            heading_y = self.y_pos + 60
            display_multiline_text("Heading", self.course_title, (heading_x, heading_y), font_heading, ui_screen, None)
            #body text
            text_x = self.x_pos + 40
            text_y = self.y_pos + 140
            display_multiline_text("Body", self.course_description, (text_x, text_y), font_text, ui_screen, None)
            #rate my prof scores:
            with open("course_data_computed.json", "r") as file:
                data = json.load(file)
            course_quality = data[self.selected_course_code]["grouped_metrics"]["course_quality"]
            workload = data[self.selected_course_code]["grouped_metrics"]["workload"]
            assessment_quality = data[self.selected_course_code]["grouped_metrics"]["assessment_quality"]
            _score_visualizer(round(course_quality), 449, self.images[1], ui_screen)
            _score_visualizer(round(workload), 513, self.images[1], ui_screen)
            _score_visualizer(round(assessment_quality), 588, self.images[1], ui_screen)
            top_3_profs = data[self.selected_course_code]["profs_by_rating"][:3]
            for i in range(len(top_3_profs)):
                name = trim_name(top_3_profs[i], 30)
                text_surface = font_text_styled.render(name, True, (35, 68, 119))
                ui_screen.blit(text_surface, (275, 652 + i * 18))
            #num_reviews
            reviews_border_rect = pygame.Rect(171, 726, 307 - 171, 733 - 726)
            num_reviews = data[self.selected_course_code]["num_responses"]
            text_surface = font_text.render(str(num_reviews) + " reviews", True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=reviews_border_rect.center)
            ui_screen.blit(text_surface, text_rect)


        elif self.is_enabled and not self.is_open:
            ui_screen.blit(self.images[2], (self.x_pos, self.y_pos + 800))
            ui_screen.blit(self.images[0], (self.x_pos, self.y_pos + 700))
            self.buttons[0].rect.topleft = (self.x_pos + 45, self.y_pos + 700)


class TextDisplayer(UIElement):
    display_text: str
    x_pos: int
    y_pos: int
    color: Optional[tuple[int, int, int]]

    def __init__(self, display_text: str, x_pos: int, y_pos: int, color: Optional[tuple[int, int, int]] = None):
        self.display_text = display_text
        self.x_pos = x_pos
        self.y_pos = y_pos

        if color is None:
            # set color to black
            self.color = (0, 0, 0)
        else:
            self.color = color

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        font = pygame.font.Font("FjallaOne-Regular.ttf", 25)
        display_multiline_text(
            "Body",
            self.display_text,
            (self.x_pos, self.y_pos),
            font,
            ui_screen,
            self.color
        )

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        return


def _score_visualizer(score: int, y_pos: int, star_image, ui_screen) -> None:
    #precondition:
        #-  score <= 5 and score >= 0
    if score <= 5:
        for i in range(score):
            ui_screen.blit(star_image, (261 + 36 * i, y_pos))



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
                    # if x_pos is on the white space, and its clicking ourside a course, info pannel closes
                    elif current_mouse_pos[0] >= 475:
                        self.course_info_box.is_enabled = False

    def reset_camera(self):
        self.__init__(self.course_info_box, self.loader, self.rect.topleft, self.rect.bottomright)

    def update_info_box(self) -> None:
        selected_course_code = self.code_clicked
        try:
            course_title, description = self.loader.get_name_and_description(self.code_clicked)
        except CourseNotFoundError:
            # Check if the info box is currently not displaying anything
            if self.course_info_box.course_title == "":
                # The info box is not displaying anything, so it shouldn't pop up (sorry you can rewrite these
                # comments lol they're trash idk how your code works
                self.course_info_box.is_enabled = False
            return
        course_quality_score = 0
        assessment_score = 0
        workload_score = 0
        number_of_reviews = 0
        prof_ranking = []
        self.course_info_box.update_information(selected_course_code, course_title, description, course_quality_score,
                                                assessment_score, workload_score, number_of_reviews)

    def show_outline_for_debugging(self, ui_screen: pygame.Surface) -> None:
        color = (255, 0, 255)
        pygame.draw.rect(ui_screen, color, self.rect, 2)

class CourseDifference(TreeController):
    course1_to_compare: str
    course2_to_compare: str
    course1_exclusive: set[str]
    course2_exclusive: set[str]
    same_to_both: set[str]
    info_box: VisualizerInfoBox


    def __init__(self, course_info_box: VisualizerInfoBox, loader: PrerequisiteTreeLoader) -> None:
        super().__init__(course_info_box, loader,(480, 30), (1400, 750))
        self.course1_to_compare = ""
        self.course2_to_compare = ""
        self.course1_exclusive = set()
        self.course2_exclusive = set()
        self.same_to_both = set()
        self.info_box = course_info_box

    def reset_camera(self) -> None:
        print(self.course1_exclusive)
        print(self.same_to_both)
        print(self.course2_exclusive)
        self.top_left_coord = (480, 30)
        self.bottom_right_coord = (1400, 750)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        self.node_course_code_map.clear()

        HORIZONTAL_SPACING = int(400 * self.zoom_factor)
        VERTICAL_SPACING = int(150 * self.zoom_factor)

        TITLE_OFFSET_FACTOR = 50
        font_size = max(12, int(24 * self.zoom_factor))
        font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
        text = font.render(f"Courses Exclusive To {self.course1_to_compare}:", True, (35, 68, 119))
        ui_screen.blit(text, (self.x_pos_tree - HORIZONTAL_SPACING,  self.y_pos_tree))

        for idx, course_code in enumerate(self.course1_exclusive):
            self.draw_node(
                (course_code, ""),
                (self.x_pos_tree - HORIZONTAL_SPACING, self.y_pos_tree + (idx+1) * VERTICAL_SPACING - TITLE_OFFSET_FACTOR),
                self.zoom_factor,
                [],
                ui_screen
            )

        text = font.render("Courses Mutual to Both:", True, (35, 68, 119))
        ui_screen.blit(text, (self.x_pos_tree, self.y_pos_tree))
        for idx, course_code in enumerate(self.same_to_both):
            self.draw_node(
                (course_code, ""),
                (self.x_pos_tree, self.y_pos_tree + (idx+1) * VERTICAL_SPACING - TITLE_OFFSET_FACTOR),
                self.zoom_factor,
                [],
                ui_screen
            )

        text = font.render(f"Courses Exclusive To {self.course2_to_compare}:", True, (35, 68, 119))
        ui_screen.blit(text, (self.x_pos_tree + HORIZONTAL_SPACING, self.y_pos_tree))
        for idx, course_code in enumerate(self.course2_exclusive):
            self.draw_node(
                (course_code, ""),
                (self.x_pos_tree + HORIZONTAL_SPACING, self.y_pos_tree + (idx+1) * VERTICAL_SPACING - TITLE_OFFSET_FACTOR),
                self.zoom_factor,
                [],
                ui_screen
            )


    def handle_interaction(self, mouse_event: pygame.event.Event) -> None:
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
    The UI element for tree
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
    #   - tree_camera: a TreeCamera to be used to control the tree
    #   - course_tree: a CourseTree to be displayed

    tree_camera: TreeController
    course_tree: CourseTree

    def __init__(self, tree_camera: TreeController, course_tree: CourseTree) -> None:
        super().__init__()
        self.tree_camera = tree_camera
        self.course_tree = course_tree

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        self.tree_camera.handle_interaction(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
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

    def show_outline_for_debugging(self, ui_screen: pygame.Surface) -> None:
        self.tree_camera.show_outline_for_debugging(ui_screen)
