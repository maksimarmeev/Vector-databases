import json
import torch
import time
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import normalize
from datasets import load_dataset


def format_time(total_time):
    minutes = int(total_time // 60) 
    seconds = int(total_time % 60)  
    milliseconds = int((total_time - int(total_time)) * 1000)  
    if milliseconds >= 1000:
        seconds += milliseconds // 1000
        milliseconds = milliseconds % 1000

    return minutes, seconds, milliseconds

def get_embeddings(text, model, tokenizer):
    inputs = tokenizer(text,  return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return embeddings


model_name = "thenlper/gte-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
file_path = r"D:\Embedding\merged_articles.json"
with open(file_path, "r", encoding="utf-8") as f:
    articles = json.load(f)
start_time = time.time()
for article in articles:
    text = article.get("text", "")
    if text and "embedding" not in article:
        article["embedding"] = get_embeddings(text, model, tokenizer).tolist()
        article_id = article["pmid"]
        print(f"Embedding added to article {article_id}")
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=4)
end_time = time.time()
total_time = end_time - start_time
minutes, seconds, milliseconds = format_time(total_time)
print(f"Embeddings were created in {minutes} minutes {seconds} seconds {milliseconds} milliseconds.")