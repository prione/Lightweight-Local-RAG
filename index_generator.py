import os
import sys
import config
import numpy as np
import re
import pdb
from sentence_transformers import SentenceTransformer, util
import importlib
from nltk import flatten
import faiss
import json
import pickle
import subprocess
import shutil
import spire.doc

class index_creater():

    def __init__(self):
        self.emb = SentenceTransformer(config.emb_model)
        
        if os.path.exists(f"{config.store_dir}/embedded_data.pkl"):
            with open(f"{config.store_dir}/embedded_data.pkl", "rb") as f:
                embedded_data = pickle.load(f)
                self.index = embedded_data["index"]
                self.dictionary = embedded_data["dictionary"]
            self.min_index = int(max(self.dictionary.keys()))       
            
        else: 
            dimension = self.emb.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatIP(dimension)
            self.dictionary = {}
            self.min_index = 0
            
    def run(self):

        total_file = 0
        for root, dirs, files in os.walk(config.docs_dir):
            total_file += len(files)

        count_file = 0
        
        if self.dictionary:
            analized_docs = np.unique([doc["doc_name"] for doc in self.dictionary.values()]).tolist()
            pkl_name = int(max([doc["file_name"] for doc in self.dictionary.values()])) + 1
        else:
            analized_docs = []
            pkl_name = 0
            
        for root, dirs, files in os.walk(config.docs_dir):
            for file_name in files:
                if not file_name in analized_docs and not "~$" in file_name:
                    try:
                        docs = self.load_docs(f"{root}/{file_name}", file_name)
                        if docs:
                            self.create_docstore(pkl_name, file_name, docs)
                            self.embed_doc(file_name, docs)
                            pkl_name += 1
                                
                            if pkl_name % 100 == 0:
                                self.save_embedded_data()

                    except Exception as e:
                        print(e)
                        pass
                    
                count_file += 1
                print(f"\r{count_file}/{total_file} is complete.", end="")
                      
        self.save_embedded_data()
          
          
    def load_docs(self, file_path, file_name):
        extension = os.path.basename(file_path).split(".")[-1]
        
        if extension.lower() == "docx":
            subprocess.run(f" pandoc -s '{file_path}' -o '{config.store_dir}/{file_name}.md' -t markdown_strict", shell=True)
            texts, tables = self.split_doc(f"{config.store_dir}/{file_name}.md")
            os.remove(f"{config.store_dir}/{file_name}.md")
            docs = {"texts": texts, "tables": tables}

        elif extension.lower() == "doc":
            filename_no_extention = ".".join(os.path.basename(file_path).split(".")[:-1])
            
            document = spire.doc.Document()
            document.LoadFromFile(file_path)
            document.SaveToFile(f"{config.store_dir}/{filename_no_extention}.docx")
            
            subprocess.run(f"pandoc -s '{config.store_dir}/{filename_no_extention}.docx' -o '{config.store_dir}/{filename_no_extention}.md' -t markdown_strict", shell=True)
            texts, tables = self.split_doc(f"{config.store_dir}/{filename_no_extention}.md")
            
            os.remove(f"{config.store_dir}/{filename_no_extention}.md")
            os.remove(f"{config.store_dir}/{filename_no_extention}.docx")
            docs = {"texts": texts, "tables": tables}
            
        elif extension.lower() == "txt":
            with open(file_path, "r") as f:
                texts = [f.read()]
            tables = []
            docs = {"texts": texts, "tables": tables}
       
        else: 
            docs = {}
        
        return docs
        
        
    def create_docstore(self, pkl_name, doc_name, docs):
    
        if docs["texts"]:
            for list_index, i in enumerate(range(self.min_index, self.min_index+len(docs["texts"]))):
                self.dictionary[str(i)] = {"file_name": pkl_name, "doc_name": doc_name, "data_type": "texts", "list_index": list_index}
            self.min_index += len(docs["texts"])

        if docs["tables"]:    
            for list_index, i in enumerate(range(self.min_index, self.min_index+len(docs["tables"]))):
                self.dictionary[str(i)] = {"file_name": pkl_name, "doc_name": doc_name, "data_type": "tables", "list_index": list_index}
            self.min_index += len(docs["tables"])

        with open(f"{config.store_dir}/{pkl_name}.pkl" ,"wb") as f:
            pickle.dump(docs, f)


    def embed_doc(self, doc_name, docs):
        if docs["texts"]:
            for n, text in enumerate(docs["texts"]):
                docs["texts"][n] = f"ファイル名: {doc_name}" + "\n" + text     
                
            embeddings = self.emb.encode(docs["texts"])
            self.index.add(embeddings)

        if docs["tables"]:    
            for n, table in enumerate(docs["tables"]):
                docs["tables"][n] = f"ファイル名: {doc_name}" + "\n" + table
                
            embeddings = self.emb.encode(docs["tables"])
            self.index.add(embeddings)
        

    def save_embedded_data(self):
        with open(f"{config.store_dir}/embedded_data.pkl", "wb") as f:
            embedded_data = {"index": self.index, "dictionary": self.dictionary} 
            pickle.dump(embedded_data, f)
            

    def split_doc(self, file_name):
        with open(file_name, "r") as f:
            lines = f.readlines()
        tab_detete = str.maketrans({v: " " for v in ["\u3000", "　", "\x0c", "\x0b", "\t"]})
        lines = [l.translate(tab_detete) for l in lines]

        texts = ""
        tables = []

        is_table = False
        is_component = False
        
        for l in lines:
        
            if not is_table and "<table" in l:
                is_table = True
                table = {"thead": "", "separator": "", "body": []}

            if not is_table and "<img" not in l:
                texts += l               

            if is_table:
                if "<tr" in l:
                    is_component = True
                    component = ""

                if is_component:            
                    if "</tr>" in l:
                        is_component = False

                        if "<th>" in component:
                            table["thead"] = "|" + "|".join(re.findall(r'<th>(.*?)</th>', component, flags=re.DOTALL)) + "|"

                        if "<td>" in component:
                            if table["thead"]:
                                table["body"].append("\n|" + "|".join(re.findall(r'<td>(.*?)</td>', component, flags=re.DOTALL)) + "|")
                                
                            else:
                                table["thead"] = "|" + "|".join(re.findall(r'<td>(.*?)</td>', component, flags=re.DOTALL)) + "|"
                        
                        table["separator"] = "\n" + (table["thead"].count("|") - 1) * "|-" + "|"
                    else:
                        component += l.replace("\n", " ").replace("<p>", " ").replace("</p>", " ").replace("<br />", " ").replace("<br>", " ").replace("<blockquote>", " ").replace("</blockquote>", " ")

                if "</table>" in l:
                    is_table = False
                    tables.append(table)

        texts = self.split_text([texts])
        tables = self.split_table(tables)

        return texts, tables


    def split_text(self, texts):

        def __adjust_text(texts_list):
            if type(texts_list) == list and len(texts_list) > 1:
                n = 0
                while True:
                        
                    if len(texts_list[n]) + len(texts_list[n+1]) < config.text_split_length:
                        texts_list[n] += texts_list.pop(n+1)
                        n = 0
                    else:
                        n+=1
                        
                    if n == len(texts_list)-1:
                    
                        break                           
                        
            return texts_list
            
          
        if type(texts) == list:
            texts = "\n\n".join(texts)

        splited_texts = texts.split("\n\n")
        splited_texts = __adjust_text(splited_texts)

        for n in range(len(splited_texts)):
            if len(splited_texts[n]) >= config.text_split_length:
                splited_texts[n] = __adjust_text(splited_texts[n].split("\n"))
               
        splited_texts = flatten(splited_texts)
        
        for n in range(len(splited_texts)):
            if len(splited_texts[n]) >= config.text_split_length:
                splited_texts[n] = __adjust_text(re.findall("[^。！？!?]+[。！？!?]?", splited_texts[n]))

        splited_texts = flatten(splited_texts)

        return splited_texts


    def split_table(self, tables):

        splited_tables = []
        for table in tables:
            while table["body"]:

                content = table["thead"] + table["separator"] + table["body"].pop(0)
                while table["body"] and (len(content) + len(table["body"][0]) < config.text_split_length):
                    content += table["body"].pop(0)
                
                splited_tables.append(content)        
                    
        return splited_tables


    def read_excel(self, file):
        

if __name__ == "__main__":
    creater = index_creater()
    creater.run()
