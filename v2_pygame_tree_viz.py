#-------------------------IMPORTS--------------------#
# Tree class
from __future__ import annotations

from operator import add
from typing import Callable
import textwrap
import webbrowser
import link_of_course
import json
from pygame.examples.scroll import zoom_factor

from optimal_path_to_course import optimal_path_to_course
from post_req_tree import PostrequisiteTreeLoader

from academic_calendar_reader import PrerequisiteTreeLoader, CourseNotFoundError
from dataclasses import dataclass
from typing import Any, Optional
import pygame
from course_tree import CourseTree
#------------------------------------------#
#------------------------------------------#
#------------------------------------------#
#TODO: APPSTATE maybe not needed
@dataclass
class AppState:
    # for rep invairants add that tree type is either pre req or post req
    current_course_tree: CourseTree | None = CourseTree(None, -1, [])
    current_tree_type: str = "prerequisite"
    is_current_tree_simplified: bool = False

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

class UIManager:
    """
    A class responsible for managing a collection of UI elements.
    The class stores UI elements and provides methods to pass
    events and drawing updates to each component.

    Instance Attributes:
        - ui_components: a list of UIElement objects managed by this UIManager
    """
    ui_components: list[UIElement | UIManager]
    def __init__(self):
        """Initialize a new UI Manager object"""
        self.ui_components = []

    def add(self, element):
        """Add a UI element to the manager"""
        self.ui_components.append(element)

    def handle_event(self, ui_event):
        """Pass a pygame event to every managed UI element"""
        for item in self.ui_components:
            item.handle_interaction(ui_event)

    def update_visually(self, ui_screen):
        """visually update appearance of every managed UI element."""
        for item in self.ui_components:
            item.update_visually(ui_screen)

@dataclass
class CourseTreeOptions:
    """
    A class storing the selectable options
    """
    # Static attributes:
    #   - PREREQ: an int representing the fact that the tree type displayed should be a prereq tree
    #   - POSTREQ: an int representing the fact that the tree type displayed should be a postreq tree
    PREREQ = 0
    POSTREQ = 1



@dataclass
class CourseSpectrumOptions:
    """
    A class that contains a mapping from the course spectrum slider index
    to metric name and whether a higher metric rating is better
    """
    idx_to_metric = {
        0: ("overall_satisfaction", True),
        1: ("workload", False),
        2: ("cognitive_growth", True)
    }


class Slider(UIManager):
    """
    A class for a slider UI manager that handles toggling between multiple options
    This is a UI manager because it contains a collection of buttons

    Representation Invariants:
        - 0 <= curr_selection < num_options
        - num_options == len(option_filepaths) == len(option_surfaces) == len(option_coords)
        - option_surface[i] is constructed from option_filepath[i] for any i in range(num_options)
        - option_buttons[i] has top left and bottom right coords from option_coords[i] for any i in range(num_options)
    """
    # Instance Attributes:
    #   - curr_selection: an int representing the index of the currently selected option
    #   - num_options: an int representing the number of options for the slider
    #   - option_filepaths: a list of filepaths where the slider options are located
    #   - option_surfaces: a list of pygame Surfaces representing the various options
    #   - option_buttons: a list of Buttons representing the slider options
    #   - option_coords: a list of coords representing the slider options
    #   - slider_size: a tuple representing the width and height of each slider option
    curr_selection: int
    num_options: int
    option_filepaths: list[str]
    option_surfaces: list[pygame.Surface]
    option_buttons: list[Button]
    option_coords: list[tuple[tuple[int, int], tuple[int, int]]]
    slider_size: tuple[int, int]

    def __init__(self,
                 option_filepaths: list[str],
                 option_coords: list[tuple[tuple[int, int], tuple[int, int]]],
                 slider_size: tuple[int, int]) -> None:
        """
        Initializes an instance of Slider
        option_coords is a list of top left and bottom right coordinates of the slider option buttons
        """
        super().__init__()
        self.option_filepaths = option_filepaths
        self.option_coords = option_coords
        self.num_options = len(self.option_filepaths)

        self.slider_size = slider_size
        self.curr_selection = 0

        # construct option surfaces from filepaths
        self.option_surfaces = []
        # construct option buttons from filepaths
        self.option_buttons = []

        for option_id in range(self.num_options):
            option_img = pygame.image.load(option_filepaths[option_id])
            option_surface = pygame.transform.smoothscale(option_img, slider_size)
            self.option_surfaces.append(option_surface)

            button_coords = self.option_coords[option_id]
            top_left, bottom_right = button_coords
            option_button = Button(
                top_left,
                bottom_right,
                lambda option_id=option_id: self.change_selection(option_id)
            )

            self.option_buttons.append(option_button)

    def change_selection(self, to_id: int) -> None:
        """
        Changes the slider selection to id
        """
        print(f"switched from {self.curr_selection} to {to_id}")
        self.curr_selection = to_id

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """
        handle interaction
        """
        if ui_event.type == pygame.MOUSEBUTTONDOWN:
            print(f"curr selection: {self.curr_selection}")
            # print(f"{self.option_buttons}")
            print("button coords:")
            print([(b.top_left_cord, b.bottom_right_cord) for b in self.option_buttons])
        for button in self.option_buttons:
            button.handle_interaction(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        update visually
        """

        selected_option_surface = self.option_surfaces[self.curr_selection]
        #always draw slider at same location b/c its the same image in a diffrent state
        coords = self.option_coords[0]
        ui_screen.blit(selected_option_surface, coords)

    def show_outline_for_debugging(self, ui_screen) -> None:
        # show outline of options
        for button in self.option_buttons:
            pygame.draw.rect(ui_screen, (0, 255, 0), button.rect, 2)


class MainScreenUI(UIManager):
    """
    A class that contains utilities and manages state for the main screen

    Representation Invariants:
        - 0 <= self.panel_output_mode <= 2  # panel output mode is a valid output mode
    """
    # Static attributes: (note that these are constants that will not be modified)
    #   - TREE_OUTPUT: an int representing the fact that the panel should output a tree
    #   - TEXT_OUTPUT: an int representing the fact that the panel should output text
    #   - ERROR_OUTPUT: an int representing the fact that the panel should output an error
    #   - BG_PATH: a str representing the file path to the UI background
    TREE_OUTPUT = 0
    TEXT_OUTPUT = 1
    ERROR_OUTPUT = 2
    BG_PATH = "course_compass_main_v6.png"

    # Instance attributes:
    #   - panel_output_mode: an int representing what type of data the panel output should display
    #   - tree_type: int
    #   - tree_camera: a TreeCamera object for the Tree UI element
    #   - course_tree: a CourseTree object for the Tree UI element
    #   - info_box: a VisualizerInfoBox representing the info box UI element
    #   - visualizer_search_field: a TextField for the course search bar
    #   - summer_offering_button: a Button for the summer offerings feature
    #   - error_displayer: a TextDisplayer for displaying a red error message
    #   - text_displayer: a TextDisplayer for displaying regular plaintext output
    #   - course_spectrum_slider: a Slider for selecting a metric
    #   - course_spectrum_button: a Button to generate a tree based on course_spectrum_slider

    panel_output_mode: int
    tree_type: int
    tree_camera: TreeCamera
    course_tree: CourseTree
    info_box: VisualizerInfoBox
    visualizer_search_field: TextField
    summer_offering_button: Button
    error_displayer: TextDisplayer
    text_displayer: TextDisplayer
    course_spectrum_generate_button: Button
    course_spectrum_slider: Slider
    # TODO: add a slider to select b/w tree heatmap and optimal path

    # TODO: use this and comment it
    course_tree_options: CourseTreeOptions
    course_tree_slider: Slider
    course_tree_generate_button: Button
    course_tree_simplify: bool

    # Private instance attributes:
    #   - _tree_ui_element: a Tree UI element storing the tree to be displayed
    #   - _background_surface: a pygame Surface object for the main screen background
    _tree_ui_element: Tree
    _background_surface: pygame.Surface

    def __init__(self):
        """Initialize a new MainScreenUI object"""
        super().__init__()

        # set default panel output mode
        self.panel_output_mode = MainScreenUI.TREE_OUTPUT

        # initialize an error message displayer
        # for error messages to be displayed, set error_displayer.display_text to the message you want to display
        red_error_color = (255, 0, 0)
        self.error_displayer = TextDisplayer("", 520, 70, red_error_color)

        # initialize a text displayer
        # for text outputs to be displayed, set text_displayer.display_text to the text you want to display
        self.text_displayer = TextDisplayer("", 520, 70)

        # load background image from file path and make it a surface
        bg_image = pygame.image.load(MainScreenUI.BG_PATH)
        self._background_surface = pygame.transform.smoothscale(bg_image, (1440, 780))

        # create info box and add it to ui elements
        self.info_box = VisualizerInfoBox(5, 25)
        self.ui_components.append(self.info_box)
        self.visualizer_search_field = TextField(
            "Search Course",
            30,
            (98, 29),
            (418, 73)
        )
        # append to ui_components list for handle_event to work properly
        # TODO: remove once handle_event is implemented based on panel_output mode
        self.ui_components.append(self.visualizer_search_field)

        self.summer_offering_button = Button(
            (272, 575),
            (424, 600),
            lambda: show_summer_offerings(self.visualizer_search_field.input_text),
        )
        # append to ui_components list for handle_event to work properly
        # TODO: remove once handle_event is implemented based on panel_output mode
        self.ui_components.append(self.summer_offering_button)

        ################################
        # Course Tree related elements #
        ################################
        self.course_tree_slider = Slider(
            ["pre_post_req_slider1.png", "pre_post_req_slider2.png"],
            [
                ((75, 180), (240, 225)),
                ((240, 180), (400, 225))
            ],
            (330, 47)
        )
        self.ui_components.append(self.course_tree_slider)

        # construct the tree ui element from a TreeCamera and CourseTree
        self.tree_camera = TreeCamera(self.info_box)
        self.course_tree = CourseTree(None, -1, [])  # set course_tree to an empty tree as the default value
        self._tree_ui_element = Tree(self.tree_camera, self.course_tree)

        # append to ui_components list for handle_event to work properly
        # TODO: remove once handle_event is implemented based on panel_output mode
        self.ui_components.append(self._tree_ui_element)

        self.course_tree_simplify = True  # TODO: make this based on checkbox

        # course tree "Generate" button
        # CourseTreeOptions contains a mapping from the prereq/postreq slider's selected id
        # to look up in course_data_computed.json
        self.course_tree_generate_button = Button(
            (165, 275),
            (315, 298),
            lambda: generate_course_tree(
                self.visualizer_search_field.input_text,
                self.course_tree_slider.curr_selection,
                self.course_tree_simplify
            )
        )
        self.ui_components.append(self.course_tree_generate_button)

        ####################################
        # Course Spectrum related elements #
        ####################################

        # x boundaries of the course spectrum slider
        left_x = 45
        right_x = 430

        # y boundaries of the course spectrum slider
        top_y = 400
        bottom_y = 445

        # there are three elements: overall_satisfaction, workload, and cognitive_growth
        num_elements = 3

        # the width of each button in the slider
        width = (right_x - left_x) // num_elements

        # create a Slider object to select a metric
        self.course_spectrum_slider = Slider(
        ["course_spec_slider1.png", "course_spec_slider2.png", "course_spec_slider3.png"],
                [
                    ((left_x + 0*width, top_y), (left_x + 1*width, bottom_y)),
                    ((left_x + 1*width, top_y), (left_x + 2*width, bottom_y)),
                    ((left_x + 2*width, top_y), (left_x + 3*width, bottom_y)),
                ],
            (384, 47)
        )

        self.ui_components.append(self.course_spectrum_slider)

        # course spectrum "Generate" button
        # CourseSpectrumOptions contains a mapping from the metric slider's selected id to the metric name
        # to look up in course_data_computed.json
        self.course_spectrum_generate_button = Button(
            (165, 495),
            (315, 515),
            lambda: generate_course_spectrum_tree(
                self.visualizer_search_field.input_text,
                CourseSpectrumOptions.idx_to_metric[self.course_spectrum_slider.curr_selection][0],
                CourseSpectrumOptions.idx_to_metric[self.course_spectrum_slider.curr_selection][1],
            )
        )

        # append to ui_components list for handle_event to work properly
        # TODO: remove once handle_event is implemented based on panel_output mode
        self.ui_components.append(self.course_spectrum_generate_button)

    def handle_event(self, ui_event):
        """Handles a UI event"""
        # the default implementation is to call handle_interaction on all elements in the ui_components list
        # TODO: call handle_interaction based on panel_output_mode
        super().handle_event(ui_event)

    def update_visually(self, ui_screen) -> None:
        """Update the screen based on the panel output mode"""

        # update UI elements that depend on panel output mode

        if self.panel_output_mode == MainScreenUI.TREE_OUTPUT:
            self._tree_ui_element.update_visually(ui_screen) #TODO; second bug fix
        elif self.panel_output_mode == MainScreenUI.TEXT_OUTPUT:
            self.text_displayer.update_visually(ui_screen)
        elif self.panel_output_mode == MainScreenUI.ERROR_OUTPUT:
            self.error_displayer.update_visually(ui_screen)
        else:
            print("!!! No valid screen panel output mode was set !!!")

        ui_screen.blit(self._background_surface, (0, 0))
        self.visualizer_search_field.update_visually(ui_screen)

        # display the info pannel on top of everything
        if self.panel_output_mode == MainScreenUI.TREE_OUTPUT:
            self.info_box.update_visually(ui_screen)  # TODO: THIRD BUG FIX

        self.course_tree_slider.update_visually(ui_screen)
        self.course_tree_slider.show_outline_for_debugging(ui_screen)
        self.course_tree_generate_button.show_outline_for_debugging(ui_screen)

        self.course_spectrum_slider.update_visually(ui_screen)
        self.course_spectrum_slider.show_outline_for_debugging(ui_screen)

class CourseManager:
    """

    """
    courses: list[tuple[str, int]]
    def __init__(self):
        self.courses = []  # list of (course_code, grade)

    def add_course(self, code: str, course_grade: int):
        self.courses.append((code, course_grade))

    def get_courses(self):
        return self.courses

    def get_dict(self) -> dict[str, int]:  # TODO: Get rid of this later
        dictionary = {}
        for current_course_code in self.courses:
            dictionary[current_course_code[0]] = course[1]

        return dictionary

class TextField(UIElement):
    default_text: str
    font_size: int
    input_text: str
    top_left_cord: tuple
    bottom_right_cord: tuple
    is_active: bool
    clear_default_value: bool
    rect: pygame.Rect

    def __init__(self, default_text: str, font_size:int, top_left_cord: tuple, bottom_right_cord: tuple) -> None:
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
        # TODO: see if all vars here are needed - also can i do this much in innit?

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
    on_click: Callable[[], None]  # TODO:i learned this today, ask group if okay

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
        self.images = [background_image,filled_star_image, background_shield]
        panel_open_button = Button((x_pos + 45, y_pos), (x_pos + 350, y_pos + 45), self.change_state)
        read_more_button = Button((159,393), (318, 414), self.read_more)
        self.buttons = [panel_open_button,read_more_button]

    def update_information(self, selected_course_code: str, course_title: str, course_description: str, quality_score: int, workload_score: int,
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
            ui_screen.blit(self.images[2], (self.x_pos, self.y_pos-20))
            ui_screen.blit(self.images[0], (self.x_pos, self.y_pos))
            self.buttons[0].rect.topleft = (self.x_pos+45, self.y_pos)
            font_text = pygame.font.Font("RobotoMono-VariableFont_wght.ttf", 12)
            font_heading = pygame.font.Font("FjallaOne-Regular.ttf", 25)
            font_text_styled =  pygame.font.Font("FjallaOne-Regular.ttf", 12)

            #visual elements of being open:
            #heading
            heading_x = self.x_pos + 40
            heading_y = self.y_pos + 60
            display_multiline_text("Heading", self.course_title,(heading_x, heading_y), font_heading, ui_screen, None)
            #body text
            text_x = self.x_pos + 40
            text_y = self.y_pos + 140
            display_multiline_text("Body", self.course_description,(text_x, text_y), font_text, ui_screen, None)
            #rate my prof scores:
            with open("course_data_computed.json", "r") as file:
                data = json.load(file)
            course_quality = data[self.selected_course_code]["grouped_metrics"]["course_quality"]
            workload = data[self.selected_course_code]["grouped_metrics"]["workload"]
            assessment_quality = data[self.selected_course_code]["grouped_metrics"]["assessment_quality"]
            score_visualizer(round(course_quality), 449, self.images[1], ui_screen)
            score_visualizer(round(workload), 513, self.images[1], ui_screen)
            score_visualizer(round(assessment_quality), 588, self.images[1], ui_screen)
            top_3_profs = data[self.selected_course_code]["profs_by_rating"][:3]
            for i in range(len(top_3_profs)):
                name = trim_name(top_3_profs[i], 30)
                text_surface = font_text_styled.render(name, True, (35,68,119))
                ui_screen.blit(text_surface, (275, 652 + i*18))
            #num_reviews
            reviews_border_rect = pygame.Rect(171, 726, 307 - 171, 733 - 726)
            num_reviews = data[self.selected_course_code]["num_responses"]
            text_surface = font_text.render(str(num_reviews) + " reviews", True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=reviews_border_rect.center)
            ui_screen.blit(text_surface, text_rect)


        elif self.is_enabled and not self.is_open:
            ui_screen.blit(self.images[2], (self.x_pos, self.y_pos + 800))
            ui_screen.blit(self.images[0], (self.x_pos, self.y_pos + 700))
            self.buttons[0].rect.topleft = (self.x_pos+45, self.y_pos + 700)

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


def score_visualizer(score: int, y_pos: int, star_image, ui_screen) -> None:
    if score <= 5:
        for i in range(score):
            ui_screen.blit(star_image, (261 + 36 * i, y_pos))
    #todo:raise error
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
    name = name.split(",")[0] #takes last name only
    if len(name) > max_length:
        return name[:max_length - 3] + "..."
    return name

def switch_to_main():
    global screen_mode
    screen_mode = "main"

def switch_to_course_select():
    global screen_mode
    screen_mode = "course_selection"

def add_course_to_list(course_manager_to_update: CourseManager, taken_course_code: str, course_mark: str):
    course_grade = int(course_mark)
    course_manager_to_update.add_course(taken_course_code, course_grade)


def show_summer_offerings(course: str) -> None:
    """
    Display the summer offerings of a course compared to the total number of years it was offered,
     as well as the most recent summer offering
    """
    # extract course eval data
    with open("course_data_computed.json", "r") as file:
        data = json.load(file)

    try:
        # access summer offerings data from json
        summer_offerings_data = data[course]["summer_offerings"]
    except KeyError:
        # course is not in json
        # TODO: handle error
        print(f"[ERROR] Could not find '{course}' in course_data_computed.json")
        main_screen_ui.error_displayer.display_text = f"Could not find summer course data for '{course}'"
        main_screen_ui.panel_output_mode = MainScreenUI.ERROR_OUTPUT
    else:
        total_years_offered = data[course]["num_years_offered"]
        summer_years_offered = summer_offerings_data["num_years_offered"]
        most_recent_year = summer_offerings_data["most_recent_year"]

        # combine data into an informative string
        summer_info_text = (f"{course} has been offered in the summer {summer_years_offered} times in its "
                f"{total_years_offered} year history, most recently in {most_recent_year}.")
        # display on main screen
        main_screen_ui.text_displayer.display_text = summer_info_text
        main_screen_ui.panel_output_mode = MainScreenUI.TEXT_OUTPUT


def generate_course_spectrum_tree(course: str, metric: str, higher_is_better: bool):
    """
    Display a course spectrum tree based on the given course code
    """
    try:
        prereq_tree = loader.get_prerequisite_tree(course)
    except CourseNotFoundError:
        # handle errors by setting the error display text
        if course == "":
            main_screen_ui.error_displayer.display_text = "Please enter a non-empty course code"
        else:
            main_screen_ui.error_displayer.display_text = \
                f"The course '{course}' is invalid or doesn't exist"

        # change panel output mode to error output
        main_screen_ui.panel_output_mode = MainScreenUI.ERROR_OUTPUT
    else:
        courses_taken_tuple = course_manager.get_courses()
        courses_taken = {}

        # convert the courses_taken tuple returned by course_manager to a dict
        for key_val_pair in courses_taken_tuple:
            key, val = key_val_pair
            courses_taken[key] = val

        # TODO: remove in final submission
        # default values of courses_taken used for testing
        courses_taken = {
            'MAT137Y1': 100,
            'CSC110Y1': 100,
            'CSC111H1': 100,
            'MAT223H1': 100,
            'STA237H1': 100
        }

        optimal_tree = optimal_path_to_course(
            loader,
            course,
            courses_taken,
            metric,
            higher_is_better
        )

        main_screen_ui.course_tree = optimal_tree
        main_screen_ui.tree_camera.reset_camera()
        main_screen_ui.panel_output_mode = MainScreenUI.TREE_OUTPUT


def generate_course_tree(course_code: str, tree_type: int, simplified: bool) -> None:
    """
    Generate a course tree given a course code and tree type
    simplified dictates whether the tree is simplified
    we do not simplify the course tree if it's a postrequisite tree

    Preconditions:
        - tree_type in {CourseTreeOptions.PREREQ, CourseTreeOptions.POSTREQ}
    """
    courses_taken_tuple = course_manager.get_courses()
    courses_taken = {}

    # TODO: remove in final submission
    # default values of courses_taken used for testing
    courses_taken = {
        'MAT137Y1': 100,
        'CSC110Y1': 100,
        'CSC111H1': 100,
        'MAT223H1': 100,
        'STA237H1': 100
    }

    # convert the courses_taken tuple returned by course_manager to a dict
    for key_val_pair in courses_taken_tuple:
        key, val = key_val_pair
        courses_taken[key] = val

    try:
        if tree_type == CourseTreeOptions.PREREQ:
            # get prereq tree
            prereq_tree = loader.get_prerequisite_tree(course_code)
            if simplified:
                prereq_tree.simplify_tree(courses_taken)
            main_screen_ui.course_tree = prereq_tree
        else:
            # tree type is a postreq tree
            # we do not simplify the course tree if it's a postrequisite tree
            postreq_tree = loader.get_postrequisite_tree(course_code)
            main_screen_ui.course_tree = postreq_tree
    except CourseNotFoundError:
        # handle errors by setting the error display text
        if course_code == "":
            main_screen_ui.error_displayer.display_text = "Please enter a non-empty course code"
        else:
            main_screen_ui.error_displayer.display_text = \
                f"The course '{course_code}' is invalid or doesn't exist"

        # change panel output mode to error output
        main_screen_ui.panel_output_mode = MainScreenUI.ERROR_OUTPUT
    else:
        # set panel output mode to tree output
        main_screen_ui.tree_camera.reset_camera()
        main_screen_ui.panel_output_mode = MainScreenUI.TREE_OUTPUT


def ui_dev_mode(ui_screen, ui_event):
    # TODO:delete this before final submission
    pygame.mouse.set_visible(False)

    position = pygame.mouse.get_pos()
    x = position[0]
    y = position[1]

    cursor_size = 3
    pygame.draw.rect(screen, (255, 0, 0), (x, y, cursor_size, cursor_size))

    if ui_event.type == pygame.MOUSEBUTTONDOWN:
        print(f"coords clicked: {x}, {y}")

#TODO: handle jacobs version april 1
# def set_prereq_tree():
#     app_state.current_tree_type = "prerequisite"
#
# def set_postreq_tree():
#     app_state.current_tree_type = "postrequisite"
# def set_simplified_tree():
#     if app_state.is_current_tree_simplified:
#         app_state.is_current_tree_simplified = False
#     else:
#         app_state.is_current_tree_simplified = True
#
# def generate_tree(loader: PrerequisiteTreeLoader):
#     print('h')
#     current_course = visualizer_search_field.input_text
#     # CASE 1: Postrequisite
#     if app_state.current_tree_type.lower() == 'postrequisite':  # TODO:
#         app_state.current_course_tree = loader.get_postrequisite_tree(current_course)
#     # Case 2: prereq unsimplified
#     elif app_state.current_tree_type.lower() == 'prerequisite' and not app_state.is_current_tree_simplified:  # TODO:
#         app_state.current_course_tree = loader.get_prerequisite_tree(current_course)
#     # Case 3: prereq simplified
#     else:
#         courses_taken = course_manager.get_dict()
#         app_state.current_course_tree = loader.get_prerequisite_tree(current_course).simplify_tree(courses_taken)
#
#     tree_camera.reset_camera()
#TODO: APP STATE IS GLOBAL? STATIC methods turn into functions?
class Tree(UIElement):
    """
    The UI element for tree
    """
    tree_camera: TreeCamera
    course_tree: CourseTree

    def __init__(self, tree_camera: TreeCamera, course_tree: CourseTree) -> None:
        super().__init__()
        self.tree_camera = tree_camera
        self.course_tree = course_tree

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        self.tree_camera.handle_interaction(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        self.tree_camera.node_course_code_map.clear() #TODO: first bug fixed for info box error

        self.draw_tree_visualization(main_screen_ui.course_tree, (self.tree_camera.x_pos_tree,
                                self.tree_camera.y_pos_tree), 300, self.tree_camera.zoom_factor,
                                self.tree_camera.node_course_code_map, ui_screen)

    def draw_tree_visualization(self, tree: CourseTree, positions: tuple[int,int], spacing_factor: int, tree_zoom_factor: int,
                                node_course_code_map: list[tuple[pygame.Rect, str]], target_screen: pygame.Surface) -> None:
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

                # Constants for tree layout
                NODE_WIDTH = 200
                NODE_HEIGHT = 50
                VERTICAL_SPACING = 150
                LINE_THICKNESS = 4
                LINE_COLOR = (0, 0, 0)

                # Draw line from parent to child
                pygame.draw.line(
                    target_screen, LINE_COLOR,
                    (x_pos + int(NODE_WIDTH / 2 * tree_zoom_factor),
                     y_pos + int(NODE_HEIGHT * tree_zoom_factor)),
                    (child_x + int(NODE_WIDTH / 2 * tree_zoom_factor),
                     y_pos + int(VERTICAL_SPACING * tree_zoom_factor)),
                    max(1, int(LINE_THICKNESS * tree_zoom_factor))
                )

                self.draw_tree_visualization(subtree, (child_x, y_pos + int(VERTICAL_SPACING * tree_zoom_factor)),
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

class TreeCamera:
    x_pos_tree: int
    y_pos_tree: int
    dragging: bool
    zoom_factor: int
    previous_mouse_pos: tuple
    node_course_code_map: list[tuple[pygame.Rect, str]]
    code_clicked: str | None
    initial_mouse_down_pos: tuple[int, int] | None
    course_info_box: VisualizerInfoBox

    def __init__(self, course_info_box: VisualizerInfoBox) -> None:
        self.x_pos_tree = 838
        self.y_pos_tree = 100
        self.dragging = False
        self.zoom_factor = 1
        self.previous_mouse_pos = (0, 0)
        self.initial_mouse_down_pos = None
        self.node_course_code_map = []
        self.code_clicked = None
        self.course_info_box = course_info_box

    def handle_interaction(self, mouse_event: pygame.event.Event) -> None:
        if mouse_event.type == pygame.MOUSEWHEEL:
            if mouse_event.y > 0:
                self.zoom_factor *= 1.1
            elif mouse_event.y < 0:
                self.zoom_factor *= 0.9
            # TODO:is limit on zoom needed?
            # screen_zoom_factor = max(0.3, min(screen_zoom_factor, 3))
        # the start of mouse drag based tree movement
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
                        print(self.code_clicked)
                        self.course_info_box.is_enabled = True
                        self.update_info_box()
                    self.code_clicked = None
                # if x_pos is on the white space, and its clicking ourside a course, info pannel closes
                elif current_mouse_pos[0] >= 475:
                    self.course_info_box.is_enabled = False

    def reset_camera(self):
        self.__init__(self.course_info_box)

    def update_info_box(self) -> None:
        selected_course_code = self.code_clicked
        # TODO: Hi Shayan, I added this march 29 8:40 pm  - Jacob
        try:
            course_title, description = loader.get_name_and_description(self.code_clicked)
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
        self.course_info_box.update_information(selected_course_code, course_title,description,course_quality_score,assessment_score,workload_score,number_of_reviews)


if __name__ == '__main__':

    # JACOB SECTION
    loader = PrerequisiteTreeLoader()
    loader.load_from_file("prerequisite_tree_save_data.json")

    # ---------------------------------------------------------------------
    # LOAD CANVAS
    # ---------------------------------------------------------------------
    pygame.init()
    screen_width = 1440
    screen_height = 780
    size = (screen_width, screen_height)
    screen = pygame.display.set_mode(size)
    font = pygame.font.Font("FjallaOne-Regular.ttf", 12)

    # for window visual look
    pygame.display.set_caption("U of T Course Compass")
    icon = pygame.image.load("course_compass_logo.png")
    pygame.display.set_icon(icon)
    # ---------------------------------------------------------------------
    # Variables
    # ---------------------------------------------------------------------
    DEV_MODE = False
    CURSOR_SIZE = 2  # tiny square
    CURSOR_COLOR = (255, 0, 0)  # white

    # tree_visualizer_page = pygame.image.load(
    #     "course_compass_main_v6.png")
    # tree_visualizer_page = pygame.transform.smoothscale(tree_visualizer_page, (1440, 780))

    start_page = pygame.image.load(
        "course_compass_startup_screen_v2.png")
    start_page = pygame.transform.smoothscale(start_page, (1440, 780))

    course_selection_page = pygame.image.load(
        "course_compass_course_selection_v3.png")
    course_selection_page = pygame.transform.smoothscale(course_selection_page, (1440, 780))

    dev_mode_event = 0  # TODO:delete before final submission

    screen_mode = "main"

    #main_screen_ui = UIManager()
    main_screen_ui = MainScreenUI()

    # visualizer_search_field = TextField("Search Course", 30,(98, 29), (418, 73))
    # info_box = VisualizerInfoBox(5,25)
    # summer_offering_button = Button(
    #     (272, 731),
    #     (424, 752),
    #     lambda: show_summer_offerings(visualizer_search_field.input_text)
    # )
    # pre_req_button = Button(
    #     (79, 184),
    #     (214, 224),
    #     set_prereq_tree
    # )
    # post_req_button = Button(
    #     (245, 183),
    #     (400, 221),
    #     set_postreq_tree
    # )
    # simplify_tree_button = Button((285,237),(308,259), set_simplified_tree)
    #
    # generate_tree_button = Button(
    #     (164,276),
    #     (314,294),
    #     lambda: generate_tree(loader)
    # )
    #
    # main_screen_text_displayer = TextDisplayer("", 100, 500)
    # # main_screen_ui.add(visualizer_search_field)
    # # main_screen_ui.add(info_box)
    # # main_screen_ui.add(summer_offering_button)
    # main_screen_ui.add(main_screen_text_displayer)
    # main_screen_ui.add(post_req_button)
    # main_screen_ui.add(pre_req_button)
    # main_screen_ui.add(simplify_tree_button)
    # main_screen_ui.add(generate_tree_button)

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

    course_tree_type_slider_image = [course_tree_type_slider1,course_tree_type_slider2]

    selection_check_mark = pygame.image.load(
        "check_mark.png")
    selection_check_mark = pygame.transform.smoothscale(selection_check_mark, (41, 33))

    #tree_camera = TreeCamera(info_box)
    app_state = AppState()

    start_button = Button((406, 693), (1033, 754), switch_to_course_select)
    start_screen_ui = UIManager()
    start_screen_ui.add(start_button)

    course_manager = CourseManager()
    taken_course_field = TextField("Course Code", 20,(492, 208), (610, 230))
    grade_mark_field = TextField("###", 20, (704, 203), (740, 237))
    add_course_button = Button((801, 167), (971, 260), lambda: add_course_to_list(course_manager, taken_course_field.input_text, grade_mark_field.input_text))
    course_selection_ui = UIManager()
    course_selection_ui.add(taken_course_field)
    course_selection_ui.add(grade_mark_field)
    course_selection_ui.add(add_course_button)


    # ---------------------------------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------------------------------
    done = False
    while not done:
        for event in pygame.event.get():
            # uncomment below for dev mode
            dev_mode_event = event
            if event.type == pygame.QUIT:
                done = True
            if screen_mode == "start_screen":
                start_screen_ui.handle_event(event)
            elif screen_mode == "course_selection":
                course_selection_ui.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                    screen_mode = "main" #TODO: REMOVE - TEMP
            elif screen_mode == "main":
                #main_screen_ui.tree_camera.handle_interaction(event) #TODO:redundent
                main_screen_ui.handle_event(event)
                # TEMPORARLY uses enter key to take input from search bar, eventually this will be a button
                # TODO: error check input
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        pass

        if screen_mode == "start_screen":
            screen.blit(start_page, (0, 0))
        elif screen_mode == "course_selection":
            screen.blit(course_selection_page, (0, 0))
            course_selection_ui.update_visually(screen)
            #delete below:
            taken_course_field.show_outline_for_debugging(screen)
            grade_mark_field.show_outline_for_debugging(screen)
            add_course_button.show_outline_for_debugging(screen)
            add_course_button.show_outline_for_debugging(screen)
            course_list = course_manager.get_courses()
            for i in range(len(course_list)):
                course_with_mark = course_list[i]
                course = course_with_mark[0]
                grade = course_with_mark[1]

                text = font.render(f"{course}: {grade}", True, (35, 68, 119))

                if i < 19:
                    x = 392
                    y = 409 + i * 18
                else:
                    x = 392 + 50
                    y = 409 + (i - 19) * 18

                screen.blit(text, (x, y))
        elif screen_mode == "main":
            screen.fill((255, 255, 255))

            main_screen_ui.update_visually(screen)

            main_screen_ui.visualizer_search_field.show_outline_for_debugging(screen)
            main_screen_ui.summer_offering_button.show_outline_for_debugging(screen)
            main_screen_ui.course_spectrum_generate_button.show_outline_for_debugging(screen)

            # if app_state.current_course_tree is not None:
            #     draw_tree_visualization(app_state.current_course_tree, (tree_camera.x_pos_tree,
            #                             tree_camera.y_pos_tree), 300, tree_camera.zoom_factor,
            #                             tree_camera.node_course_code_map)
            # screen.blit(tree_visualizer_page, (0, 0))

            # if app_state.current_tree_type == "prerequisite":
            #     screen.blit(course_tree_type_slider_image[0],(74,181))
            # else:
            #     screen.blit(course_tree_type_slider_image[1], (74, 181))

            if app_state.is_current_tree_simplified:
                screen.blit(selection_check_mark, (288,230))

            #
            #
            # main_screen_ui.update_visually(screen)
            # visualizer_search_field.show_outline_for_debugging(screen)
            # summer_offering_button.show_outline_for_debugging(screen)
            # # for button in info_box.buttons:
            #     button.draw_button_for_debugging(screen)
    # uncomment below for dev mode
        ui_dev_mode(screen, dev_mode_event)
        pygame.display.flip()
    pygame.quit()
