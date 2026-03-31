from __future__ import annotations
from typing import Any, Optional
from academic_calendar_reader import PrerequisiteTreeLoader
from course_tree import CourseTree
import json


def optimal_path_to_course(
        loader: PrerequisiteTreeLoader,
        course_code: str,
        courses_taken: dict[str, int],
        metric_name: str,
        higher_is_better: bool) -> CourseTree:
    """
    A recursive function that returns the optimal tree for the given course code based on what
     courses the user has taken and a certain metric
    If higher_is_better is true, we look for courses with higher numerical ratings of the metric specified
     and vice versa if higher_is_better is false

    The CourseTree returned is one without any CHOOSE subtrees

    If an optimal path cannot be found, an empty tree is returned

    courses_taken is a dict that maps from the course code to the mark received in that course

    Preconditions:
        - course_code is a valid course code
        - metric_name must be under average_metrics or grouped_metrics in course_data_computed.json
    """

    tree = loader.get_simplified_tree(course_code, courses_taken)
    ratings_tree = CourseRatingsTree.from_course_tree(tree, metric_name, higher_is_better)

    return ratings_tree.return_optimal_tree()


class CourseRatingsTree(CourseTree):
    _subtrees: list[CourseRatingsTree]
    _metric: str
    _rating: float
    _avg_rating: float
    _higher_is_better: bool

    def __init__(self,
                 root: Optional[Any],
                 grade: int,
                 subtrees: list[CourseTree],
                 metric: str,
                 rating: Optional[float],
                 avg_rating: float,
                 higher_is_better: bool) -> None:
        """Initialize a new CourseRatingsTree with the given root value, grade, subtrees, metric, and rating

        If root is None, the tree is empty.
        If rating is None, the root is either ALL or CHOOSE

        Preconditions:
            - self._root is not None or self._subtrees == []
            - -1 <= self._grade <= 100
            - 0.0 <= self._rating <= 5.0 == self._root not in {"ALL", "CHOOSE"}
            - self._rating is None == self._root in {"ALL", "CHOOSE"}
            - 0.0 <= self.avg_rating <= 5.0
        """
        super().__init__(root, grade, subtrees)
        self._metric = metric
        self._rating = rating
        self._avg_rating = avg_rating
        self._higher_is_better = higher_is_better

    @classmethod
    def from_course_tree(cls, course_tree_instance: CourseTree, metric: str, higher_is_better: bool):
        """
        Initializes a CourseRatingsTree from an instance of its parent (CourseTree)
        """

        if course_tree_instance._root in {"ALL", "CHOOSE"}:
            rating = None
        else:
            try:
                rating = _get_metric_rating(course_tree_instance._root, metric)
            except CourseDataNotFoundError:
                if higher_is_better:
                    rating = 0.0
                else:
                    rating = 5.0

        subtrees = course_tree_instance._subtrees
        new_subtrees = []

        if course_tree_instance._root == "CHOOSE":
            for subtree in subtrees:
                new_subtree = CourseRatingsTree.from_course_tree(subtree, metric, higher_is_better)
                new_subtrees.append(new_subtree)

            if higher_is_better:
                avg_rating = max(t.get_avg_rating() for t in new_subtrees)
            else:
                avg_rating = min(t.get_avg_rating() for t in new_subtrees)
        elif course_tree_instance._root == "ALL":
            total_rating = 0.0

            for subtree in subtrees:
                new_subtree = CourseRatingsTree.from_course_tree(subtree, metric, higher_is_better)
                new_subtrees.append(new_subtree)
                total_rating += new_subtree.get_avg_rating()

            avg_rating = total_rating / len(subtrees)
        else:
            total_rating = rating

            for subtree in subtrees:
                new_subtree = CourseRatingsTree.from_course_tree(subtree, metric, higher_is_better)
                new_subtrees.append(new_subtree)
                total_rating += new_subtree.get_avg_rating()

            avg_rating = total_rating / (len(subtrees) + 1)

        return cls(
            root=course_tree_instance._root,
            grade=course_tree_instance._required_grade,
            subtrees=new_subtrees,
            metric=metric,
            rating=rating,
            avg_rating=avg_rating,
            higher_is_better=higher_is_better
        )

    def get_rating(self):
        """Returns the rating of this course"""
        return self._rating

    def get_avg_rating(self):
        """Returns the avg of the ratings of this course"""
        return self._avg_rating

    def get_subtrees(self) -> list[CourseRatingsTree]:
        """Returns the subtrees of this CourseRatingsTree"""
        return self._subtrees

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
            str_so_far = '  ' * depth + f'{self._root} {grade_string} {self._rating} {self._avg_rating}\n'
            for subtree in self._subtrees:
                str_so_far += subtree._str_indented(depth + 1)
            return str_so_far

    def return_optimal_tree(self) -> CourseTree:
        """
        optimal tree
        """
        if self._root == "CHOOSE":
            if self._higher_is_better:
                highest_rating = 0.0
                highest_subtree = None
                for subtree in self._subtrees:
                    if subtree.get_avg_rating() >= highest_rating:
                        highest_rating = subtree.get_avg_rating()
                        highest_subtree = subtree

                highest_subtree = highest_subtree.return_optimal_tree()
                return highest_subtree
            else:
                lowest_rating = 5.0
                lowest_subtree = None
                for subtree in self._subtrees:
                    if subtree.get_avg_rating() <= lowest_rating:
                        lowest_rating = subtree.get_avg_rating()
                        lowest_subtree = subtree

                lowest_subtree = lowest_subtree.return_optimal_tree()
                return lowest_subtree
        else:
            optimal_subtrees = []
            for subtree in self._subtrees:
                optimal_subtrees.append(subtree.return_optimal_tree())
            optimal_tree = CourseTree(self._root, self._required_grade, optimal_subtrees)
            return optimal_tree


class CourseDataNotFoundError(Exception):
    """Exception raised when attempting to access non-existent course data from a file"""
    def __str__(self) -> str:
        """Return a string representation of this error"""
        return "No such course data was found. Course either doesn't exist or has no course evals."


def _get_metric_rating(course_code: str, metric_name: str) -> float:
    """Returns the corresponding metric rating of a course

    Preconditions:
        - metric_name is under average_metrics or grouped_metrics
    """
    with open("course_data_computed.json", "r") as file:
        data = json.load(file)

    if course_code not in data:
        raise CourseDataNotFoundError
    elif metric_name in data[course_code]["average_metrics"]:
        return data[course_code]["average_metrics"][metric_name]
    elif metric_name in data[course_code]["grouped_metrics"]:
        return data[course_code]["grouped_metrics"][metric_name]
    else:
        raise CourseDataNotFoundError
