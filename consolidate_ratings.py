"""Course Evaluation Data Processing Pipeline.

This module provides the data transformation logic for processing raw course
evaluation data scraped into CSV files. It defines a pipeline that first cleans
and groups the raw data by course code using regular expressions, and then
computes key aggregate metrics.

The core functions calculate average satisfaction scores, group related metrics
(e.g., workload, assessment quality), determine historical and summer course
availability, and rank professors based on student feedback. The final output
is compiled into a structured JSON format used by the main visualizer application.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

import csv
import json
import re
from typing import Any

# a mapping from each entry to its corresponding datatype to be converted to
ENTRIES_TO_DATATYPE = {
    "dept": str,
    "division": str,
    "course": str,
    "prof_last_name": str,
    "prof_first_name": str,
    "term": str,
    "year": int,
    "intellectual_engagement": float,
    "cognitive_growth": float,
    "instructor_environment": float,
    "assessment_learning_value": float,
    "assessment_alignment": float,
    "overall_satisfaction": float,
    "instructor_engagement": float,
    "perceived_workload": float,
    "likelihood_to_recommend": float,
    "num_invited": int,
    "num_responses": int
}


def group_by_course_code(filenames: list[str], output_filename: str) -> None:
    """
    This function groups the course eval data in csvs by course code and outputs them in a json file
    filenames contains the names of the course evals csv files
    output_filename is the name of the json file to output to
    Note: if output_filename already exists, its contents will be cleared and overwritten with the new output

    Preconditions:
        - all([f.rsplit(".", 1)[1] == "csv" for f in filenames])  # all filenames provided end in .csv
        - output_filename.rsplit(".", 1)[1] == "json"  # output_filename ends in .json
    """
    course_data = {}

    for filename in filenames:
        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                entry_to_data = {}

                for i, item in enumerate(row):
                    # find the correct key in the ENTRIES_TO_DATATYPE dict
                    # based on index of the element in the current row
                    entry = list(ENTRIES_TO_DATATYPE.keys())[i]

                    # TODO: deal with N/A
                    if item == "N/A":
                        if ENTRIES_TO_DATATYPE[entry] == float:
                            data = 0.0
                        elif ENTRIES_TO_DATATYPE[entry] == int:
                            data = 0
                        else:
                            data = "N/A"
                    else:
                        # convert the current row item to the desired datatype
                        data = ENTRIES_TO_DATATYPE[entry](item)

                    entry_to_data[entry] = data

                # use regex to search for a course code pattern
                # e.g. this is how MAT235Y1 is seen as a match:
                # [A-Z]{3}  exactly 3 capital letters (MAT)
                # \d{3}     exactly 3 digits (235)
                # [YH]      exactly 1 Y or H (Y)
                # \d        exactly 1 digit (1)

                course_code_pattern = r"[A-Z]{3}\d{3}[YH]\d"
                match = re.search(course_code_pattern, entry_to_data["course"])

                if match:
                    course_code = match.group()
                else:
                    continue

                if course_code not in course_data:
                    course_data[course_code] = [entry_to_data]
                else:
                    course_data[course_code].append(entry_to_data)

    # clear existing contents
    with open(output_filename, "w") as write_file:
        pass

    # write course data to file
    with open(output_filename, "a") as write_file:
        json.dump(course_data, write_file, indent=2)


def compute(filename: str, output_filename: str) -> None:
    """
    Performs some computations on raw json course data and outputs it in json format
    filename specifies the json course data to compute on
    output_filename specifies the name of the filename to output to
    Note: if output_filename already exists, its contents will be cleared and overwritten with the new output

    Preconditions:
        - filename.rsplit(".", 1)[1] == "json"  # filename ends in .json
        - output_filename.rsplit(".", 1)[1] == "json"  # output_filename ends in .json
    """
    round_ndigits = 2  # number of decimal places to round averages to

    course_data = {}
    with open(filename, "r") as read_file:
        course_data = json.load(read_file)

    computed = {}

    for course_code in course_data:
        course_offerings = course_data[course_code]

        num_responses = _compute_num_responses(course_offerings)
        num_offerings = len(course_offerings)
        historical_offerings = _compute_historical_offerings(course_offerings)

        years_offered = {term[1] for term in historical_offerings}
        num_years_offered = len(years_offered)

        summer_offerings = _compute_summer_offerings(historical_offerings)

        # gets the metrics in the ENTRIES_TO_DATATYPE mapping
        # metrics are intellectual_engagement to likelihood_to_recommend
        metrics = list(ENTRIES_TO_DATATYPE.keys())[7:16]

        average_course_metrics, average_course_metrics_rounded = (
            _compute_average_metrics(metrics, course_offerings, round_ndigits))

        # mapping from each group to the metrics it averaged
        # e.g. course_quality is the average of intellectual_engagement, cognitive_growth
        metrics_grouped = {
            "course_quality": ["intellectual_engagement", "cognitive_growth"],
            "prof_quality": ["instructor_environment", "instructor_engagement"],
            "assessment_quality": ["assessment_learning_value", "assessment_alignment"],
            "workload": ["perceived_workload"],
            "satisfaction": ["overall_satisfaction", "likelihood_to_recommend"]
        }

        average_course_metrics_grouped = (
            _compute_average_metrics_grouped(metrics_grouped, average_course_metrics, round_ndigits))

        profs = _compute_prof_data(course_offerings, round_ndigits)
        profs_by_rating = _sorted_profs(profs)

        computed[course_code] = {
            "num_responses": num_responses,
            "average_metrics": average_course_metrics_rounded,
            "grouped_metrics": average_course_metrics_grouped,
            "num_offerings": num_offerings,
            "num_years_offered": num_years_offered,
            "historical_offerings": historical_offerings,
            "summer_offerings": summer_offerings,
            "profs": profs,
            "profs_by_rating": profs_by_rating,
        }

        # clear existing contents
        with open(output_filename, "w") as write_file:
            pass

        # write computed data to the file
        with open(output_filename, "a") as write_file:
            json.dump(computed, write_file, indent=2)


##########################################
# Below are helper functions for compute #
##########################################

def _compute_num_responses(course_offerings):
    total_responses = 0
    for course_offering in course_offerings:
        total_responses += course_offering["num_responses"]
    return total_responses


def _compute_average_metrics(
        metrics: list[str],
        course_offerings: list[dict],
        round_ndigits: int) -> tuple[dict[str, float], dict[str, float]]:
    """
    Computes the average metrics for a course
    metrics is a list of metrics that will be keys in the dicts that are returned
    course_offerings is a list of dicts, with each key value pair representing a mapping from column title to
     row entry in the course eval table that was scraped from

    Returns two mappings from metric name to average metric, one unrounded and one rounded to the nearest
    decimal place specified by round_ndigits
    """
    num_offerings = len(course_offerings)

    # initialize the total metrics dictionary with default values
    # this will be an accumulator for each course metric
    total_course_metrics = {metric: 0.0 for metric in metrics}

    for course_offering in course_offerings:
        # add up total metrics for averaging
        for metric in metrics:
            total_course_metrics[metric] += course_offering[metric]

    average_course_metrics = {}
    average_course_metrics_rounded = {}

    # compute averages
    for metric in total_course_metrics:
        average_course_metrics[metric] = total_course_metrics[metric] / num_offerings
        average_course_metrics_rounded[metric] = round(average_course_metrics[metric], round_ndigits)

    return average_course_metrics, average_course_metrics_rounded


def _compute_average_metrics_grouped(
        metrics_grouped: dict[str, list[str]],
        average_course_metrics: dict[str, float],
        round_ndigits: int) -> dict[str, float]:
    """
    Compute average course metrics grouped into categories
    """

    average_course_metrics_grouped = {}
    for group in metrics_grouped:
        # the metrics in the group to be averaged
        metrics_to_average = metrics_grouped[group]
        average_course_metrics_grouped[group] = round(
            sum(average_course_metrics[metric] for metric in metrics_to_average) / len(metrics_to_average),
            round_ndigits
        )

    return average_course_metrics_grouped


def _compute_prof_data(course_offerings: list[dict], round_ndigits: int) -> dict[str, dict[str, Any]]:
    """
    Compute prof data for a course
    course_offerings is a list of dicts, with each key value pair representing a mapping from column title to
     row entry in the course eval table that was scraped from

    Returns a list of mappings from prof names to various data including:
        - number of terms taught
        - terms taught
        - average rating
    """
    profs = {}

    for course_offering in course_offerings:
        prof_name = f"{course_offering['prof_last_name']}, {course_offering['prof_first_name']}"

        # prof's total_rating is the sum of their instructor_environment and instructor_engagement ratings
        # total_rating is for the purpose of calculating average_rating and will be removed prior to function return
        if prof_name not in profs:
            profs[prof_name] = {
                "num_terms_taught": 1,
                "terms_taught": [
                    [course_offering["term"], course_offering["year"]]
                ],
                "total_rating": course_offering["instructor_environment"] + course_offering["instructor_engagement"],
                "total_reviews": course_offering["num_responses"]
            }
        else:
            profs[prof_name]["num_terms_taught"] += 1
            profs[prof_name]["terms_taught"].append([course_offering["term"], course_offering["year"]])
            profs[prof_name]["total_rating"] += (
                    course_offering["instructor_environment"] + course_offering["instructor_engagement"])
            profs[prof_name]["total_reviews"] += course_offering["num_responses"]

    # compute prof's average rating
    for prof_name in profs:
        prof = profs[prof_name]
        prof["average_rating"] = round(
            prof["total_rating"] / (2 * prof["num_terms_taught"]),
            round_ndigits
        )
        profs[prof_name].pop("total_rating")  # remove total_rating, as it was only used for averaging purposes

    return profs


def _sorted_profs(profs: dict[str, Any]) -> list[str]:
    """
    Returns a list of prof names sorted by their average rating

    >>> profs = {
    ... "Doe, John": {"average_rating": 4.2, "irrelevant_attribute": 0},
    ... "Smith, Jane": {"average_rating": 2.0, "irrelevant_attribute": 1},
    ... "Ipsum, Lorem": {"average_rating": 3.3, "irrelevant_attribute": 2}
    ... }
    >>> _sorted_profs(profs)
    ['Doe, John', 'Ipsum, Lorem', 'Smith, Jane']
    """
    prof_name_and_ratings = [(prof_name, profs[prof_name]["average_rating"]) for prof_name in profs]
    prof_name_and_ratings.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in prof_name_and_ratings]


def _compute_historical_offerings(course_offerings: list[dict]) -> list[list[str | int]]:
    """
    Returns a list containing the academic terms a course was offered in

    course_offerings is a list of dicts, with each key value pair representing a mapping from column title to
     row entry in the course eval table that was scraped from

    An academic term is represented as a list of two elements:
        - the season (a str that's one of Fall/Winter/Summer), and
        - the year (an int, e.g. 2025)

    Note that a Y course in the Fall/Winter term has season "Winter"

    It is guaranteed that there will be no duplicate terms in the output list

    >>> course_offerings = [
    ...     {
    ...         "term": "Fall",
    ...         "year": 2024
    ...     },
    ...     {
    ...         "term": "Winter",
    ...         "year": 2024
    ...     },
    ...     {
    ...         "term": "Winter",
    ...         "year": 2025
    ...     },
    ...     {
    ...         "term": "Summer",
    ...         "year": 2025
    ...     },
    ...     {
    ...         "term": "Summer",
    ...         "year": 2025
    ...     },
    ... ]
    >>> _compute_historical_offerings(course_offerings)
    [['Summer', 2025], ['Winter', 2025], ['Winter', 2024], ['Fall', 2024]]
    """
    terms_offered = set()

    # prevent duplicates by adding to a set
    for offering in course_offerings:
        terms_offered.add((offering["term"], offering["year"]))

    # a mapping representing the desired sorting order of the seasons (chronologically)
    season_sort_map = {
        "Fall": 0,
        "Winter": 1,
        "Summer": 2
    }

    # sort the academic terms from most to least recent
    result = sorted(list(terms_offered), key=lambda x: (x[1], season_sort_map[x[0]]), reverse=True)
    result = [list(x) for x in result]

    return result


def _compute_summer_offerings(historical_offerings: list[list[str | int]]) -> dict:
    """
    Based on the historical offerings of a course, this function computes
        - the most recent year a summer course was offered
        - the number of years summer courses were offered
        - a list of the years in chronological order in which summer courses were offered
    Returns the above data in a dictionary

    >>> historical_offerings = [['Summer', 2025], ['Winter', 2025], ['Winter', 2024], ['Fall', 2024], ['Summer', 2023]]
    >>> expected = {
    ...     "most_recent_year": 2025,
    ...     "num_years_offered": 2,
    ...     "years_offered": [2025, 2023],
    ... }
    >>> _compute_summer_offerings(historical_offerings) == expected
    True
    >>> historical_offerings = []
    >>> expected = {
    ...     "most_recent_year": 0,
    ...     "num_years_offered": 0,
    ...     "years_offered": [],
    ... }
    >>> _compute_summer_offerings(historical_offerings) == expected
    True
    """
    summer_years_offered = {term[1] for term in historical_offerings if term[0] == "Summer"}
    summer_years_offered_chronological = sorted(list(summer_years_offered), reverse=True)

    if len(summer_years_offered_chronological) == 0:
        most_recent_year = 0
    else:
        most_recent_year = summer_years_offered_chronological[0]

    result = {
        "most_recent_year": most_recent_year,
        "num_years_offered": len(summer_years_offered),
        "years_offered": summer_years_offered_chronological,
    }

    return result


if __name__ == "__main__":
    group_by_course_code([
        "computer_science.csv",
        "economics.csv",
        "mathematics.csv",
        "physics.csv",
        "statistical_sciences.csv",
    ], "course_data.json")
    compute("course_data.json", "course_data_computed.json")

    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': [],
        'disable': ['static_type_checker'],
    })
