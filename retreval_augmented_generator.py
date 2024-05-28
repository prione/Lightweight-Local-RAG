import os
import sys
import config
import numpy as np
import re
import pdb
from sentence_transformers import SentenceTransformer, util, CrossEncoder
import importlib
from nltk import flatten
import faiss
import json
import pickle


class handler():
    
    def __init__(self):
        self.emb = SentenceTransformer(config.emb_model)
        self.cross_encorder = CrossEncoder(config.cross_encoder_model, max_length=512)

        with open(f"{config.store_dir}/embedded_data.pkl", "rb") as f:
            embedded_data = pickle.load(f)
            self.index = embedded_data["index"]
            self.dictionary = embedded_data["dictionary"]


    def generate(self, user_input:str):
        importlib.reload(config)
        
        try:
    
            self.user_input = user_input

            similarities, indices = self.search_index([self.user_input])
            summary_dic = self.create_dictionary_for_summary(similarities, indices)
            references = ""

            if summary_dic:
                for doc_name, sentences in summary_dic.items():
                    for n, sentence in enumerate(sentences):
                        if not "|-|" in sentences[n]:
                            sentences[n] =f"```\n{sentences[n]}\n```"
                    
                    sentence = "\n".join(sentences)
                    references += f"\n- {doc_name}\n{sentence}"
                return ("rag_prompt", self.sum_prompt_generator(references), references)
 
            else:
                return ("chat_prompt", self.sum_prompt_generator(summary_dic))
                    
        except Exception as e:
            print(e)
            return ("error", f"エラーが発生しました。\n```{e}```")

        importlib.reload(config)

    def search_index(self, queries):
        query_embeddings = self.emb.encode(queries)
        similarities, indices = self.index.search(np.array(query_embeddings), 100)
        return similarities, indices
    

    def create_dictionary_for_summary(self, similarities, indices, top_k=config.emb_top_k):
        sentences = []
        sentences_to_summary = []
        doc_names = []
        summary_dic = {}
        
        for similarities_per_sentence, indices_per_sentence in zip(similarities, indices):
            for cosine_simmilary, i in zip(similarities_per_sentence, indices_per_sentence):
                if i != -1:
                    pkl_name = self.dictionary[str(i)]["file_name"]
                    doc_name = self.dictionary[str(i)]["doc_name"]
                    data_type = self.dictionary[str(i)]["data_type"]
                    list_index = self.dictionary[str(i)]["list_index"]
                    with open(f"{config.store_dir}/{pkl_name}.pkl", "rb") as f:
                        sentence = pickle.load(f)[data_type][list_index]
                    sentences.append(sentence)
                    doc_names.append(doc_name)
                
                
            ranks = self.cross_encorder.predict([(self.user_input, sentence) for sentence in sentences])
            data = [(s, d, r) for s, d, r in zip(sentences, doc_names, ranks)]
            data.sort(reverse=True, key=lambda x: x[-1])
            
            count = 0
            for sentence, doc_name, rank in data:
                if 50 < len(sentence):
                    if config.threshold < rank:
                        if doc_name not in summary_dic.keys():
                            summary_dic[doc_name] = [sentence]
                        else:
                            summary_dic[doc_name].append(sentence)
                        count += 1
                        
                if count == top_k:
                    break
                        
        return summary_dic


    def sum_prompt_generator(self, references):
        user_input = re.sub(r"[？?]", "", self.user_input)

        if references:
            return f"""質問に対して、文章に基づいた回答をしてください。

質問:
{user_input}

文章:
{references}
"""
        else:
            return self.user_input


if __name__ == "__main__":

    doc_handler = handler()

    print(doc_handler.generate(input("input: ")))
