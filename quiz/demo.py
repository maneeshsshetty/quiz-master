#fibo
'''
fibo1 =0
fibo2=1
newfibo=0
print(fibo1)
print(fibo2)
for i in range(10):
    newfibo =fibo1+fibo2
    print(newfibo)
    fibo1=fibo2
    fibo2=newfibo
'''
#fibo with recursion
'''
n=int(input("enter a number"))   
print(0)
print(1)

count=2
def fibon(prev1,prev2):
    global count
    if count<n:
        newfibo =prev1+prev2
        print(newfibo)
        count+=1
        prev1=prev2
        prev2=newfibo
        fibon(prev1,prev2)
fibon(0,1)
'''
#bubble sort
'''
my_arr=[3,5,1,2,9,4,0]
n=len(my_arr)
for i in range(n-1):
    for j in range(n-i-1):
         if my_arr[j]>my_arr[j+1]:
             my_arr[j],my_arr[j+1]=my_arr[j+1],my_arr[j]
print(my_arr)
'''
'''
my_arr=[3,5,1,2,9,4,0]
n=len(my_arr)
for i in range(n-1):
    minval=i
    for j in range(i+1,n):
         if my_arr[j] < my_arr[minval]:
             minval=j
    min_value=my_arr.pop(minval)
    my_arr.insert(i,min_value)
print("sorted array :",my_arr)
'''
