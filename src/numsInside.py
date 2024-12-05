import time
seen = {}
num = 10
insides = [1,2]
ct = 0
def numsInside(num):
    global ct
    if num < 0: return 0
    if num == 0: return 1
    
    s = seen.get(num)
    if s:
        print(f"{ct=}")
        ct+=1
        return s

    validInsides = [numI for numI in insides if numI <= num]
    numInside = 0
    for numI in validInsides:
        rec = numsInside(num-numI)
        seen[num-numI] = rec
        numInside+=rec
        
    return numInside

start = time.time()
print(numsInside(num))
end = time.time()

print(f"Time elapsed: {(end-start)*1000:.6f}MS")
