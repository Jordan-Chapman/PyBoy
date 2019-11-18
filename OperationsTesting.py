# Author: Jordan Chapman
# Testing module for operation speeds
import time


def overflow_bin(c):
    t = time.time()
    for i in range(c):
        if i >= 0x100:
            x = i & 0xff
    return time.time() - t


def overflow_int(c):
    t = time.time()
    for i in range(c):
        if i >= 0x100:
            x = i % 0x100
    return time.time() - t


print(overflow_int(10000000))
print(overflow_bin(10000000))
print(overflow_int(10000000))