import csv
import json
import re

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
                        if ENTRIES_TO_DATATYPE[item] == float:
                            data = 0.0
                        elif ENTRIES_TO_DATATYPE[item] == int:
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

        num_offerings = len(course_offerings)
        profs = {}
        # intellectual_engagement to likelihood_to_recommend
        metrics = list(ENTRIES_TO_DATATYPE.keys())[7:16]

        total_course_metrics = {metric: 0.0 for metric in metrics}

        print(course_code)
        for course_offering in course_offerings:
            # add up total metrics for averaging
            for metric in metrics:
                total_course_metrics[metric] += course_offering[metric]

            prof_name = f"{course_offering["prof_last_name"]}, {course_offering["prof_first_name"]}"

            # prof's total_rating is the sum of their instructor_environment and instructor_engagement ratings
            # add total terms taught
            if prof_name not in profs:
                profs[prof_name] = {
                    "num_terms_taught": 1,
                    "terms_taught": [
                        [course_offering["term"], course_offering["year"]]
                    ],
                    "total_rating": course_offering["instructor_environment"] + course_offering["instructor_engagement"]
                }
            else:
                profs[prof_name]["num_terms_taught"] += 1
                profs[prof_name]["terms_taught"].append([course_offering["term"], course_offering["year"]])
                profs[prof_name]["total_rating"] += (
                        course_offering["instructor_environment"] + course_offering["instructor_engagement"])

        average_course_metrics = {}
        average_course_metrics_rounded = {}
        for metric in total_course_metrics:
            average_course_metrics[metric] = total_course_metrics[metric] / num_offerings
            average_course_metrics_rounded[metric] = round(average_course_metrics[metric], round_ndigits)

        # mapping from each group to the metrics it averaged
        # e.g. course_quality is the average of intellectual_engagement, cognitive_growth
        metrics_grouped = {
            "course_quality": ["intellectual_engagement", "cognitive_growth"],
            "prof_quality": ["instructor_environment", "instructor_engagement"],
            "assessment_quality": ["assessment_learning_value", "assessment_alignment"],
            "workload": ["perceived_workload"],
            "satisfaction": ["overall_satisfaction", "likelihood_to_recommend"]
        }

        average_course_metrics_grouped = {}
        for group in metrics_grouped:
            # the metrics in the group to be averaged
            metrics_to_average = metrics_grouped[group]
            average_course_metrics_grouped[group] = round(
                sum(average_course_metrics[metric] for metric in metrics_to_average) / len(metrics_to_average),
                round_ndigits
            )


        # TODO: refactor this and the above prof code into another function
        # compute prof's average rating
        for prof_name in profs:
            prof = profs[prof_name]
            prof["average_rating"] = round(
                prof["total_rating"] / (2 * prof["num_terms_taught"]),
                round_ndigits
            )
            profs[prof_name].pop("total_rating")  # remove total_rating, as it was only used for averaging purposes

        computed[course_code] = {
            "average_metrics": average_course_metrics_rounded,
            "grouped_metrics": average_course_metrics_grouped,
            "historical_offerings": [],
            "profs": profs,
            "num_offerings": num_offerings,
        }

        # clear existing contents
        with open(output_filename, "w") as write_file:
            pass

        # write computed data to the file
        with open(output_filename, "a") as write_file:
            json.dump(computed, write_file, indent=2)


if __name__ == "__main__":
    group_by_course_code([
        "demo.csv"
    ], "course_data.json")
    compute("course_data.json", "course_data_computed.json")
