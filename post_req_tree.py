"""This file is used to create a tree of all the post-requisites and all post requisit tree related function"""
from academic_calendar_reader import PrerequisiteTreeLoader
from academic_calendar_reader import load_course_information
from string_methods import is_course_code
from course_tree import CourseTree


# TODO: ...
def load_course_postrequisites(program: str) -> dict[str, list[str]]:
    """
    This function takes in a program and return a dictionary with each course corresponding to its post
    requisite courses
    """

    # takes in a dictionary with course linked to its prerequisite (as string)
    prerequisites_dictionary = load_course_information(program)[0]
    # creates a dictionary with all courses link to empty list
    post_req_dict = {course: [] for course in prerequisites_dictionary}

    # swap the places of dictionary key and it's value (Note: this only works bc all courses are in dictionary)
    for course in prerequisites_dictionary:
        if prerequisites_dictionary[course] == '':  # ignores keys with no value tied
            continue
        list_of_course = fix_given_courses(prerequisites_dictionary[course])
        # adds all the "code" that are post req of the course into that dictionary.
        for code in list_of_course:
            if code in post_req_dict:
                post_req_dict[code].append(course)
    return post_req_dict

def fix_given_courses(courses: str) -> list:
    """clean the string and return a list of all the valid courses in the string"""
    codes = []
    i = 0
    while i < len(courses):
        chunk = courses[i:i + 8]
        if is_course_code(chunk):
            codes.append(chunk)
            i += 8
        else:
            i += 1
    return codes

def _build_tree(course_code: str, postrequisite_dict: dict[str, list[str]], depth: int) -> CourseTree:
    """Helper function! (not to use). Recursively build a post-requisite tree up to the given depth"""
    # Base Case
    if depth == 0 or course_code not in postrequisite_dict:
        return CourseTree(course_code, -1, [])

    # subtree for each of the course
    subtrees = [_build_tree(post_req, postrequisite_dict, depth - 1) for post_req in postrequisite_dict[course_code]]
    return CourseTree(course_code, -1, subtrees)


class PostrequisiteTreeLoader:
    """Loads and stores post-requisite information for all courses in the given programs
        _postrequisite_dict: dictionary that contains course string linked to list of course
                            string one can take after completing the course
        root_course: The course in question

    """
    _postrequisite_dict: dict[str, list[str]]
    root_course: str

    def __init__(self, programs: list[str], root_course: str):
        self._postrequisite_dict = {}

        for program in programs:
            self._postrequisite_dict.update(load_course_postrequisites(program))

        self.root_course = root_course

    def get_postrequisite_tree(self, depth: int) -> CourseTree:
        """Return the post-requisite tree for the given course code up to the given depth"""
        return _build_tree(self.root_course, self._postrequisite_dict, depth)


def all_items_in_tree(tree: CourseTree) -> set:
    """Returns all the items that is in the tree"""
    # use recursion to save in set, and return
    if tree.is_empty():
        return set()
    elif tree.is_leaf():
        return {tree.get_root()}
    else:
        result = {tree.get_root()}
        for subtree in tree.get_subtrees():
            result.update(all_items_in_tree(subtree))
        return result


def course_difference_tree(tree1: CourseTree, tree2: CourseTree):
    """Return two sets: courses in tree1 but not tree2, and courses in tree2 but not tree1"""
    courses1 = all_items_in_tree(tree1)  # saves all courses in tree1 as a set
    courses2 = all_items_in_tree(tree2)  # saves all courses in tree2 as a set
    # find and save the courses that are exclusive to tree1 and tree2, saved them respectively
    courses_exclusive_tree1, courses_exclusive_tree2 = courses1 - courses2, courses2 - courses1
    return {"course for both": courses1 | courses2, f"course exclusive for {tree1.get_root()}" : courses_exclusive_tree1,
            f"course exclusive for {tree2.get_root()}": courses_exclusive_tree2}


# def get_direct_postrequisites(course_code: str, save_file: str) -> CourseTree:
#     loader = PrerequisiteTreeLoader()
#     loader.load_from_file(save_file)
#     course_tree = loader.get_prerequisite_tree
