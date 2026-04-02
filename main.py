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
