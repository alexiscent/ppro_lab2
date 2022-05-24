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
            item = self.queue.get()
            if not item: return
            res = item.func(item.arg)
            item.future.setResult(res)


class CustomExecutor:
    def __init__(self, max_workers=1):
        self.queue = Queue()
        self.workers = []
        for _ in range(max(max_workers, 1)):
            self.workers.append(WorkerThread(self.queue))
            self.workers[-1].start()

    def execute(self, func, args):
        item = WorkItem(func, args)
        self.queue.put(item)
        return item.future

    def map(self, func, args_array):
        items = []
        for arg in args_array:
            items.append(WorkItem(func, arg))
            self.queue.put(items[-1])
        return [i.future for i in items]

    def shutdown(self):
        for _ in self.workers:
            self.queue.put(None)
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
    executor.shutdown()
