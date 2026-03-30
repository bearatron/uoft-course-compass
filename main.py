"""main"""

from academic_calendar_reader import PrerequisiteTreeLoader

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

        tree = loader.get_prerequisite_tree(course)
        print(tree)
        print('------')

        simplified_tree = loader.get_simplified_tree(course, courses_taken)
        print(simplified_tree)
        print('------')
