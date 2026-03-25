from academic_calendar_reader import load_course_prerequisites
from string_methods import is_course_code
from course_tree import CourseTree


def load_course_postrequisites (program:str) -> dict[str, list[str]]:

    prerequisites_dictionary = load_course_prerequisites(program)
    post_req_dict = {course: [] for course in prerequisites_dictionary}

    for course in prerequisites_dictionary:
        if prerequisites_dictionary[course] == '':
            continue
        list_of_course = fix_given_courses(prerequisites_dictionary[course])
        for code in list_of_course:
            if code in post_req_dict:
                post_req_dict[code].append(course)
    return post_req_dict


def fix_given_courses(courses: str) -> list:
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
    """Recursively build a post-requisite tree up to the given depth"""
    if depth == 0 or course_code not in postrequisite_dict:
        return CourseTree(course_code, -1, [])

    subtrees = [_build_tree(post_req, postrequisite_dict, depth - 1) for post_req in postrequisite_dict[course_code]]
    return CourseTree(course_code, -1, subtrees)


class PostrequisiteTreeLoader:
    """Loads and stores post-requisite information for all courses in the given programs"""
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
    """Returns the all the item that is in the tree"""
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
    courses1 = all_items_in_tree(tree1)
    courses2 = all_items_in_tree(tree2)
    courses_exclusive_tree1, courses_exclusive_tree2 = courses1 - courses2, courses2 - courses1
    return f"Courses you can take if you took {tree1.get_root()} instead of {tree2.get_root()}: {courses_exclusive_tree1}"\
           f"Courses you can take if you took {tree2.get_root()} instead of {tree1.get_root()}: {courses_exclusive_tree2}"
