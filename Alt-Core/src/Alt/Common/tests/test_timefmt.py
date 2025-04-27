

def test_get_local_ip():
    from ..timeFmt import getTimeStr
    import time
    print(getTimeStr())
    print("\n\n")
    print(getTimeStr(time.localtime(12345)))
