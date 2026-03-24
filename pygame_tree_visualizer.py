#Tree class
from __future__ import annotations

from pygame.examples.scroll import zoom_factor

from academic_calendar_reader import PrerequisiteTreeLoader
from dataclasses import dataclass
from typing import Any, Optional
import pygame
from course_tree import CourseTree
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# TREE VISUALIZATION HELPER FUNCTIONS
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
def draw_node(display_val:str,x_pos:int, y_pos:int, zoom_factor:int):
    #rect Size Configurations
    rect_width = int(200*zoom_factor)
    rect_height = int(50*zoom_factor)

    #Drawing rect to screen
    pygame.draw.rect(screen,
                     (161, 202, 246),
                     [x_pos, y_pos, rect_width, rect_height],
                     border_radius= int(15*zoom_factor))

    #Making and drawing text to screen
    font_size = max(12, int(24 * zoom_factor))
    node_font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
    text_img = node_font.render(display_val, True, [0,0,0])
    text_rect = text_img.get_rect()
    text_rect.center = (x_pos + rect_width // 2, y_pos + rect_height // 2)
    screen.blit(text_img, text_rect)

def tree_width(tree: CourseTree) -> int:
    #returns width of tree (width of lowest layer of subtree)
    if tree.is_empty():
        return 0
    elif not tree.get_subtrees():
        return 1
    else:
        width_so_far = 0
        for subtree in tree.get_subtrees():
            width_so_far += tree_width(subtree)
        return width_so_far

def draw_tree_visualization(tree: CourseTree, x_pos: int, y_pos:int, spacing_factor: int, zoom_factor: int):
    if tree.is_empty():
        return
    else:
        draw_node(tree.get_root(), x_pos, y_pos, zoom_factor)
        total_spacing = tree_width(tree) * spacing_factor * zoom_factor
        start_x_pos = x_pos - total_spacing // 2 # center children under parent

        for subtree in tree.get_subtrees():
            #horizontally place child node
            subtree_width = tree_width(subtree) * spacing_factor * zoom_factor
            child_x = start_x_pos + subtree_width // 2 #place child node in center of its allocated space

            #draw line from parent to child node
            #TODO: magic nums: surface, color, start pos, end pos, width
            pygame.draw.line(
                screen, (0, 0, 0),
                (x_pos + int(100 * zoom_factor), y_pos + int(50 * zoom_factor)),
                (child_x + int(100 * zoom_factor), y_pos + int(150 * zoom_factor)),
                max(1, int(4 * zoom_factor))
            )

            draw_tree_visualization(subtree, child_x, y_pos + int(150*zoom_factor), spacing_factor, zoom_factor)

            start_x_pos += subtree_width

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# UI Classes
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
#TODO: type annotations are not specified for some methods in this block, a contract in the form of an interface is
# needed to state what a ui item is i.e button/textfield
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

class TextField:
    default_text: str
    input_text: str
    top_left_cord: tuple
    bottom_right_cord: tuple
    is_active: bool
    clear_default_value: bool
    rect: pygame.Rect


    def __init__(self, default_text: str, top_left_cord: tuple, bottom_right_cord: tuple) -> None:
        self.default_text = default_text
        self.top_left_cord = top_left_cord
        self.bottom_right_cord = bottom_right_cord

        self.is_active = False
        self.clear_default_value = False

        self.input_text = default_text
        #creating parameters of rect
        width = bottom_right_cord[0] - top_left_cord[0]
        height = bottom_right_cord[1] - top_left_cord[1]
        self.rect = pygame.Rect(top_left_cord[0],top_left_cord[1], width, height)
        #TODO: see if all vars here are needed - also can i do this much in innit?

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
        font_size = 30
        font = pygame.font.Font("FjallaOne-Regular.ttf", font_size)
        if self.is_active:
            color = (0,0,200)
        else:
            color = (0,0,0)
        text_surface = font.render(self.input_text, True, color)
        center_of_rect = self.rect.center
        justified_text_format = (self.top_left_cord[0],center_of_rect[1] - font_size//2)

        ui_screen.blit(text_surface, justified_text_format)

    def show_outline_for_debugging(self, ui_screen) -> None:
        #show outline of field
        pygame.draw.rect(ui_screen, (255, 255, 255), self.rect, 2)

class TreeCamera:
    x_pos_tree: int
    y_pos_tree: int
    dragging: bool
    zoom_factor: float
    previous_mouse_pos: tuple

    def __init__(self) -> None:
        self.x_pos_tree = 838
        self.y_pos_tree = 100
        self.dragging = False
        self.zoom_factor = 1
        self.previous_mouse_pos = (0, 0)

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
                self.previous_mouse_pos = pygame.mouse.get_pos()
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


def ui_dev_mode(ui_screen, ui_event):
    #TODO:delete this before final submission
    pygame.mouse.set_visible(False)

    position = pygame.mouse.get_pos()
    x = position[0]
    y = position[1]

    cursor_size = 3
    pygame.draw.rect(screen, (255, 0, 0), (x, y, cursor_size, cursor_size))

    if ui_event.type == pygame.MOUSEBUTTONDOWN:
        print(x,y)




if __name__ == '__main__':

    #---------------------------------------------------------------------
    #LOAD CANVAS
    # ---------------------------------------------------------------------
    pygame.init()
    screen_width = 1440
    screen_height = 780
    size = (screen_width, screen_height)
    screen = pygame.display.set_mode(size)
    #---------------------------------------------------------------------
    #Variables
    # ---------------------------------------------------------------------
    DEV_MODE = False
    CURSOR_SIZE = 2  # tiny square
    CURSOR_COLOR = (255, 0, 0)  # white

    tree_visualizer_page = pygame.image.load(
        "course_compass_main_UI_page.png")
    tree_visualizer_page = pygame.transform.smoothscale(tree_visualizer_page, (1440, 780))

    #For Shayan's Use Later
    #image2 = pygame.image.load("course_compass_course_selection_page.png")
    #image2 = pygame.transform.smoothscale(image2, (1440, 780))

    dev_mode_event = 0 #TODO:delete before final submission

    screen_mode = "main"
    tree_camera = TreeCamera()
    main_screen_ui = UIManager()

    visualizer_search_field = TextField("Search Course",(89,81),(427,132))
    main_screen_ui.add(visualizer_search_field)

    course_tree = None
    #---------------------------------------------------------------------
    #MAIN LOOP
    # ---------------------------------------------------------------------
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            tree_camera.handle_interaction(event)
            main_screen_ui.handle_event(event)
            #uncomment below for dev mode
            #dev_mode_event = event
            #TEMPORARLY uses enter key to take input from search bar, eventuall this will be a button
            #TODO: error check input
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    programs = ["Computer Science", "Mathematics"]
                    loader = PrerequisiteTreeLoader(programs)
                    course_code = visualizer_search_field.input_text
                    course_tree = loader.get_prerequisite_tree(course_code)

        if screen_mode == "main":
            screen.fill((255, 255, 255))
            if course_tree is not None:
                draw_tree_visualization(course_tree, tree_camera.x_pos_tree, tree_camera.y_pos_tree, 300, tree_camera.zoom_factor)
            screen.blit(tree_visualizer_page, (0, 0))
            # uncomment below for dev mode
            #ui_dev_mode(screen, dev_mode_event)
            main_screen_ui.update_visually(screen)

        pygame.display.flip()
    pygame.quit()
