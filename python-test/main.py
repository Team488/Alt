import probmap
import random
import traceback

def main():
    fieldMap = probmap.ProbMap(1000, 500, 5)
    fieldMap.display_map()
    for i in range(100):
        # fieldMap.add_detection(300, 150, 250, 250, 0.5)
        test_randomization_ranges(fieldMap, fieldMap.get_shape()[0], fieldMap.get_shape()[1])
        fieldMap.display_map()
        # fieldMap.clear_map()
        

# randomizes values for stress testing algorithm

def test_randomization_ranges(map, width, height):
    for i in range(1):
        x = random.randrange(0, width)
        y = random.randrange(0, height)
        obj_size = random.randrange(299, 300) 
        confidence = random.randrange(70, 100, 1)/100 # generates a confidence threshold between 0.7 - 1.0
        try:
            map.add_detection(x, y, obj_size, obj_size, confidence)
        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    main()
    
    
