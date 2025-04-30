

def test_get_local_ip():
    from Alt.Core.Utils.timeFmt import getTimeStr
    import time
    print(getTimeStr())
    print("\n\n")
    print(getTimeStr(time.localtime(12345)))
