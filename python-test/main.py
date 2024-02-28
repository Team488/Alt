import probmap

fieldMap = probmap.ProbMap(2000, 1000, 5)
fieldMap.display_map()
fieldMap.add_detection(300, 150, 450, 450, 0.5)
fieldMap.display_map()