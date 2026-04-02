"""main"""

from academic_calendar_reader import CourseNotFoundError, PrerequisiteTreeLoader
from optimal_path_to_course import CourseRatingsTree, optimal_path_to_course

if __name__ == "__main__":
    visualizer = TreeVisualizer()
    visualizer.run_simulation()
