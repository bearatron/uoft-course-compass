"""main"""

from academic_calendar_reader import PrerequisiteTreeLoader

if __name__ == "__main__":
    programs = ["Computer Science", "Mathematics"]
    loader = PrerequisiteTreeLoader(programs)

    running = True
    while running:
        course = input("Please enter a course code: ")
        tree = loader.get_prerequisite_tree(course)
        print(tree)
        print()
