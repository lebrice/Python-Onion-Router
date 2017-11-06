#!/usr/bin/python3

from queue import Queue

class ClosableQueue(Queue):
    """
    Queue subclass that can be closed. By closing the Queue,
    the threads that are consuming its output are stopped.
    """
    SENTINEL = object()

    def __init__(self, maxsize=0):
        super().__init__(maxsize)
        self.closed = False

    def close(self):
        if self.closed:
            raise RuntimeError("Queue Already Closed.")
        else:
            self.put(self.SENTINEL)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.SENTINEL:
                    return  # Cause the thread to exit.
                yield item
            finally:
                self.task_done()

    def __enter__(self):
        pass

    def __exit__(self, *exc):
        self.close()
