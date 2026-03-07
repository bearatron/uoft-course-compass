"""main"""

from academic_calendar_reader import AcademicCalendarReader
from course_tree import CourseTree
from string_methods import *

if __name__ == "__main__":
    programs = ["Computer Science", "Physics", "Mathematics"]
    prerequisite_strings: dict[str, str] = {}
    prerequisite_trees: dict[str, CourseTree] = {}
    for program in programs:
        prerequisite_strings.update(AcademicCalendarReader.load_course_prerequisites(program))
        prerequisite_trees.update(AcademicCalendarReader.convert_to_tree(prerequisite_strings))

    ####################################################
    #                GENERATE MEGA TREE                #
    ####################################################
    # Ok so since these are all mutable objects, all we should have to do is go through each one and add other courses
    for course_code in prerequisite_trees:
        course_tree = prerequisite_trees[course_code]
        leaves = course_tree.get_course_leaves()
        for leaf in leaves:
            if leaf.get_root() in prerequisite_trees:
                leaf.set_subtrees(prerequisite_trees[leaf.get_root()].get_subtrees())

    running = True
    while running:
        course = input("Please enter a course code: ")
        if course in prerequisite_trees:
            print(prerequisite_trees[course].__str__())
        elif course.lower() in {"q", "quit", "exit"}:
            running = False
        else:
            print("Sorry, that isn't a valid course")
        print()
