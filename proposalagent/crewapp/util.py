from crewai import Task

class RepeatedHumanInputTask(Task):
    def execute(self, context=None):
        result = None
        while True:
            # Execute the task logic
            result = super().execute(context=context)

            # Request human input
            human_feedback = input("Review the GoogleSheet and Update Balance details then Submit (type 'done' to finish): ")

            # Check if the user wants to finalize the task
            if human_feedback.lower() == 'done':
                break

            # Process the human feedback (this is a placeholder, you might want to update task details based on feedback)
            print("Processing Update...")

        return result
