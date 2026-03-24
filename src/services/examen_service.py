# Exam Business Logic

class Exam:
    def __init__(self, subject, date, duration):
        self.subject = subject
        self.date = date
        self.duration = duration

    def is_conflict(self, other_exam):
        return self.date == other_exam.date

    def __str__(self):
        return f"Exam(subject={self.subject}, date={self.date}, duration={self.duration})"

# Example usage
if __name__ == '__main__':
    exam1 = Exam('Math', '2026-03-25', 90)
    exam2 = Exam('Physics', '2026-03-25', 120)
    print(exam1)
    print(exam2)
    print(f"Conflict: {exam1.is_conflict(exam2)}")