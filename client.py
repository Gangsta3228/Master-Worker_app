import argparse
import socket
from concurrent.futures import ThreadPoolExecutor


def send_request(url):
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("localhost", 8080))
        request = f"GET {url} HTTP/1.1\r\nHost: localhost\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
        conn.send(request.encode('utf-8'))

        response = b""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            response += data

        print(f"{url}: {response.decode('utf-8')}")

        conn.close()
    except (socket.error, ConnectionRefusedError) as exception:
        print(f"An error occurred while sending request to the server: {exception}")
    finally:
        conn.close()

def main(num_threads, file_name):
    with open(file_name, encoding='utf-8') as file:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for line in file:
                url = line.strip()
                executor.submit(send_request, url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("num_threads", type=int, help="Number of threads to use")
    parser.add_argument("file_name", type=str, help="File containing URLs")
    args = parser.parse_args()

    main(args.num_threads, args.file_name)