# Lightweight-Local-RAG
完全なオフライン、CPUのみの非力な環境で動作するRAGを搭載したチャットボットです。

Slack,mattermostのインタフェースを想定した実装です。

# Feature
- 完全オフライン, ノートPCのCPUのみで動作
- RAGはWord(文章と表どちらも認識), Textの形式に対応
- LLMはストリームレスポンスで応答し, RAGに使われた根拠も提示
- チャットボットへの入力コンテクストはスレッド単位で管理

# Requirements
### 環境
- Ubuntu (WSL) 

### モデル
- 任意のLLMモデルGGUFファイル (gemma-2b-it.Q8_0) を推奨
- 任意のEmbbedingモデル (multilingual-e5-small) を推奨
- 任意のリランキングモデル (japanese-reranker-cross-encoder-xsmall-v1) を推奨
  
### ライブラリ
```
pip install numpy request llama-cpp-python sentence_transformers nltk faiss Spire.Doc flask 
```

# Setup
- config.py を参照

# Usage
0. 事前にRAGに使用したいドキュメントを配置し, index_generator.py を実行

1. main.pyを起動

2. Slackやmattermost上でスラッシュコマンド(デフォルトでは /chatや/question)を文頭につけてチャット

<img src=https://github.com/prione/Lightweight-Local-RAG/assets/92021420/a0b10b24-efdd-4671-8a8c-05f83091866c width="40%" />
