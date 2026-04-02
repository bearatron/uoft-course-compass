"""Optimal Course Pathway Generation.

This module provides the core logic for calculating the most efficient or highly
rated prerequisite pathway to a target course. It introduces the `CourseRatingsTree`,
which extends standard course trees by integrating evaluation metrics (e.g., workload,
overall quality) parsed from pre-computed JSON data.

By applying a greedy algorithm, this module evaluates and resolves "CHOOSE" nodes
within the prerequisite structure. It returns a simplified `CourseTree` that
recommends the optimal course sequence tailored to both the student's previously
completed courses and their selected optimization metric.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

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
    Return the optimal CourseTree for a given course_code based on courses_taken and metric_name
    If higher_is_better, we look for courses with higher numerical ratings of the metric_name specified
     and vice versa if higher_is_better is false

    The CourseTree returned is one without any CHOOSE subtrees

    If an optimal path cannot be found, an empty tree is returned

    courses_taken is a dict that maps from the course code to the mark received in that course

    Preconditions:
        - course_code is a valid course code
        - metric_name must be under average_metrics or grouped_metrics in course_data_computed.json
    """
    # get the simplified course tree based on courses taken
    tree = loader.get_prerequisite_tree(course_code)
    tree = tree.get_simplified_tree(courses_taken)

    # convert it to a CourseRatingsTree
    ratings_tree = CourseRatingsTree.from_course_tree(tree, metric_name, higher_is_better)

    # return the optimal tree based on ratings
    return ratings_tree.return_optimal_tree()


class CourseDataNotFoundError(Exception):
    """Exception raised when attempting to access non-existent course data from a file"""

    def __str__(self) -> str:
        """Return a string representation of this error"""
        return "No such course data was found. Course either doesn't exist or has no course evals."


def _get_metric_rating(course_code: str, metric_name: str) -> float:
    """Return the corresponding metric rating of a course
    Throw a CourseDataNotFoundError if either course_code or metric_name are invalid

    Preconditions:
        - metric_name is under average_metrics or grouped_metrics in course_data_computed.json
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


class CourseRatingsTree(CourseTree):
    """
    A class that stores extra metric and rating information about a course
    """
    # Private Instance Attributes:
    #   - _subtrees: a list of subtrees of this tree
    #   - _metric: a string for the metric name, which must be within average_metrics or
    #       grouped_metrics in course_data_computed.json
    #   - _rating: a float representing the course's rating for that metric, None if the root is "ALL" or "CHOOSE"
    #   - _subtree_rating: a float representing the average rating of child courses, or
    #       the optimal rating of child courses if root is "CHOOSE"
    #   - _higher_is_better: a bool representing whether a higher rating is better or a lower rating is better
    _subtrees: list[CourseRatingsTree]
    _metric: str
    _rating: Optional[float]
    _subtree_rating: float
    _higher_is_better: bool

    def __init__(self,
                 root: Optional[Any],
                 grade: int,
                 subtrees: list[CourseRatingsTree],
                 metric: str,
                 rating: Optional[float],
                 subtree_rating: float,
                 higher_is_better: bool) -> None:
        """
        Initialize a new CourseRatingsTree with the given parameters
        root and grade are the same parameters as CourseTre
        subtrees contains a list of CourseRatingsTrees instead of CourseTrees
        all other attributes are new to CourseRatingsTree

        If root is None, the tree is empty.
        If rating is None, the root is either "ALL" or "CHOOSE"

        Preconditions:
            - self._root is not None or self._subtrees == []
            - -1 <= self._grade <= 100
            - 0.0 <= self._rating <= 5.0 == self._root not in {"ALL", "CHOOSE"}
            - self._rating is None == self._root in {"ALL", "CHOOSE"}
            - 0.0 <= self.avg_rating <= 5.0
        """
        # note that we won't need the superclass's subtrees attribute since we defined our own,
        #  so we pass an empty list to its constructor
        super().__init__(root, grade, [])
        self._subtrees = subtrees
        self._metric = metric
        self._rating = rating
        self._subtree_rating = subtree_rating
        self._higher_is_better = higher_is_better

    @classmethod
    def from_course_tree(cls, course_tree_instance: CourseTree, metric: str, higher_is_better: bool):
        """
        Initializes a CourseRatingsTree from a CourseTree instance, with additional
         attributes like metric and higher_is_better
        The rest of the attributes are computed
        """
        # rating is calculated below
        if course_tree_instance._root in {"ALL", "CHOOSE"}:
            # "ALL" or "CHOOSE" nodes don't have a rating
            rating = None
        else:
            try:
                # find this course's metric rating
                rating = _get_metric_rating(course_tree_instance._root, metric)
            except CourseDataNotFoundError:
                # rating cannot be found, set its value to be the least optimal to
                #  incentivise choosing courses in which we have ratings for
                if higher_is_better:
                    rating = 0.0
                else:
                    rating = 5.0

        # convert subtrees, which are CourseTrees, to CourseRatingsTrees
        subtrees = course_tree_instance._subtrees
        new_subtrees = []

        for subtree in subtrees:
            # use the provided metric and higher_is_better parameters
            new_subtree = CourseRatingsTree.from_course_tree(subtree, metric, higher_is_better)
            new_subtrees.append(new_subtree)

        # subtree_rating will be calculated below
        if course_tree_instance._root == "CHOOSE":
            # for CHOOSE nodes, subtree_rating is the best among child subtree ratings
            if higher_is_better:
                subtree_rating = max(t.get_subtree_rating() for t in new_subtrees)
            else:
                subtree_rating = min(t.get_subtree_rating() for t in new_subtrees)
        elif course_tree_instance._root == "ALL":
            # for ALL nodes, subtree_rating is the average among child subtree ratings
            total_rating = 0.0

            for subtree in new_subtrees:
                total_rating += subtree.get_subtree_rating()

            subtree_rating = total_rating / len(subtrees)
        else:
            # for course nodes, subtree_rating is the average rating among the current course and child subtrees
            total_rating = rating

            for subtree in new_subtrees:
                total_rating += subtree.get_subtree_rating()

            subtree_rating = total_rating / (len(subtrees) + 1)

        # return the resulting CourseRatingsTree
        return cls(
            root=course_tree_instance._root,
            grade=course_tree_instance._required_grade,
            subtrees=new_subtrees,
            metric=metric,
            rating=rating,
            subtree_rating=subtree_rating,
            higher_is_better=higher_is_better
        )

    def get_rating(self):
        """Return this course's rating"""
        return self._rating

    def get_subtree_rating(self):
        """Return the subtree rating of this course"""
        return self._subtree_rating

    def get_subtrees(self) -> list[CourseRatingsTree]:
        """Return the subtrees of this CourseRatingsTree"""
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
            str_so_far = '  ' * depth + f'{self._root} {grade_string} {self._rating} {self._subtree_rating}\n'
            for subtree in self._subtrees:
                str_so_far += subtree._str_indented(depth + 1)
            return str_so_far

    def return_optimal_tree(self) -> CourseTree:
        """
        Return a CourseTree representation of the most optimal path from the current course to leaf courses
        The optimal path is defined by the metric, rating, and higher_is_better attributes
        """
        if self._root == "CHOOSE":
            # for CHOOSE nodes, pick the most optimal subtree
            # this is a greedy algorithm that picks the optimally-rated course at each step

            if self._higher_is_better:
                highest_rating = 0.0
                highest_subtree = None

                # find the highest rated subtree
                for subtree in self._subtrees:
                    if subtree.get_subtree_rating() >= highest_rating:
                        highest_rating = subtree.get_subtree_rating()
                        highest_subtree = subtree

                # recurse into the highest rated child to get its optimal sub-path
                highest_subtree = highest_subtree.return_optimal_tree()
                return highest_subtree
            else:
                # lower is better
                lowest_rating = 5.0
                lowest_subtree = None

                # find the lowest rated subtree
                for subtree in self._subtrees:
                    if subtree.get_subtree_rating() <= lowest_rating:
                        lowest_rating = subtree.get_subtree_rating()
                        lowest_subtree = subtree

                # recurse into the highest rated child to get its optimal sub-path
                lowest_subtree = lowest_subtree.return_optimal_tree()
                return lowest_subtree
        else:
            # for ALL subtrees and subtrees with courses as children, we have no choices to make
            optimal_subtrees = []

            # recurse into each child to get the optimal sub-path, and add it to subtree accumulator
            for subtree in self._subtrees:
                optimal_subtrees.append(subtree.return_optimal_tree())

            optimal_tree = CourseTree(self._root, self._required_grade, optimal_subtrees)
            return optimal_tree
