"""Course Tree
(some methods borrowed and slightly modified from CSC111 tree class)"""
from __future__ import annotations

from typing import Any, Optional

from string_methods import *


class CourseTree:
    """A recursive tree data structure for storing course prerequisites

    Representation Invariants:
       - self._root is not None or self._subtrees == []
       - all(not subtree.is_empty() for subtree in self._subtrees)
    """
    # Private Instance Attributes:
    #   - _root:
    #       The item stored at this tree's root, or None if the tree is empty.
    #       This item will either be a course code or a '*' character
    #   - _subtrees:
    #       The list of subtrees of this tree. This attribute is empty when
    #       self._root is None (representing an empty tree). However, this attribute
    #       may be empty when self._root is not None, which represents a tree consisting
    #       of just one item.
    _root: Optional[Any]
    _required_grade: int  # TODO: private instance attributes
    _subtrees: list[CourseTree]

    def __init__(self, root: Optional[Any], grade: int, subtrees: list[CourseTree]) -> None:
        """Initialize a new CourseTree with the given root value and subtrees.

        If root is None, the tree is empty.

        Preconditions:
            - root is not none or subtrees == []
        """
        self._root = root
        self._required_grade = grade
        self._subtrees = subtrees

    def is_leaf(self) -> bool:
        """docstring"""
        return self._subtrees == []

    def get_subtrees(self) -> list[CourseTree]:
        """f"""
        return self._subtrees

    def set_subtrees(self, subtrees: list[CourseTree]) -> None:
        """slkdjf"""
        self._subtrees = subtrees

    def get_root(self) -> Optional[Any]:
        """d"""
        return self._root

    def get_course_leaves(self) -> list[CourseTree]:
        """docstring"""
        leaves = []
        for subtree in self._subtrees:
            if subtree.is_leaf():
                leaves += [subtree]
            else:
                leaves += subtree.get_course_leaves()
        return leaves

    @staticmethod
    def generate_course_tree(prerequisites: str, course_code: str | None = None) -> CourseTree:
        """docstring"""
        if course_code:
            # This is the top call, not a recursive call
            # If there are no prerequisites, return an empty tree
            if prerequisites == "N/A":
                return CourseTree(course_code, -1, [])
            else:
                course_tree = CourseTree.generate_course_tree(prerequisites)
                return CourseTree(course_code, -1, [course_tree])
        else:
            if is_graded_course_code(prerequisites):
                # BASE CASE: The prerequisites string is a single course code
                # We return a tree with 'prerequisites' as the root and no subtrees
                return CourseTree(prerequisites[0:8], int(prerequisites[9:11]), [])
            elif has_unnested(prerequisites, ","):
                # The prerequisites string is composed of entries separated by commas: (...),(...)
                # This indicates that all the constituents are required
                # We return a tree whose root is 'ALL' and whose subtrees are the constituents
                constituents = unnested_split(prerequisites, ",")
                return CourseTree(
                    'ALL', -1, [CourseTree.generate_course_tree(constituent) for constituent in constituents]
                )
            elif has_unnested(prerequisites, "/"):
                # The prerequisites string is composed of entries separated by slashes: (...)/(...)
                # This indicates that one of the constituents is required
                # We return a tree whose root is 'CHOOSE' and whose subtrees are the constituents
                constituents = unnested_split(prerequisites, "/")
                return CourseTree(
                    'CHOOSE', -1, [CourseTree.generate_course_tree(constituent) for constituent in constituents]
                )
            elif prerequisites[0] == "(" and prerequisites[-1] == ")":
                # The prerequisites string is entirely nested within redundant parentheses: (...)
                # We return the tree corresponding to what is within the parentheses
                return CourseTree.generate_course_tree(prerequisites[1:-1])
            else:
                raise Exception

    def _set_values(self, course_tree: CourseTree) -> None:
        self._root = course_tree._root
        self._subtrees = course_tree._subtrees

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


if __name__ == "__main__":
    ...
