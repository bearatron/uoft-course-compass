"""Course management and main user interface module.

This module handles the core state and user interactions for the application's
main screen. It provides the `CourseManager` to track student course history,
along with UI components (`UIManager`, `Slider`, and `MainScreenUI`) that manage
event handling, visual updates, and the generation of course prerequisite trees.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from __future__ import annotations
import pygame
from dataclasses import dataclass
import json

from ui_element import UIElement, Button, TreeController, VisualizerInfoBox, TextField, TextDisplayer, Tree, Checkbox, \
    CourseDifference
from course_tree import CourseTree
from academic_calendar_reader import PrerequisiteTreeLoader, CourseNotFoundError

from optimal_path_to_course import optimal_path_to_course
from post_req_tree import course_difference_tree


class CourseManager:
    """
    A class responsible for storing courses the user has taken and the grades earned.

    Instance Attributes:
        - courses: a dictionary mapping course codes to the user's grade in that course
    """
    courses: dict[str, int]

    def __init__(self) -> None:
        """Initialize a new CourseManager object with no stored courses."""
        self.courses = {}

    def add_course(self, code: str, course_grade: int) -> None:
        """
        Add a course and its respective grade to the manager.
        If the course already exists, its grade is overwritten.
        Preconditions:
            - code != ""
            - 0 <= course_grade <= 100
        """
        self.courses[code] = course_grade

    def get_courses(self) -> dict[str, int]:
        """
        Return the dictionary of stored courses and grades.
        """
        return self.courses


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


class UIManager:
    """
    A class responsible for managing a collection of UI elements.
    The class stores UI elements and provides methods to pass
    events and drawing updates to each component.

    Instance Attributes:
        - ui_components: a list of UIElement or other UIManager objects managed by this UIManager
    """
    ui_components: list[UIElement | UIManager]

    def __init__(self) -> None:
        """Initialize a new UI Manager object"""
        self.ui_components = []

    def add(self, element: UIElement | UIManager) -> None:
        """Add a UI element to the manager"""
        self.ui_components.append(element)

    def handle_event(self, ui_event: pygame.event.Event) -> None:
        """Pass a pygame event to every managed UI element"""
        for item in self.ui_components:
            item.handle_interaction(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """visually update appearance of every managed UI element."""
        for item in self.ui_components:
            item.update_visually(ui_screen)


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
    #   - slider_size: a tuple representing the width and height of the entire slider
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
        option_filepaths is a list of paths to the slider button images
        option_coords is a list of top left and bottom right coordinates of the slider option buttons
        slider_size is the size of the entire slider image

        The rest of the class's attributes are computed based on the above values
        """
        super().__init__()
        self.option_filepaths = option_filepaths
        self.option_coords = option_coords

        # number of options should be the same as the number of option images that are stored
        self.num_options = len(self.option_filepaths)
        self.slider_size = slider_size

        # the first element is selected by default
        self.curr_selection = 0

        # initialize accumulators
        self.option_surfaces = []  # pygame Surface objects for the slider buttons, are drawn to the screen
        self.option_buttons = []  # Button objects that correspond to the Surfaces that provide selection functionality

        # construct option surfaces and buttons from filepaths
        for option_id in range(self.num_options):
            # load image
            option_img = pygame.image.load(option_filepaths[option_id])

            # convert to surface
            option_surface = pygame.transform.smoothscale(option_img, slider_size)

            # accumulate
            self.option_surfaces.append(option_surface)

            # construct Button UIElement based on coords provided
            button_coords = self.option_coords[option_id]
            top_left, bottom_right = button_coords
            option_button = Button(
                top_left,
                bottom_right,
                # change selection to the corresponding option when button is clicked
                lambda option_id=option_id: self.change_selection(option_id)
            )

            # accumulate
            self.option_buttons.append(option_button)

    def change_selection(self, to_id: int) -> None:
        """
        Change the slider selection to id
        """
        self.curr_selection = to_id

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        """
        Check if any slider buttons have been clicked
        """
        for button in self.option_buttons:
            button.handle_interaction(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """
        Draw the slider image corresponding to the option currently selected
        """
        # get the pygame Surface of the currently selected slider option
        selected_option_surface = self.option_surfaces[self.curr_selection]

        # always draw slider option at same location because it's the same image, but in a different state
        coords = self.option_coords[0]  # top left coordinate of the slider

        # draw to screen
        ui_screen.blit(selected_option_surface, coords)


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
    #   - COURSE_DIFFERENCE_OUTPUT: an int representing the fact that the course difference tree is outputted
    #   - BG_PATH: a str representing the file path to the UI background
    TREE_OUTPUT = 0
    TEXT_OUTPUT = 1
    ERROR_OUTPUT = 2
    COURSE_DIFFERENCE_OUTPUT = 3
    BG_PATH = "course_compass_main_ui_v7.png"

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
    #   - optimal_path_slider: a Slider for selecting a metric
    #   - optimal_path_generate_button: a Button to generate a tree based on optimal_path_slider
    #   - course_tree_options: a dataclass to store whether a prereq or postreq tree should be displayed
    #   - course_tree_slider: a slider that allows the user to choose to display prereq or postreq tree
    #   - course_tree_generate_button: a button that generates the course tree
    #   - course_tree_simplify_checkbox: a Checkbox that stores whether
    #       to simplify the tree if it's a prereq tree
    #   - course_manager: a CourseManager that stores the courses taken, entered by the user
    #   - loader: a PrerequisiteTreeLoader that can load prerequisite CourseTrees

    panel_output_mode: int
    tree_type: int
    tree_camera: TreeController
    course_tree: CourseTree
    info_box: VisualizerInfoBox
    visualizer_search_field: TextField
    summer_offering_button: Button
    error_displayer: TextDisplayer
    text_displayer: TextDisplayer
    optimal_path_generate_button: Button
    optimal_path_slider: Slider
    course_tree_options: CourseTreeOptions
    course_tree_slider: Slider
    course_tree_generate_button: Button
    course_tree_simplify_checkbox: Checkbox
    course_difference_search_field: TextField
    course_difference_generate_button: Button
    course_difference_tree: CourseDifference
    course_manager: CourseManager
    loader: PrerequisiteTreeLoader

    # Private instance attributes:
    #   - _tree_ui_element: a Tree UI element storing the tree to be displayed
    #   - _background_surface: a pygame Surface object for the main screen background
    _tree_ui_element: Tree
    _background_surface: pygame.Surface

    def __init__(self, course_manager: CourseManager) -> None:
        """Initialize a new MainScreenUI object"""
        super().__init__()

        self.loader = PrerequisiteTreeLoader()
        self.loader.load_from_file("prerequisite_tree_save_data.json")

        self.course_manager = course_manager

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
        self.ui_components.append(self.visualizer_search_field)

        #####################################
        # Summer Offerings related elements #
        #####################################

        # create summer offerings button
        self.summer_offering_button = Button(
            (272, 575),
            (424, 600),
            # when clicked, display info about summer course offerings as text on the panel
            lambda main_screen_ui=self:
                show_summer_offerings(self.visualizer_search_field.get_input_text(), main_screen_ui),
        )
        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.summer_offering_button)

        ###########################################
        # Course Difference Tree related elements #
        ###########################################
        # create the field to enter the course the user can compare to
        self.course_difference_search_field = TextField(
            "Course to compare to",
            18,
            (260, 690),
            (430, 717)
        )
        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.course_difference_search_field)

        # create the button for showing similarities and differences between courses
        self.course_difference_generate_button = Button(
            (272, 725),
            (424, 747),
            # display course similarities and differences to the panel
            lambda main_screen_ui=self: generate_course_difference_tree(
                self.visualizer_search_field.get_input_text(),
                self.course_difference_search_field.get_input_text(),
                self.course_difference_tree, self.loader, main_screen_ui
            )
        )
        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.course_difference_generate_button)

        # create course difference tree object (will be displayed on the panel)
        self.course_difference_tree = CourseDifference(self.info_box, self.loader)
        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.course_difference_tree)

        ################################
        # Course Tree related elements #
        ################################
        # slider object for course tree
        self.course_tree_slider = Slider(
            ["pre_post_req_slider1.png", "pre_post_req_slider2.png"],
            [
                ((75, 180), (240, 225)),
                ((240, 180), (400, 225))
            ],
            (330, 47)
        )
        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.course_tree_slider)

        # construct the tree ui element from a TreeController and CourseTree
        top_left_coord = (480, 30)
        bottom_right_coord = (1400, 750)

        self.tree_camera = TreeController(self.info_box, self.loader, top_left_coord, bottom_right_coord)
        # set course_tree to an empty tree as the default value
        self.course_tree = CourseTree(None, -1, [])
        self._tree_ui_element = Tree(self.tree_camera, self.course_tree)

        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self._tree_ui_element)

        # create the checkbox for selecting whether to simplify the course tree if it's a prereq tree
        self.course_tree_simplify_checkbox = Checkbox((288, 239), 23)

        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.course_tree_simplify_checkbox)

        # course tree "Generate" button
        # CourseTreeOptions contains a mapping from the prereq/postreq slider's selected id
        # to look up in course_data_computed.json
        self.course_tree_generate_button = Button(
            (165, 275),
            (315, 298),
            lambda course_manager=self.course_manager, loader=self.loader, main_screen_ui=self:
                generate_course_tree(
                    self.visualizer_search_field.get_input_text(),
                    self.course_tree_slider.curr_selection,
                    self.course_tree_simplify_checkbox.checked,
                    course_manager,
                    loader,
                    main_screen_ui
            )
        )

        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.course_tree_generate_button)

        #################################
        # Optimal path related elements #
        #################################

        # x boundaries of the course spectrum slider
        left_x = 45
        right_x = 430

        # y boundaries of the course spectrum slider
        top_y = 410
        bottom_y = 455

        # there are three elements: overall_satisfaction, workload, and cognitive_growth
        num_elements = 3

        # the width of each button in the slider
        width = (right_x - left_x) // num_elements

        # create a Slider object to select a metric
        self.optimal_path_slider = Slider(
            ["course_spec_slider1.png", "course_spec_slider2.png", "course_spec_slider3.png"],
            [
                ((left_x + 0 * width, top_y), (left_x + 1 * width, bottom_y)),
                ((left_x + 1 * width, top_y), (left_x + 2 * width, bottom_y)),
                ((left_x + 2 * width, top_y), (left_x + 3 * width, bottom_y)),
            ],
            (384, 47)
        )

        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.optimal_path_slider)

        # course spectrum "Generate" button
        # CourseSpectrumOptions contains a mapping from the metric slider's selected id to the metric name
        # to look up in course_data_computed.json
        self.optimal_path_generate_button = Button(
            (165, 478),
            (315, 500),
            lambda course_manager=self.course_manager, loader=self.loader, main_screen_ui=self: generate_optimal_tree(
                self.visualizer_search_field.get_input_text(),
                CourseSpectrumOptions.idx_to_metric[self.optimal_path_slider.curr_selection][0],
                CourseSpectrumOptions.idx_to_metric[self.optimal_path_slider.curr_selection][1],
                course_manager,
                loader,
                main_screen_ui
            )
        )

        # append to ui_components list for handle_event to work properly
        self.ui_components.append(self.optimal_path_generate_button)

    def get_tree_ui_element(self) -> Tree:
        """Get the private tree UI element attribute"""
        return self._tree_ui_element

    def handle_event(self, ui_event: pygame.event.Event) -> None:
        """Handles a UI event"""
        # the default implementation is to call handle_interaction on all elements in the ui_components list
        super().handle_event(ui_event)

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        """Update the screen based on the panel output mode"""
        # update UI elements that depend on panel output mode
        if self.panel_output_mode == MainScreenUI.TREE_OUTPUT:
            self._tree_ui_element.update_visually(ui_screen)
        elif self.panel_output_mode == MainScreenUI.TEXT_OUTPUT:
            self.text_displayer.update_visually(ui_screen)
        elif self.panel_output_mode == MainScreenUI.ERROR_OUTPUT:
            self.error_displayer.update_visually(ui_screen)
        elif self.panel_output_mode == MainScreenUI.COURSE_DIFFERENCE_OUTPUT:
            self.course_difference_tree.update_visually(ui_screen)
        else:
            print("!!! No valid screen panel output mode was set !!!")

        ui_screen.blit(self._background_surface, (0, 0))

        # draw buttons to screen

        self.visualizer_search_field.update_visually(ui_screen)

        self.course_tree_slider.update_visually(ui_screen)

        self.course_tree_simplify_checkbox.update_visually(ui_screen)

        self.course_difference_search_field.update_visually(ui_screen)

        self.course_difference_generate_button.update_visually(ui_screen)

        self.optimal_path_slider.update_visually(ui_screen)

        # draw the info panel last, as it should be displayed on top of everything
        if self.panel_output_mode == MainScreenUI.TREE_OUTPUT:
            self.info_box.update_visually(ui_screen)


def show_summer_offerings(course: str, main_screen_ui: MainScreenUI) -> None:
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
        print(f"[ERROR] Could not find '{course}' in course_data_computed.json")
        main_screen_ui.error_displayer.display_text = f"Could not find summer course data for '{course}'"
        main_screen_ui.panel_output_mode = MainScreenUI.ERROR_OUTPUT
    else:
        total_years_offered = data[course]["num_years_offered"]
        summer_years_offered = summer_offerings_data["num_years_offered"]
        most_recent_year = summer_offerings_data["most_recent_year"]

        # combine data into an informative string
        if most_recent_year == 0:
            # the course was offered 0 times, so it doesn't have a most recently offered year
            summer_info_text = (f"{course} has been offered in the summer {summer_years_offered} times in its "
                                f"{total_years_offered} year history.")
        else:
            summer_info_text = (f"{course} has been offered in the summer {summer_years_offered} times in its "
                                f"{total_years_offered} year history, most recently in {most_recent_year}.")

        # display on main screen
        main_screen_ui.text_displayer.display_text = summer_info_text
        main_screen_ui.panel_output_mode = MainScreenUI.TEXT_OUTPUT


def generate_optimal_tree(course: str, metric: str, higher_is_better: bool, course_manager: CourseManager,
                          loader: PrerequisiteTreeLoader, main_screen_ui: MainScreenUI) -> None:
    """
    Display a tree to the main screen representing the optimal courses to take (defined by metric)
     in order to reach course
    Display an empty tree if course has been taken before

    Remove courses that the user has already taken (accessed through course_manager.get_courses())
    """
    try:
        # check if the course is a valid course code by attempting to load its prerequisite tree
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
        # get the courses user has taken
        courses_taken = course_manager.get_courses()

        # get the CourseTree representation of the optimal tree
        optimal_tree = optimal_path_to_course(
            loader,
            course,
            courses_taken,
            metric,
            higher_is_better
        )

        # display the optimal course tree on the main screen
        main_screen_ui.course_tree = optimal_tree
        main_screen_ui.get_tree_ui_element().course_tree = optimal_tree
        main_screen_ui.tree_camera.reset_camera()
        main_screen_ui.panel_output_mode = MainScreenUI.TREE_OUTPUT


def generate_course_tree(course_code: str, tree_type: int, simplified: bool, course_manager: CourseManager,
                         loader: PrerequisiteTreeLoader, main_screen_ui: MainScreenUI) -> None:
    """
    Generate a course tree given a course code and tree type

    simplified dictates whether the tree is simplified
    We do not simplify the course tree if it's a postrequisite tree

    Preconditions:
        - tree_type in {CourseTreeOptions.PREREQ, CourseTreeOptions.POSTREQ}
    """
    courses_taken = course_manager.get_courses()

    try:
        if tree_type == CourseTreeOptions.PREREQ:
            # get prereq tree
            prereq_tree = loader.get_prerequisite_tree(course_code)

            # simplify the tree if needed
            if simplified:
                prereq_tree = prereq_tree.get_simplified_tree(courses_taken)

            # display the tree to the main screen
            main_screen_ui.course_tree = prereq_tree
            main_screen_ui.get_tree_ui_element().course_tree = prereq_tree

        else:
            # tree type is a postreq tree
            # we do not simplify the course tree if it's a postrequisite tree
            postreq_tree = loader.get_postrequisite_tree(course_code)

            # display the tree to the main screen
            main_screen_ui.course_tree = postreq_tree
            main_screen_ui.get_tree_ui_element().course_tree = postreq_tree
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


def generate_course_difference_tree(original_course: str,
                                    course_to_compare: str,
                                    course_difference: CourseDifference,
                                    loader: PrerequisiteTreeLoader,
                                    main_screen_ui: MainScreenUI) -> None:
    """
    Display three columns of course nodes to the main screen.

    From left to right, the columns contain:
        1. The postreq courses exclusive to original_course
        2. The postreq courses shared by original and course_to_compare
        3. The postreq courses exclusive to course_to_compare
    """
    try:
        # postreq tree for original_course
        tree1 = loader.get_postrequisite_tree(original_course)
    except CourseNotFoundError:
        # handle errors by setting the error display text
        if original_course == "":
            main_screen_ui.error_displayer.display_text = "Please enter a non-empty course code"
        else:
            main_screen_ui.error_displayer.display_text = \
                f"The course '{original_course}' is invalid or doesn't exist"

        # change panel output mode to error output
        main_screen_ui.panel_output_mode = MainScreenUI.ERROR_OUTPUT
        return

    try:
        # postreq tree for course_to_compare
        tree2 = loader.get_postrequisite_tree(course_to_compare)
    except CourseNotFoundError:
        # handle errors by setting the error display text
        if original_course == "":
            main_screen_ui.error_displayer.display_text = "Please enter a non-empty course code to compare to"
        else:
            main_screen_ui.error_displayer.display_text = \
                f"The course '{original_course}' you are trying to compare with is invalid or doesn't exist"

        # change panel output mode to error output
        main_screen_ui.panel_output_mode = MainScreenUI.ERROR_OUTPUT
        return

    # get the sets of similar and different courses
    similar_courses, tree1_exclusive, tree2_exclusive = course_difference_tree(tree1, tree2).values()

    # pass them to the course difference tree to display
    course_difference.course1_to_compare = original_course
    course_difference.course2_to_compare = course_to_compare
    course_difference.same_to_both = similar_courses
    course_difference.course1_exclusive = tree1_exclusive
    course_difference.course2_exclusive = tree2_exclusive

    # set panel output mode to course difference output
    # this signals that the main screen ui should display course differences
    main_screen_ui.course_difference_tree.reset_camera()
    main_screen_ui.panel_output_mode = MainScreenUI.COURSE_DIFFERENCE_OUTPUT


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
