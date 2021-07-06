from datetime import datetime

class DateUtil:
    def __init__(self):
        self.start_time = any
        self.end_time = any

    def record_start_time(self, operationName):
        self.start_time = datetime.utcnow()
        print(f'Starting to {operationName} at {self.start_time}')

    def record_end_time_and_total_time_elapsed(self, operationName):
        self.end_time = datetime.utcnow()
        print(f'Finished {operationName} at {self.end_time}')
        print(f'Total time elapsed: {self.end_time - self.start_time}')

