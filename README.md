```
Embedding/                          # Main project folder
├── get-query.py                    # Loading articles from rag-datasets/rag-mini-bioasq dataset
├── main.py                         # Basic script for creating embeddings for uploaded articles
├── merged_articles.json            # JSON file where articles were uploaded
├── time.txt                        # A file for recording the results of article loading times in different databases
│
├── Elasticsearch/               
│   ├── clear_elastic.py           # Cleaning data in Elasticsearch
│   ├── docker-compose.yml         # Creating a container for Elasticsearch
│   ├── elastic.py                 # Basic logic of uploading articles to Elasticsearch
│   └── find.py                    # Search script for Elasticsearch
│
├── milvus/                       
│   ├── clear.py                   # Cleaning data in Milvus
│   ├── docker-compose.yml         # Creating a container for Milvus
│   ├── find.py                    # Search script for Milvus
│   └── milvus.py                  # Basic logic for uploading articles to Milvus
│
├── Weaviate/                      
│   ├── clear.py                   # Cleaning data in Weaviate
│   ├── docker-compose.yml         # Creating a container for Weaviate
│   ├── find.py                    # Search script for Weaviate
│   └── weavite.py                 # Basic logic for uploading articles to Weaviate
```
