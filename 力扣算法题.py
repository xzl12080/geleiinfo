def function_1(nums,target):
    for i in range(len(nums)):
        x = target - nums[i]
        for j in range(len(nums)):
            if x == nums[j]:
                return [i,j]

def function_2(l1,l2):
    def int_to_str(int_list):
        str_list = [str(num) for num in int_list]
        all_str = ''.join(str_list)
        return int(all_str)
    data = int_to_str(l1) + int_to_str(l2)
    data = [int(number) for number in str(data)]
    return data[::-1]


l1 = [2,4,3]
l2 = [5,6,4]
print(function_2(l1, l2))