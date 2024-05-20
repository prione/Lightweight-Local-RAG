from flask import Flask, request, g, jsonify
from threading import Thread
from queue import Queue
from chatbot import bot
import api
import config

bot = bot()

q = Queue()
thread_bot = Thread(target=bot.run, args=(q,), daemon=True)
thread_bot.start()

app = Flask("matterbot")

def post_wait(bool, data):

    if bool:
        # api.create_post(data["channel_id"], config.plz_wait_comment)
        channel_id = data["channel_id"]
        recent_post_id, root_id = api.get_id(channel_id, data["text"])
        api.create_post(channel_id, config.plz_wait_comment, root_id)

@app.route("/chat", methods=["POST"])
def get_chat():

    data = request.form 
      
    post_wait(bot.is_active, data)

    if data["command"] == "/test":
        q.put(["test",data])
    
    elif data["command"] == "/bot":
        q.put(["bot",data])
    
    elif data["command"] == "/s":
        q.put(["search",data])
    
    
    return jsonify({"response_type": "in_channel", "text": data["text"]})
   
app.run(host="0.0.0.0", port=8000)