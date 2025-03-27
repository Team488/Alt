from time import localtime, strftime


def getTimeStr():
    return strftime("%Y-%m-%d_%H-%M-%S", localtime())
