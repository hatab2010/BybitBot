from threading import Timer

def callback():
    print("TRIGGER")


timer = Timer(3, callback)
timer.start()