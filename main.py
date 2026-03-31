"""main"""

from academic_calendar_reader import CourseNotFoundError, PrerequisiteTreeLoader
from optimal_path_to_course import CourseRatingsTree, optimal_path_to_course

if __name__ == "__main__":
    programs = ["Computer Science", "Mathematics"]
    loader = PrerequisiteTreeLoader()
    loader.load_from_file("prerequisite_tree_save_data.json")
    courses_taken = {
        'MAT137Y1': 100,
        'CSC110Y1': 100,
        'CSC111H1': 100,
        'MAT223H1': 100,
        'STA237H1': 100
    }

    running = True
    while running:
        course = input("Please enter a course code: ")

        try:
            tree = loader.get_prerequisite_tree(course)
        except CourseNotFoundError:
            print("That course does not exist")
            continue

        print(tree)
        print('------')

        simplified_tree = loader.get_simplified_tree(course, courses_taken)
        print(simplified_tree)
        print('=' * 6)
        metric = "prof_quality"
        higher_is_better = True
        print(f"Ratings for {metric} ({"higher is better" if higher_is_better else "lower is better"}):")
        print(CourseRatingsTree.from_course_tree(simplified_tree, metric, higher_is_better))
        print('-' * 6)
        print("optimal path:")
        print(optimal_path_to_course(
            loader,
            course,
            courses_taken,
            metric,
            higher_is_better))

        print('-' * 6)
