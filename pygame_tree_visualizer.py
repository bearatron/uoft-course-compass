# Tree class
from __future__ import annotations

from operator import add
from typing import Callable
import textwrap
import webbrowser
import link_of_course
import json
from pygame.examples.scroll import zoom_factor

from academic_calendar_reader import PrerequisiteTreeLoader, CourseNotFoundError
from dataclasses import dataclass
from typing import Any, Optional
import pygame
from course_tree import CourseTree

#TODO: make it so that when info pannel is open than the search doesnt work
# make all the new code more clean, ask for code practice feedback, add comments
# missing tpye anotations
# Bug with if i click ui, then the behind layer of course tree might also be clicked.
# clean out useless images from file
# make var private/public - basically good class practices
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# TREE VISUALIZATION HELPER FUNCTIONS
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
def draw_node(display_vals: tuple[str | None, str], x_pos: int, y_pos: int, screen_zoom_factor: int,
              node_course_code_map: list[tuple[pygame.Rect, str]]):
    """
    Draw a node on point (x_pos, y_pos) with text, display_val
    """

    # define rectangle size with respect to the screen_zoom_factor which scales the
    # rectangle based on how zoomed in or out the user is
    rect_width = int(200 * screen_zoom_factor)
    rect_height = int(50 * screen_zoom_factor)

    COURSE_CODE_INDEX = 0
    COURSE_MARK_INDEX = 1

    node = pygame.Rect(x_pos, y_pos, rect_width, rect_height)

    # adding node to a tuple list that maps node with course code (display_val)
    node_course_code_map.append((node, display_vals[COURSE_CODE_INDEX]))

    # Drawing rect to screen
    pygame.draw.rect(screen,
                     (161, 202, 246),
                     node,
                     border_radius=int(15 * screen_zoom_factor))

    # Creating the node text
    font_size = max(12, int(24 * screen_zoom_factor))
    node_font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
    text_to_display = display_vals[COURSE_CODE_INDEX] + " " + display_vals[COURSE_MARK_INDEX]
    text_img = node_font.render(text_to_display, True, [0, 0, 0])
    text_rect = text_img.get_rect()

    # displaying the node text
    text_rect.center = (x_pos + rect_width // 2, y_pos + rect_height // 2)  # setting the text to the center of the node
    screen.blit(text_img, text_rect)


def tree_width(tree: CourseTree) -> int:
    # returns width of tree (width of lowest layer of subtree)
    if tree.is_empty():
        return 0
    elif not tree.get_subtrees():
        return 1
    else:
        width_so_far = 0
        for subtree in tree.get_subtrees():
            width_so_far += tree_width(subtree)
        return width_so_far


def draw_tree_visualization(tree: CourseTree, x_pos: int, y_pos: int, spacing_factor: int, zoom_factor: int,
                            node_course_code_map: list[tuple[pygame.Rect, str]]):
    if tree.is_empty():
        return
    else:
        draw_node((tree.get_root(), tree.get_grade_requirement()), x_pos, y_pos, zoom_factor, node_course_code_map)
        total_spacing = tree_width(tree) * spacing_factor * zoom_factor
        start_x_pos = x_pos - total_spacing // 2  # center children under parent

        for subtree in tree.get_subtrees():
            # horizontally place child node
            subtree_width = tree_width(subtree) * spacing_factor * zoom_factor
            child_x = start_x_pos + subtree_width // 2  # place child node in center of its allocated space

            # draw line from parent to child node
            # TODO: magic nums: surface, color, start pos, end pos, width
            pygame.draw.line(
                screen, (0, 0, 0),
                (x_pos + int(100 * zoom_factor), y_pos + int(50 * zoom_factor)),
                (child_x + int(100 * zoom_factor), y_pos + int(150 * zoom_factor)),
                max(1, int(4 * zoom_factor))
            )

            draw_tree_visualization(subtree, child_x, y_pos + int(150 * zoom_factor), spacing_factor, zoom_factor,
                                    node_course_code_map)

            start_x_pos += subtree_width


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# UI Classes
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# TODO: type annotations are not specified for some methods in this block, a contract in the form of an interface is
# needed to state what a ui item is i.e button/textfield
# TODO: specify the contents of collections ie dict in type anotations
#TODO: IS THIS GOOD CODE PRACTICE. add more attributes/complete ui element class
class UIElement:
    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        return  # default: do nothing

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        return  # default: do nothing

class UIManager:
    ui_components: list

    def __init__(self):
        self.ui_components = []

    def add(self, element):
        self.ui_components.append(element)

    def handle_event(self, ui_event):
        for item in self.ui_components:
            item.handle_interaction(ui_event)

    def update_visually(self, ui_screen):
        for e in self.ui_components:
            e.update_visually(ui_screen)

class CourseManager:
    courses: list[tuple[str, int]]
    def __init__(self):
        self.courses = []  # list of (course_code, grade)

    def add_course(self, code: str, grade: int):
        self.courses.append((code, grade))

    def get_courses(self):
        return self.courses

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
                if self.code_clicked is not None:

                    current_mouse_pos = pygame.mouse.get_pos()
                    displacement_x = current_mouse_pos[0] - self.initial_mouse_down_pos[0]
                    displacement_y = current_mouse_pos[1] - self.initial_mouse_down_pos[1]

                    if displacement_x < 2 and displacement_y < 2:
                        print(self.code_clicked)
                        self.course_info_box.is_enabled = True
                        self.update_info_box()
                    self.code_clicked = None

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


# TODO: can I use button class in text field
class Button(UIElement):
    top_left_cord: tuple
    bottom_right_cord: tuple
    is_pressed: bool
    rect: pygame.Rect
    on_click: Callable[[], None]  # TODO:i learned this today, ask group if okay

    def __init__(self, top_left_cord: tuple, bottom_right_cord: tuple, on_click: Callable[[], None]):
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
        self.images = [background_image,filled_star_image]
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
            ui_screen.blit(self.images[0], (self.x_pos, self.y_pos))
            self.buttons[0].rect.topleft = (self.x_pos+45, self.y_pos)
            font_text = pygame.font.Font("RobotoMono-VariableFont_wght.ttf", 12)
            font_heading = pygame.font.Font("FjallaOne-Regular.ttf", 25)
            font_text_styled =  pygame.font.Font("FjallaOne-Regular.ttf", 12)

            #visual elements of being open:
            #heading
            heading_x = self.x_pos + 40
            heading_y = self.y_pos + 60
            display_multiline_text("Heading", self.course_title,(heading_x, heading_y), font_heading, ui_screen)
            #body text
            text_x = self.x_pos + 40
            text_y = self.y_pos + 140
            display_multiline_text("Body", self.course_description,(text_x, text_y), font_text, ui_screen)
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
            ui_screen.blit(self.images[0], (self.x_pos, self.y_pos + 700))
            self.buttons[0].rect.topleft = (self.x_pos+45, self.y_pos + 700)


class SummerOfferingsText(UIElement):
    def __init__(self):
        pass

    def handle_interaction(self, ui_event: pygame.event.Event) -> None:
        pass

    def update_visually(self, ui_screen: pygame.Surface) -> None:
        pass

def score_visualizer(score: int, y_pos: int, star_image, ui_screen) -> None:
    if score <= 5:
        for i in range(score):
            ui_screen.blit(star_image, (261 + 36 * i, y_pos))
    #todo:raise error
def display_multiline_text(text_type: str, text: str, position: tuple[int, int], font: pygame.font.Font, ui_screen) -> None:
    #TODO: make considtion s.t. text type can only be body or heading
    if text_type == "Heading":
        max_lines = 2
        max_chars_per_line = 38
        color = (35,68,119)
    else:
        max_lines = 13
        max_chars_per_line = 55
        color = (0,0,0)
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

def show_summer_offerings(screen):
    with open("course_data_computed.json", "r") as file:
        data = json.load(file)

    font_text = pygame.font.Font("RobotoMono-VariableFont_wght.ttf", 12)

    display_multiline_text(
"paragraph",
   "This is some test text",
(531, 85),
        font_text,
        screen
    )

def ui_dev_mode(ui_screen, ui_event):
    # TODO:delete this before final submission
    pygame.mouse.set_visible(False)

    position = pygame.mouse.get_pos()
    x = position[0]
    y = position[1]

    cursor_size = 3
    pygame.draw.rect(screen, (255, 0, 0), (x, y, cursor_size, cursor_size))

    if ui_event.type == pygame.MOUSEBUTTONDOWN:
        print(x, y)

if __name__ == '__main__':

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
    DEV_MODE = True
    CURSOR_SIZE = 2  # tiny square
    CURSOR_COLOR = (255, 0, 0)  # white

    tree_visualizer_page = pygame.image.load(
        "course_compass_main_ui_v4.png")
    tree_visualizer_page = pygame.transform.smoothscale(tree_visualizer_page, (1440, 780))

    start_page = pygame.image.load(
        "course_compass_startup_screen_v2.png")
    start_page = pygame.transform.smoothscale(start_page, (1440, 780))

    course_selection_page = pygame.image.load(
        "course_compass_course_selection_v3.png")
    course_selection_page = pygame.transform.smoothscale(course_selection_page, (1440, 780))
    # For Shayan's Use Later
    # image2 = pygame.image.load("course_compass_course_selection_page.png")
    # image2 = pygame.transform.smoothscale(image2, (1440, 780))

    dev_mode_event = 0  # TODO:delete before final submission

    screen_mode = "course_selection"

    main_screen_ui = UIManager()
    visualizer_search_field = TextField("Search Course", 30,(98, 29), (418, 73))
    info_box = VisualizerInfoBox(5,25)
    summer_offering_button = Button(
        (272, 731),
        (424, 752),
        lambda: show_summer_offerings(screen),
    )

    main_screen_ui.add(visualizer_search_field)
    main_screen_ui.add(info_box)
    main_screen_ui.add(summer_offering_button)

    tree_camera = TreeCamera(info_box)
    course_tree = None

    programs = ["Computer Science", "Mathematics"]
    loader = PrerequisiteTreeLoader()
    loader.load_from_file("prerequisite_tree_save_data.json")

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
            elif screen_mode == "main":
                tree_camera.handle_interaction(event)
                main_screen_ui.handle_event(event)
                # TEMPORARLY uses enter key to take input from search bar, eventually this will be a button
                # TODO: error check input
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        course_code = visualizer_search_field.input_text
                        course_tree = loader.get_prerequisite_tree(course_code)
                        tree_camera.reset_camera()
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
            font = pygame.font.Font("FjallaOne-Regular.ttf", 12)
            text = font.render("Hello world", True, (0,0,0))


            screen.fill((255, 255, 255))
            if course_tree is not None:
                draw_tree_visualization(course_tree, tree_camera.x_pos_tree,
                                        tree_camera.y_pos_tree, 300, tree_camera.zoom_factor,
                                        tree_camera.node_course_code_map)
            screen.blit(tree_visualizer_page, (0, 0))
            screen.blit(text, (100, 100))


            main_screen_ui.update_visually(screen)
            visualizer_search_field.show_outline_for_debugging(screen)
            summer_offering_button.show_outline_for_debugging(screen)
            # for button in info_box.buttons:
            #     button.draw_button_for_debugging(screen)
        # uncomment below for dev mode
        ui_dev_mode(screen, dev_mode_event)
        pygame.display.flip()
    pygame.quit()
