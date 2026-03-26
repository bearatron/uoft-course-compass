import csv
import json
import re


def group_by_course_code(filenames: list[str]) -> None:
    """
    Groups the course evals by course code and outputs them in a JSON

    Preconditions:
        - all([f.rsplit(".", 1)[1] == "csv" for f in filenames])  # all filenames provided end in .csv
    """
    output_filename = "course_data.json"
    course_data = {}

    for filename in filenames:
        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                entries = [
                    "dept",
                    "division",
                    "course",
                    "prof_last_name",
                    "prof_first_name",
                    "term",
                    "year",  # index 6
                    "intellectual_engagement",  # index 7
                    "cognitive_growth",
                    "instructor_environment",
                    "assessment_learning_value",
                    "assessment_alignment",
                    "overall_satisfaction",
                    "instructor_engagement",
                    "perceived_workload",
                    "likelihood_to_recommend",
                    "num_invited",  # index 16
                    "num_responses"
                ]

                entry_to_data = {}

                for i in range(len(row)):
                    if i >= 16 or i == 6:
                        # num_invited, num_responses, year
                        if row[i] == "N/A":
                            data = -1
                        else:
                            data = int(row[i])
                    elif i >= 7:
                        # course rating entries
                        if row[i] == "N/A":
                            data = -1.0
                        else:
                            data = float(row[i])
                    else:
                        data = row[i]

                    entry_to_data[entries[i]] = data

                # use regex to search for a course code pattern
                # e.g. in MAT235Y1:
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


# @dataclass
# class Professor:
#     num_terms_taught: int
#     terms_taught: list[list[str, int]]

def compute(filename: str) -> None:
    """
    Performs some computations on the raw JSON course data

    Preconditions:
        - filename.rsplit(".", 1)[1] == "json"  # filename ends in .json
    """
    output_filename = "course_data_computed.json"
    round_ndigits = 2

    course_data = {}
    with open(filename, "r") as read_file:
        course_data = json.load(read_file)

    computed = {}

    for course_code in course_data:
        offerings = course_data[course_code]

        total_intellectual_engagment = 0.0
        total_cognitive_growth = 0.0
        num_offerings = len(offerings)
        profs = {}

        print(course_code)
        for offering in offerings:
            keys = list(offering.keys())[7:16]
            eval_qs = {k: 0.0 for k in keys}

            total_intellectual_engagment += offering["intellectual_engagement"]
            total_cognitive_growth += offering["cognitive_growth"]

            name = f"{offering["prof_last_name"]}, {offering["prof_first_name"]}"

            # instructor_environment, instructor_engagement
            total_instructor_environment = 0.0
            total_instructor_engagement = 0.0

            if name not in profs:
                profs[name] = {
                    "num_terms_taught": 1,
                    "terms_taught": [
                        f"{offering["term"]} {offering["year"]}"
                    ],
                    "total_score": offering["instructor_environment"] + offering["instructor_engagement"]
                }
            else:
                profs[name]["num_terms_taught"] += 1
                profs[name]["terms_taught"].append(f"{offering["term"]} {offering["year"]}")
                profs[name]["total_score"] += offering["instructor_environment"] + offering["instructor_engagement"]


        course_quality = round(
            (total_intellectual_engagment + total_cognitive_growth) / (2 * num_offerings),
            round_ndigits
        )

        for name in profs:
            prof = profs[name]
            prof["average_score"] = round(
                prof["total_score"] / (2 * prof["num_terms_taught"]),
                round_ndigits
            )

        computed[course_code] = {
            "average_ratings": {
                "course_quality": course_quality,
                "assessment_quality": 0.0,
                "workload": 0.0,
                "satisfaction": 0.0
            },
            "historical_offerings": [],
            "profs": profs,
            "num_rows": 0,
        }
        factors = [
            # average of intellectual_engagement, cognitive_growth
            "course_quality",
            # average of instructor_environment, instructor_engagement
            "prof_quality",
            # average of assessment_learning_value, assessment_alignment
            "assessment_quality",
            # perceived_workload
            "workload",
            # average of overall_satisfaction, likelihood_to_recommend
            "satisfaction"
        ]
        # clear existing contents
        with open(output_filename, "w") as write_file:
            pass

        # write course data to file
        with open(output_filename, "a") as write_file:
            json.dump(computed, write_file, indent=2)


if __name__ == "__main__":
    group_by_course_code([
        "computer_science.csv",
        "economics.csv",
        "mathematics.csv",
        "physics.csv",
        "statistical_sciences.csv"
    ])
    compute("course_data.json")
