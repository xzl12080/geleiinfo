x = -789
y = int(str(x)[0] + str(x)[:0:-1]) if x < 0 else int(str(x)[::-1])
print(y)

def foo(a_int, b_list, c_list):
    tmp = 1
    a_int += 1
    b_list.append(1)
    c_list.append(tmp)
    print(a_int, b_list, c_list)

a_int = 5
b_list = [5]
c_list = [5]
foo(a_int, b_list, c_list)
print(a_int, b_list, c_list)

import re

def get_word_count(sentence: str) -> int:
    return len([word for word in re.findall(r'\b\w+\b', sentence) if word])

sentence = "Hi,,,,,I’m,,,,a,ca t."
count = get_word_count(sentence)
print(count)

nested_list = [[2, 3], [5, 4], 6]
result = [num for sublist in nested_list for num in ([sublist] if isinstance(sublist, int) else sublist) if num % 2 == 0]
print(result)  # 输出 [2, 4, 6]


import time

def random_number() -> int:
    seed = int(str(time.time()).replace('.', ''))
    num = (seed * 1103515245 + 12345) % (2**31) % 100 + 1
    return num

from collections import Counter

def mysort(s: str) -> str:
    counter = Counter(s)
    sorted_items = sorted(counter.items(), key=lambda x: (x[1], x[0]))
    return ''.join([item[0] for item in sorted_items])

s = "adapbpaaa"
result = mysort(s)
print(result)  # 输出 "bdpa"

import re

import re

s = "iPhone 13 小明 998 拼多多"
pattern = r"[a-zA-Z0-9]+"
result = re.findall(pattern, s)

print(result)  # 输出 ["iPhone", "13", "998"]

from typing import List

class Solution:
    def findMinAbsValue(self, nums: List[int]) -> int:
        left = 0
        right = len(nums) - 1

        while left < right:
            mid = (left + right) // 2

            if abs(nums[mid]) < abs(nums[mid + 1]):
                right = mid
            else:
                left = mid + 1

        return nums[left]

# 示例输入
sorted_nums = [-10, -4, -2, 4, 8, 13]
result = Solution().findMinAbsValue(sorted_nums)
print(result)  # 输出：1

from typing import List

def min_cost_to_top(cost):
    k = len(cost)
    dp = [0] * (k + 1)

    for i in range(1, k + 1):
        if i == 1:
            dp[i] = cost[i-1]
        elif i == 2:
            dp[i] = cost[i-1] + dp[i-1]
        else:
            dp[i] = cost[i-1] + min(dp[i-1], dp[i-2], dp[i-3])

    return dp[k]

# 示例输入
cost = [1, 10, 5, 3, 8, 20, 25, 22, 100, 3]
result = min_cost_to_top(cost)
print(result)  # 输出：74

