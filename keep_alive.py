from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    # Adding the 200 status code explicitly ensures the host sees a "Success"
    return "Bot is online!", 200 

def run():
    # 0.0.0.0 is required for the internet to see the app
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()