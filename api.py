import requests
import json
import numpy as np
import time
import config

access_token = config.access_token

def get_log(channel_id, log_num):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "per_page": log_num
        }

    url = f"http://{config.server_url}/api/v4/channels/{channel_id}/posts"

    response = requests.get(url, params=params, headers=headers)
    return response.json()

def get_id(channel_id, message):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "page": 0,
        "per_page": 1
        }

    url = f"http://{config.server_url}/api/v4/channels/{channel_id}/posts"

    response = requests.get(url, params=params, headers=headers)
    index = np.argsort([v["create_at"] for v in response.json()["posts"].values()])

    data = response.json()

    while True:
        if message not in [v["message"] for v in data["posts"].values()]:
            time.sleep(1)
            response = requests.get(url, params=params, headers=headers)
            index = np.argsort([v["create_at"] for v in response.json()["posts"].values()])
            data = response.json()
        else:
            break         


    ids = [v["id"] for v in data["posts"].values()] 
    post_id = [ids[i] for i in index][-1]

    if data["posts"][post_id]["root_id"] == "":
        root_id = post_id
    else:
        root_id = data["posts"][post_id]["root_id"]

    return post_id, root_id

def get_thread(post_id, log_num):
    url = f"http://{config.server_url}/api/v4/posts/{post_id}/thread"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
        }

    json = {
        "id": post_id,
        "per_page": log_num
        }

    response = requests.get(url, params=json, headers=headers)
    return response.json()      

def create_post(channel_id, message, root_id=None):
    url = f"http://{config.server_url}/api/v4/posts"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
        }

    if root_id == None:
        json = {
            "channel_id": channel_id,
            "message": message
            }

    else:
        json = {
            "channel_id": channel_id,
            "message": message,
            "root_id": root_id
            }


    response = requests.post(url, json=json, headers=headers)

    return response.json()["id"]

def update_post(post_id, message):
    url = f"http://{config.server_url}/api/v4/posts/{post_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
        }

    json = {
        "id": post_id,
        "message": message
        }

    response = requests.put(url, json=json, headers=headers)
    return response.json()["id"]
    
def get_user_by_email(email):
    url = f"http://{config.server_url}/api/v4/users/email/{email}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
        }
        
    json = {
        "email": email,
        }
    
    response = requests.get(url, params=json, headers=headers)
    
    return response.json()["username"]
    
def get_cahnnel_by_name(team_name,channel_name):
    url = f"http://{config.server_url}/api/v4/teams/name/{team_name}/channels/name/{channel_name}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
        }
        
    json = {
        "team_name": team_name,
        "channel_name": channel_name
        }
    
    response = requests.get(url, params=json, headers=headers)

    return response.json()
    
    
def get_file(file_id, file_name, save_dir):
    url = f"http://{config.server_url}/api/v4/files/{file_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
        }
        
    json = {
        "file_id": file_id,
        }
    
    binary_file = requests.get(url, params=json, headers=headers).content
        
    file_path = f"{save_dir}/{file_name}"
    with open(file_path,"wb") as f:
        f.write(binary_file)

    return file_path