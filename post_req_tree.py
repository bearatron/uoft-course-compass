"""
Course tree computation methods

This module provides two useful methods. One finds all items in a tree, and
the other finds the similarities and differences between the two trees.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from course_tree import CourseTree


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
