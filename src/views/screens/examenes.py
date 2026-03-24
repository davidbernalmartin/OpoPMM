class ExamInterface:
    def __init__(self, exam_data):
        self.exam_data = exam_data

    def start_exam(self):
        # Start the exam logic
        pass

    def submit_exam(self):
        # Submit the exam logic
        pass

    def get_results(self):
        # Logic to get the results
        return self.exam_data
