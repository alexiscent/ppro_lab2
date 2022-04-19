from queue import Queue
from threading import Condition, Thread
from time import sleep, strftime

class FutureResult:
    def __init__(self):
        self.hasResult = False
        self.lock = Condition()

    def setResult(self, result):
        with self.lock:
            self.res = result
            self.hasResult = True
            self.lock.notify()

    def result(self):
        with self.lock:
            if not self.hasResult:
                self.lock.wait()
            return self.res


class WorkItem:
    def __init__(self, func, arg):
        self.func = func
        self.arg = arg
        self.future = FutureResult()


class WorkerThread(Thread):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def run(self):
        while True:
            if self.queue.empty():
                return
            item = self.queue.get()
            res = item.func(item.arg)
            item.future.setResult(res)


class CustomExecutor:
    def __init__(self, max_workers=1):
        self.queue = Queue()
        self.max_workers = max(max_workers, 1)
        self.workers = []

    def execute(self, func, args):
        item = WorkItem(func, args)
        self.queue.put(item)
        self.workers = [WorkerThread(self.queue)]
        self.workers[0].start()
        return item.future

    def map(self, func, args_array):
        items = [WorkItem(func, arg) for arg in args_array]
        [self.queue.put(i) for i in items]
        self.workers = [WorkerThread(self.queue) for i in range(self.max_workers)]
        [w.start() for w in self.workers]
        return [i.future for i in items]

    def shutdown(self):
        for w in self.workers:
            w.join()



def longRunningTask(x):
    sleep(2)
    return x * 2

if __name__ == '__main__':
    executor = CustomExecutor(max_workers=2)
    futures = executor.map(longRunningTask, [1, 2, 3, 4])
    for f in futures:
        print(strftime('%H:%M:%S') + ' - ' + str(f.result()))