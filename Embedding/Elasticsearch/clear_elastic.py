from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200")
index_name = "articles"

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"Index '{index_name}' removed.")
else:
    print(f"Index '{index_name}' is not.")