import datetime

def log(message):
    print("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] " + message)
