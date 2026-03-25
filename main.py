"""main"""

from academic_calendar_reader import PrerequisiteTreeLoader

if __name__ == "__main__":
    programs = ["Computer Science", "Mathematics"]
    loader = PrerequisiteTreeLoader(programs)

    running = True
    while running:
        course = input("Please enter a course code: ")
        tree = loader.get_prerequisite_tree(course)
        name, description = loader.get_name_and_description(course)
        print(name)
        print(description)
        print(tree)
        print()
