from queue import Queue as PythonQueue


class Queue(PythonQueue):

    def __init__(self, threads):
        super().__init__()
        self.completed_count = 0
        self.threads = threads

    def task_done(self):
        self.completed_count += 1
        super().task_done()

    def get_task_count(self):
        return self.completed_count

    @property
    def completed(self):
        return self.threads == self.completed_count
