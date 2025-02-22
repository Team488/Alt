from tools.Constants import ATLocations, ReefBranches


class ReefState:
    def __init__(self):
        self.reefMap = self.__createReefMap()

    def __createReefMap(self):
        map = {}
        for reef_id in ATLocations.getReefBasedIds():
            map[reef_id] = self.__createBranchMap()

        return map

    def __createBranchMap(self):
        branchMap = {}
        for branch in ReefBranches:
            branchMap[branch.branchid] = 0
        return branchMap
