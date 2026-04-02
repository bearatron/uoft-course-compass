"""
Main file to run application
This file launches the TreeVisualizer application.
When run directly, it creates an instance of TreeVisualizer and starts
the main pygame event loop for the course visualization interface.

This file is Copyright (c) 2026 Shayan Bhatti, Jacob Chislett, Ethan Diep, Shuhan Yuan
"""

from TreeVisualizer import TreeVisualizer

if __name__ == "__main__":
    visualizer = TreeVisualizer()
    visualizer.run_simulation()

    # |----------------------------------------------------------------------------------------------------------------|
    # | UNCOMMENT THE BELOW CODE FOR A DEMONSTRATION ON HOW THE ACADEMIC CALENDAR DATASET IS GENERATED                 |
    # | This code will scrape information from the U of T academic calendar website, parse the prerequisite strings,   |
    # | rewrite them in a format that is easier to run computations on and save all information including course names |
    # | and descriptions to a json file called 'dataset_example.json'                                                  |
    # |----------------------------------------------------------------------------------------------------------------|
    # from academic_calendar_reader import PrerequisiteTreeLoader
    # loader = PrerequisiteTreeLoader
    # loader.load_from_programs(['Computer Science'])
    # loader.save_to_file('dataset_example.json')

    # |----------------------------------------------------------------------------------------------------------------|
    # | UNCOMMENT THE BELOW CODE FOR A DEMONSTRATION ON HOW THE COURSE EVALUATION DATASET IS GENERATED                 |
    # | This code will scrape information from the UofT course evaluations calendar website, and                       |
    # | rewrite them in a format that is easier to run computations on and save all information. The output            |
    # | can found in demo.csv.                                                                                         |
    # | NOTE: GOOGLE CHROME MUST BE INSTALLED ON YOUR COMPUTER FOR THIS TO RUN                                         |
    # | IMPORTANT: A NEW CHROME WINDOW WILL OPEN ON YOUR COMPUTER. DO NOT INTERACT WITH THE WEBPAGE IN ANY WAY.        |
    # |            IT IS SCRAPING THE DATA.                                                                            |
    # |----------------------------------------------------------------------------------------------------------------|
    # from course_evals_parser import CourseEvalsParser
    # CourseEvalsParser.demo()

    # |----------------------------------------------------------------------------------------------------------------|
    # | UNCOMMENT THE BELOW CODE FOR A DEMONSTRATION ON HOW THE COURSE EVALUATION DATASET IS COMPUTED                  |
    # | Computing the data is much faster than scraping so this code uses the real csv datasets. First it will         |
    # | group all the data by course code and output it to course_data.json. Then it will perform computations         |
    # | and output those to course_data_computed.json.                                                                 |
    # |                                                                                                                |
    # | The group_by_course_code function is quick, but the compute function can take around 20-30 seconds.            |
    # |----------------------------------------------------------------------------------------------------------------|
    # from consolidate_ratings import group_by_course_code, compute
    #
    # group_by_course_code([
    #     "computer_science.csv",
    #     "economics.csv",
    #     "mathematics.csv",
    #     "physics.csv",
    #     "statistical_sciences.csv",
    # ], "course_data.json")
    # compute("course_data.json", "course_data_computed.json")
