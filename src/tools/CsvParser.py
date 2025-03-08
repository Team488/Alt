from typing import List, Tuple, Optional

class CsvParser:
    """Reads in a csv file and extracts the keys provided into a dict"""

    def __init__(
        self, csvLocation: str, minTimestepS: float, csvKeys: list[str]
    ) -> None:
        self.keys = csvKeys
        union = self.__calculateUnion(csvKeys)
        self.values: List[List[Tuple[float, str]]] = self.__parseCsvIntoGroups(
            csvLocation, union, minTimestepS, csvKeys
        )

    def __calculateUnion(self, csvKeys: list[str]) -> str:
        if not csvKeys:
            return ""

        union = ""
        minLen = len(min(csvKeys, key=len))

        for i in range(minLen):
            commonChar = csvKeys[0][i]
            for key in csvKeys[1:]:
                if commonChar != " " and key[i] != commonChar:
                    return union
            union += key[i]
        return union

    def __parseCsvIntoGroups(
        self, csvLocation: str, union: str, minTimestepS: float, csvKeys: list[str]
    ) -> List[List[Tuple[float, str]]]:
        lastTimeStamps = [-1.0] * len(csvKeys)
        values: List[List[Tuple[float, str]]] = [[] for _ in range(len(csvKeys))]
        csvLens = [len(k) for k in csvKeys]
        unionLen = len(union)
        with open(csvLocation, "r") as file:
            # Read each line in the file
            for line in file:
                # Strip leading/trailing whitespace
                line = line.strip()

                if not line:  # Skip empty lines
                    continue

                split = line.split(",")
                try:
                    value = split[2]
                    key = split[1]
                    keyLen = len(key)
                    # Ensure key length matches and check for the target
                    if union == "" or (keyLen >= unionLen and key[0:unionLen] == union):
                        # contains union so now check specifics
                        timeStamp = float(split[0])
                        for i in range(len(csvKeys)):
                            # iterate over each key to see if there is a match
                            if keyLen >= csvLens[i] and key == csvKeys[i]:
                                timeDiff = timeStamp - lastTimeStamps[i]
                                if timeDiff >= minTimestepS:
                                    # add value
                                    lastTimeStamps[i] = timeStamp
                                    values[i].append((timeStamp, value))
                                    break
                except:
                    pass
        return values

    def removeZeroEntriesAtStart(self) -> None:
        for i in range(len(self.keys)):
            values = self.values[i]
            for j in range(len(values)):
                if values[j][1] == 0:
                    values.remove(values[j])
                else:
                    break

    def getNearestValues(self, timeSeconds: float) -> list[tuple[str, tuple[float, str]]]:
        ret: List[Tuple[str, Tuple[float, str]]] = []
        for i in range(len(self.keys)):
            keyName = self.keys[i]
            nearest = self.__getNearestValue(timeSeconds, self.values[i])
            ret.append((keyName, nearest))
        return ret

    def __getNearestValue(
        self, timeSeconds: float, values: list[tuple[float, str]]
    ) -> tuple[float, str]:
        nearest: Optional[tuple[float, str]] = None
        diff = 100000.0
        for entry in values:
            timeStamp = entry[0]
            newDiff = abs(timeSeconds - timeStamp)
            if newDiff < diff:
                nearest = entry
                diff = newDiff
        # Return a default if nearest is None
        return nearest if nearest is not None else (0.0, "")

    """ Absolute max timestamp value in the data"""

    def getMaxTimeStamp(self) -> float:
        maxValue = 0.0
        for i in range(len(self.keys)):
            maxTimeStamp = self.__getMaxTimeStamp(self.values[i])
            maxValue = max(maxValue, maxTimeStamp)
        return maxValue

    def __getMaxTimeStamp(self, values: list[tuple[float, str]]) -> float:
        maxTimeStamp = 0.0
        for entry in values:
            timeStamp = entry[0]
            maxTimeStamp = max(timeStamp, maxTimeStamp)
        return maxTimeStamp

    """ Absolute min timestamp value in the data"""

    def getMinTimeStamp(self) -> float:
        minValue = 0.0
        for i in range(len(self.keys)):
            minTimeStamp = self.__getMinTimeStamp(self.values[i])
            minValue = min(minValue, minTimeStamp)
        return minValue

    def __getMinTimeStamp(self, values: list[tuple[float, str]]) -> float:
        minTimeStamp = 0.0
        for entry in values:
            timeStamp = entry[0]
            minTimeStamp = min(timeStamp, minTimeStamp)
        return minTimeStamp
