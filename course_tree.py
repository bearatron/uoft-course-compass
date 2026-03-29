"""The definition of the Course Tree class, used to store prerequisite information for a course as a tree"""
from __future__ import annotations

from typing import Any, Optional

import string_methods


class CourseTree:
    """A recursive tree data structure for storing course prerequisites

    Representation Invariants:
       - self._root is not None or self._subtrees == []
       - all(not subtree.is_empty() for subtree in self._subtrees)
    """
    # Private Instance Attributes:
    #   - _required_grade:
    #       The required grade prerequisite for the course at the root, or '-1' if there is none
    #   - _root:
    #       The item stored at this tree's root, or None if the tree is empty.
    #       This item will either be a Course Code or '*'
    #   - _subtrees:
    #       The list of subtrees of this tree. This attribute is empty when
    #       self._root is None (representing an empty tree). However, this attribute
    #       may be empty when self._root is not None, which represents a tree consisting
    #       of just one item.
    _required_grade: int
    _root: Optional[Any]
    _subtrees: list[CourseTree]

    def __init__(self, root: Optional[Any], grade: int, subtrees: list[CourseTree]) -> None:
        """Initialize a new CourseTree with the given root value, grade, and subtrees.

        If root is None, the tree is empty.

        Preconditions:
            - root is not none or subtrees == []
            - -1 <= grade <= 100
        """
        self._root = root
        self._required_grade = grade
        self._subtrees = subtrees

    def is_leaf(self) -> bool:
        """Return whether the tree is a leaf"""
        return self._subtrees == []

    def get_subtrees(self) -> list[CourseTree]:
        """Return the list of subtrees of the Course Tree"""
        return self._subtrees

    def set_subtrees(self, subtrees: list[CourseTree]) -> None:
        """Set the subtrees attribute of the Course Tree to the provided subtrees"""
        self._subtrees = subtrees

    def get_root(self) -> Optional[str]:
        """Return the root of the Course Tree"""
        return self._root

    def get_grade_requirement(self) -> str:
        """Return the course code of the Course Tree with the grade requirement if applicable"""
        if self._required_grade == -1:
            return ""
        else:
            return f'({self._required_grade}%)'

    def get_course_leaves(self) -> list[CourseTree]:
        """Return all the leaves of the Course Tree"""
        leaves = []
        for subtree in self._subtrees:
            if subtree.is_leaf():
                leaves += [subtree]
            else:
                leaves += subtree.get_course_leaves()
        return leaves

    @staticmethod
    def generate_course_tree(prerequisites: str, course_code: str | None = None) -> CourseTree:
        """Generate and return a properly formatted Course Tree based on the provided prerequisites string with the
        given course_code as the root value.

        Preconditions:
            - prerequisites is a properly formatted prerequisite string (as described in the project report)
            - is_course_code(course_code)"""
        # Check if this is the top call and not a recursive call
        if course_code:
            # If there are no prerequisites, return an empty tree  # TODO: not an empty tree :)
            if prerequisites == '':
                return CourseTree(course_code, -1, [])
            # Otherwise, return a course tree generated based on the provided prerequisites string
            else:
                course_tree = CourseTree.generate_course_tree(prerequisites)
                return CourseTree(course_code, -1, [course_tree])
        else:
            if string_methods.is_graded_course_code(prerequisites):
                # BASE CASE: The prerequisites string is a single course code
                # We return a tree with 'prerequisites' as the root and no subtrees
                return CourseTree(prerequisites[0:8], int(prerequisites[9:11]), [])
            elif string_methods.has_unnested(prerequisites, ','):
                # The prerequisites string is composed of entries separated by commas: (...),(...)
                # This indicates that all the constituents are required
                # We return a tree whose root is 'ALL' and whose subtrees are the constituents
                constituents = string_methods.unnested_split(prerequisites, ',')
                return CourseTree(
                    'ALL', -1, [CourseTree.generate_course_tree(constituent) for constituent in constituents]
                )
            elif string_methods.has_unnested(prerequisites, '/'):
                # The prerequisites string is composed of entries separated by slashes: (...)/(...)
                # This indicates that one of the constituents is required
                # We return a tree whose root is 'CHOOSE' and whose subtrees are the constituents
                constituents = string_methods.unnested_split(prerequisites, '/')
                return CourseTree(
                    'CHOOSE', -1, [CourseTree.generate_course_tree(constituent) for constituent in constituents]
                )
            elif prerequisites[0] == '(' and prerequisites[-1] == ')':
                # The prerequisites string is entirely nested within redundant parentheses: (...)
                # We return the tree corresponding to what is within the parentheses
                return CourseTree.generate_course_tree(prerequisites[1:-1])

        # This code should be inaccessible unless something went very wrong.
        # This line is needed to appease PythonTA, we return an empty course tree
        return CourseTree(course_code, -1, [])

    def is_empty(self) -> bool:
        """Return whether this tree is empty.
        """
        return self._root is None

    def __str__(self) -> str:
        """Return a string representation of this tree.

        For each node, its item is printed before any of its
        descendants' items. the output is nicely indented.
        """
        return self._str_indented(0)

    def _str_indented(self, depth: int) -> str:
        """Return an indented string representation of this tree.

        The indentation level is specified by the <depth> parameter.
        """
        if self.is_empty():
            return ''
        else:
            if self._required_grade != -1:
                grade_string = f'({self._required_grade}%)'
            else:
                grade_string = ''
            str_so_far = '  ' * depth + f'{self._root} {grade_string}\n'
            for subtree in self._subtrees:
                str_so_far += subtree._str_indented(depth + 1)
            return str_so_far

    def _course_completed(self, courses_taken: dict[str, int]) -> bool:
        """Docstring"""
        for course in courses_taken:
            grade = courses_taken[course]
            if course == self._root and grade >= self._required_grade:
                return True

        return False

    def _remove_empty_subtrees(self) -> None:
        """Docstring"""
        for i in range(len(self._subtrees) - 1, -1, -1):
            if self._subtrees[i].is_empty():
                self._subtrees.pop(i)

    def simplify_tree(self, courses_taken: dict[str, int]) -> CourseTree:
        """Docstring"""
        # Simplify subtrees
        for i in range(len(self._subtrees)):
            self._subtrees[i] = self._subtrees[i].simplify_tree(courses_taken)

        if self._root == 'ALL':
            # If all subtrees are empty, return an emptry tree
            if all(subtree.is_empty() for subtree in self._subtrees):
                return CourseTree(None, -1, [])
            # Otherwise, return the current tree with empty subtrees removed
            # Also, we simplify the tree if it only has one subtree
            else:
                self._remove_empty_subtrees()
                if len(self._subtrees) == 1:
                    return self._subtrees[0]
                return self

        elif self._root == 'CHOOSE':
            # If one of the subtrees is empty, return an empty tree
            if any(subtree.is_empty() for subtree in self._subtrees):
                return CourseTree(None, -1, [])
            # Otherwise, return the current tree
            # Also, we simplify the tree if it only has one subtree
            else:
                if len(self._subtrees) == 1:
                    return self._subtrees[0]
                return self

        else:  # self._root is a course
            # If the course at the root has been completed, return an empty tree
            if self._course_completed(courses_taken):
                return CourseTree(None, -1, [])
            # Otherwise, return the current tree with empty subtrees removed
            else:
                self._remove_empty_subtrees()
                return self

    def copy(self) -> CourseTree:
        """Dosctring"""
        copied_tree = CourseTree(self._root, self._required_grade, [subtree.copy() for subtree in self._subtrees])
        return copied_tree


if __name__ == '__main__':
    pass
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'extra-imports': ['string_methods'],
    #     'disable': ['static_type_checker'],
    # })
