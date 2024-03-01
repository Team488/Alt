import probmap
import random

def main():
    fieldMap = probmap.ProbMap(2000, 1000, 5)
    fieldMap.display_map()
    fieldMap.add_detection(300, 150, 450, 450, 0.5)
    fieldMap.display_map()    
    
    # test_randomization_ranges(488)


# randomizes values for stress testing algorithm
def test_randomization_ranges(seed):
    random.seed(seed)

    fieldMap = probmap.ProbMap(2000, 1000, 5)
    fieldMap.display_map()
    obj_size = 1
    failedsizes = []
    for i in range(300):
        x = random.randrange(0, 2000)
        y = random.randrange(0, 1000)
        # obj_size = random.randrange(100, 200)
        confidence = random.randrange(50, 100, 1)/100
        obj_size += 1
        print(x, y, obj_size, confidence)
        fieldMap.add_detection(x, y, obj_size, obj_size, confidence)

        # try:
            # fieldMap.add_detection(x, y, obj_size, obj_size, confidence)
        # except:
            # failedsizes.append(obj_size)
    fieldMap.display_map()
    print(failedsizes)
    
    
if __name__ == "__main__":
    main()
    
    