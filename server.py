import argparse
import json
import re
import socket
from collections import Counter
from queue import Queue
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup


class Worker(Thread):
    def __init__(self, general_master, worker_id):
        super().__init__()
        self.master = general_master
        self.worker_id = worker_id
        self.task_queue = general_master.task_queue
        self.lock = Lock()

    def run(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            url, client_socket = task
            try:
                needed_url = re.search(r'GET (.*?) HTTP', url).group(1)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/58.0.3029.110 Safari/537.36'}
                response = requests.get(needed_url, headers=headers, timeout=5)
                clean_html = BeautifulSoup(
                    response.content.decode('utf-8', 'ignore'),
                    "html.parser"
                ).text
                words = re.split(r'[\s.,;:]+', clean_html.lower())
                top_words = (Counter(word for word in words if word.isalpha())
                             .most_common(self.master.top_k))
                result = dict(top_words)
                result_json = json.dumps(result, ensure_ascii=False).encode()
                client_socket.sendall(result_json)
                client_socket.close()

                with self.master.lock:
                    self.master.processed_urls += 1
                    print(f"Processed by Worker {self.worker_id}: {self.master.processed_urls}")
            except (requests.exceptions.RequestException, socket.error) as exception:
                print(f"An error occurred while processing request: {exception}")

    def process_task(self, task):
        self.task_queue.put(task)


class Master:
    def __init__(self, num_workers, host, port, top_k):
        self.num_workers = num_workers
        self.host = host
        self.port = port
        self.top_k = top_k
        self.workers = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.task_queue = Queue()
        self.processed_urls = 0
        self.lock = Lock()

    def run(self):
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            for _ in range(self.num_workers):
                worker = Worker(self, _ + 1)
                self.workers.append(worker)
                executor.submit(worker.run)

            print(f"Server started on {self.host}:{self.port}")
            print(f"Number of workers: {self.num_workers}")
            print(f"Top {self.top_k} words will be counted\n")

            while True:
                client_socket, _ = self.socket.accept()
                request = client_socket.recv(1024).decode('utf-8')
                self.task_queue.put((request, client_socket))

            self.task_queue.join()
            for _ in range(self.num_workers):
                self.task_queue.put(None)

        self.socket.close()
        print("\nServer stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--num_workers", type=int, default=1,
                        help="number of worker threads (default: 1)")
    parser.add_argument("-k", "--top_k", type=int, default=10,
                        help="number of top words to return (default: 10)")
    args = parser.parse_args()

    master = Master(
        num_workers=args.num_workers,
        host='localhost',
        port=8080,
        top_k=args.top_k
    )
    master.run()