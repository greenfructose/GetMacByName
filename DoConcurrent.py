import concurrent.futures
import csv
import time
from pprint import pprint
from main import write_mac_tables


def multithread():
    ips = []
    with open('SwitchAddresses.csv', 'r') as f:
        for row in csv.reader(f):
            ips.append(row[0])
    with concurrent.futures.ThreadPoolExecutor() as executor:
        start = time.perf_counter()
        response_process = []
        for ip in ips:
            response_process.append(executor.submit(write_mac_tables, ip))
        print(f'Duration: {time.perf_counter() - start}')
        for f in response_process[0:]:
            pprint(f.result())


if __name__ == '__main__':
    multithread()
