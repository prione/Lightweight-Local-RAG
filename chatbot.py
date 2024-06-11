import os
import numpy as np
import time
from llama_cpp import Llama
import api
import config
# import interpreter
import retreval_augmented_generator
import importlib
import pdb

class bot():
    def __init__(self):
        
        self.llm = Llama(
            model_path = config.model,
            verbose = True,
            n_ctx = config.n_ctx,
        )            

        self.system_prompt = config.system_prompt
        self.history_num = config.n_history
        self.is_active = False
        self.rag = retreval_augmented_generator.handler()

    def token_counter(self, input):
        return len(self.llm.tokenize(input.encode("UTF-8")))

    def generate_prompt(self, messages):

        if "elyza" in config.model.lower():
            prompt = f"<s>[INST]<<SYS>>\n{self.system_prompt}\n<</SYS>>\n\n"    
            for who, post in messages:

               if who.lower() == "user":
                   prompt += f"{post} [/INST]" 

               elif who.lower() == "assistant":
                   prompt += f"{post}</s><s>[INST] "
        
        elif "calm" in config.model.lower():
            prompt = ""
            for who, post in messages:
                prompt += f"""\n{who}: {post}"""
            
            prompt += """\nASSISTANT:"""    

        elif "xwin" in config.model.lower():
            prompt = self.system_prompt
            
            for who, post in messages:
                prompt += f" {who}: {post}"
            
            prompt += " ASSISTANT:"     

        elif "gemma" in config.model.lower():
            prompt = "ステップバイステップで回答してください。\n"
            for who, post in messages:
                if who.lower() == "user":
                    prompt += f"<start_of_turn>user\n{post}<end_of_turn>\n"
                else:
                    prompt += f"<start_of_turn>model\n{post}<end_of_turn>\n"

            prompt += "<start_of_turn>model\n"     

        return prompt

    def chat(self, messages, channel_id, root_id, temperature, top_p, references=None):
        importlib.reload(config)
        
        post_id, ref = self.post_reference("bot", channel_id, root_id, references)
        prompt = self.generate_prompt(messages)

        while config.n_ctx <= self.token_counter(prompt):
            messages.pop(0)
            if len(messages) == 0:
                api.create_post(channel_id, "入力が長すぎます。\n\n```{references}```", root_id)
                return None
                
            prompt = self.generate_prompt(messages)
            
        # print("\n"+prompt)
        
        response = self.llm(
            prompt,
            temperature=temperature,
            top_p=top_p,
            top_k=config.top_k,
            max_tokens=config.max_tokens,
            repeat_penalty=config.repeat_penalty,
            stream = True,
            stop = ["</s>", "ASSISTANT", "USER", "<|endoftext|>", "### 指示", "### 入力", "<end_of_turn>"]
        )            

        stream_response = ""
        count = 0
        for chunk in response:
            message = chunk["choices"][0]
            if "text" in message:
                token = message["text"]
                stream_response += token
                count += 1
                
                if count == 3:
                    api.update_post(post_id, stream_response + ref)
                    count = 0

        api.update_post(post_id, stream_response + ref)
        
        return None


    def post_reference(self, mode, channel_id, root_id, references=None):
        ref = ""
        if references:
            ref = f"\n\n#### <参照ドキュメント>{references}"     
    
        if mode == "search":
            post_id = api.create_post(channel_id, ref, root_id)
        else:
            post_id = api.create_post(channel_id, "考え中..." + ref, root_id)

        return post_id, ref
        

    def run(self, q):
        while True:
            if q.qsize():
                self.is_active = True
                time.sleep(1)
                mode, data = q.get()
                channel_id = data["channel_id"]
                recent_post_id, root_id = api.get_id(channel_id, data["text"])
                
                try:
                    
                    if config.n_ctx <= self.token_counter(data["text"]):
                        api.create_post(channel_id, "入力が長すぎます。", root_id)

                    else:
                        
                        thread_data = api.get_thread(recent_post_id, self.history_num)
                        create_time = [int(v["create_at"]) for v in thread_data["posts"].values()]
                        chat_log = [v["message"] for v in thread_data["posts"].values()]
                        user_id = [v["user_id"] for v in thread_data["posts"].values()]
    
                        index = np.argsort(create_time)
                        chat_log = ["".join(chat_log[i].split("\n\n#### <参照ドキュメント>")[0]) for i in index]
                        user_id = [user_id[i] for i in index]
                        who = ["USER" if i != config.bot_id else "ASSISTANT" for i in user_id]

                        messages = [[w,c] for w,c in zip(who, chat_log) if c!=config.plz_wait_comment]
                        if who[-1] == "ASSISTANT":
                            messages.append(["USER",data["text"]])

                        if mode == "chat":

                            self.chat(messages, channel_id, root_id, config.rag_temperature, config.rag_top_p)

                        elif mode == "question":
                            rag_prompt = self.rag.generate(data["text"])

                            if rag_prompt[0] == "rag_prompt":
                                messages[-1][1] = rag_prompt[1]
                                references = rag_prompt[2]
                                self.chat(messages, channel_id, root_id, config.rag_temperature, config.rag_top_p, references)

                            elif rag_prompt[0] == "chat_prompt":
                                messages[-1][1] = rag_prompt[1]
                                self.chat(messages, channel_id, root_id, config.chat_temperature, config.chat_top_p)                            

                            elif rag_prompt[0] == "error":
                                api.api.create_post(channel_id, rag_prompt[1], root_id)                      
                                
                except Exception as e:
                    print(e)
                    api.create_post(channel_id, f"エラーが発生しました。\n```{e}```", root_id)
                    
            else:
                self.is_active = False
