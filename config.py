model = "./models/gemma-2b-it.Q8_0.gguf" # Model path for LLM

# Chatbot config
system_prompt = "以下は文脈のある入力と指示に基づいた会話です。入力の要求を適切に満たす回答を書きなさい。"
plz_wait_comment = "ただいま別ユーザが使用中です。しばらくお待ちください。"

chat_temperature=0.5 # Temprature parameter to LLM with no reference text from RAG
chat_top_p=0.6
top_k=50
max_tokens=1100
repeat_penalty=1.0
n_ctx=2048
n_history = 10 # Maximum number of chat histories to read from a thread

# rag config
rag_temperature = 0 # Temprature parameter to LLM with reference text from RAG
rag_top_p = 0.6
cross_encoder_model = "./models/japanese-reranker-cross-encoder-xsmall-v1" # Model path for reranker 
emb_model = "./models/multilingual-e5-small" # Model path for embedding
emb_top_k = 5
threshold = 0.5
text_split_length = 200 # Maximum sentence length for embedding
docs_dir = "./docs" # Root path of the document to use for RAG (also searches subdirectories and below)
store_dir = "./data" # indexed document data storage path

# Slack, mattermost config 
server_url = "your-slack/mattermost-url.com" # your slack/mattermost server url
bot_id = "xxxxxxxxxxxxxxxxxxx" # ID to assign to chatbots on slack or mattermost
access_token = "xxxxxxxxxxxxxxxxxxx" # Bearer authentication token