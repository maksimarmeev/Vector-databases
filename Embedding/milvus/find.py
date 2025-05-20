import time
from pymilvus import connections, Collection, utility
import matplotlib.pyplot as plt
import threading
import torch
import pandas as pd
import docker
from transformers import AutoModel, AutoTokenizer
from datasets import load_dataset
import ast
import numpy as np

def format_time(total_time):
    minutes = int(total_time // 60) 
    seconds = int(total_time % 60)  
    milliseconds = int((total_time - int(total_time)) * 1000)  
    if milliseconds >= 1000:
        seconds += milliseconds // 1000
        milliseconds = milliseconds % 1000

    return minutes, seconds, milliseconds
def get_embeddings(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return embeddings
def get_container_metrics(container):
    stats = container.stats(stream=False)
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
    cpu_usage = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100 if system_delta > 0 else 0
    memory_usage = stats["memory_stats"]["usage"] / (1024 * 1024) 
    return cpu_usage, memory_usage
model_name = "thenlper/gte-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
dataset = load_dataset("rag-datasets/rag-mini-bioasq", "question-answer-passages")['test']
questions = dataset["question"]
relevant_passages_list = dataset["relevant_passage_ids"]

client = connections.connect("default", host="localhost", port="19530")
index_name = "articles"
if not utility.has_collection(index_name):
    raise Exception(f"Collection '{index_name}' does not exist.")

collection = Collection(name=index_name)
if collection.has_index():
    collection.release()
    collection.drop_index()
if not collection.has_index():
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "IP",  
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
collection.load()

search_params = {
    "metric_type": "IP",
    "params": {"nprobe": 16}
}
client_docker = docker.from_env()
container_name = "milvus-standalone"
container = client_docker.containers.get(container_name)
results_list = []
timestamps = []
cpu_usages = []
memory_usages = []
data_lock = threading.Lock()
stop_metrics = False
def collect_metrics():
    while not stop_metrics:
        with data_lock: 
            timestamps.append(time.time()) 
            cpu_usage, memory_usage = get_container_metrics(container)
            cpu_usages.append(cpu_usage)
            memory_usages.append(memory_usage) 
        time.sleep(10) 

metrics_thread = threading.Thread(target=collect_metrics)
metrics_thread.daemon = True  
metrics_thread.start()

search_start_time = time.time()
intervals = list(range(100, 1001, 100))
all_presnost = {k: [] for k in intervals}
all_navratnost = {k: [] for k in intervals}

for i, (question, relevant_passages_raw) in enumerate(zip(questions, relevant_passages_list), start=1):
    embed_start = time.time()
    query_embedding = get_embeddings(question, model, tokenizer)
    embed_end = time.time()
    embed_time = embed_end - embed_start


    search_start = time.time()
    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=1000
    )
    search_end = time.time()
    search_time = search_end - search_start
    relevant_passages = ast.literal_eval(relevant_passages_raw)
    relevant_passages = [str(id) for id in relevant_passages]
    found_articles = [hit.id for hit in list(results[0])] 
    relevant_positions = {}
    for rel_article in relevant_passages:
        if rel_article in found_articles:
            position = found_articles.index(rel_article) + 1
            relevant_positions[rel_article] = position
    result_str = [f"{article_id} ({position})" for article_id, position in relevant_positions.items()]
    if relevant_positions:
        max_position = max(relevant_positions.values())
    results_list.append([
        i,
        question,
        ", ".join(result_str),
        embed_time,
        search_time,
        max_position
    ])
    for k in intervals:
        top_k = found_articles[:k]
        relevant_in_k = sum(1 for article in top_k if article in relevant_passages)
        precision = relevant_in_k/ k if k > 0 else 0
        navratnost = relevant_in_k / len(relevant_passages) if relevant_passages else 0
        all_presnost[k].append(precision)
        all_navratnost[k].append(navratnost)
    print(f"Number {i} search for question {question}")    
    print("------")
search_end_time = time.time()
avg_precision = {k: sum(all_presnost[k])/len(all_presnost[k]) for k in intervals}
avg_recall = {k: sum(all_navratnost[k])/len(all_navratnost[k]) for k in intervals}
std_precision = {k: np.std(all_presnost[k]) for k in intervals}
std_recall = {k: np.std(all_navratnost[k]) for k in intervals}
stop_metrics = True 
metrics_thread.join(timeout=1)
with data_lock:
    if len(timestamps) != len(cpu_usages) or len(timestamps) != len(memory_usages):
        print(f"timestamps: {len(timestamps)}, cpu_usages: {len(cpu_usages)}, memory_usages: {len(memory_usages)}")
        min_length = min(len(timestamps), len(cpu_usages), len(memory_usages))
        timestamps = timestamps[:min_length]
        cpu_usages = cpu_usages[:min_length]
        memory_usages = memory_usages[:min_length]

total_time = search_end_time - search_start_time
minutes, seconds, milliseconds = format_time(total_time)
print(f"Search completed in {minutes} minutes {seconds} seconds {milliseconds} milliseconds.")
df = pd.DataFrame(results_list, columns=["id", "question", "relevant_passage_positions", "Embedding time", "Search time", "Max position"])
excel_path = "D:/Embedding/milvus/final.xlsx"
df.to_excel(excel_path, index=False, engine='openpyxl')




plt.figure(figsize=(12, 6))

#CPU
plt.subplot(2, 1, 1)
plt.plot(timestamps, cpu_usages, label='CPU Usage (%)', color='blue')
plt.axvline(x=search_start_time, color='red', linestyle='--', label='Search Start')
plt.axvline(x=search_end_time, color='green', linestyle='--', label='Search End')   
plt.xlabel('Time (s)')
plt.ylabel('CPU Usage (%)')
plt.title('Milvus CPU Usage During Search')
plt.legend()

#Memory
plt.subplot(2, 1, 2)
plt.plot(timestamps, memory_usages, label='Memory Usage (MB)', color='green')
plt.axvline(x=search_start_time, color='red', linestyle='--', label='Search Start')  
plt.axvline(x=search_end_time, color='green', linestyle='--', label='Search End')  
plt.xlabel('Time (s)')
plt.ylabel('Memory Usage (MB)')
plt.title('Milvus Memory Usage During Search')
plt.legend()


plt.tight_layout()
plot_path = "D:/Embedding/milvus/milvus_usage.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')

recall_values = [avg_recall[k] for k in intervals]
precision_values = [avg_precision[k] for k in intervals]

plt.figure(figsize=(10, 6))
plt.plot(recall_values, precision_values, 'bo-', linewidth=2)
plt.fill_between(
    recall_values,
    [avg_precision[k] - std_precision[k] for k in intervals],
    [avg_precision[k] + std_precision[k] for k in intervals],
    alpha=0.2, color='blue', label='±1 std dev'
)
plt.xlabel('Navratnost', fontsize=12)
plt.ylabel('Presnost', fontsize=12)
plt.title('Precnost-navratnost', fontsize=14)
plt.grid(True)
plt.xlim(0.70, 0.8)
plt.ylim(0.00, 0.16) 

for k, x, y in zip(intervals, recall_values, precision_values):
    plt.annotate(f'K={k}', (x, y), xytext=(5, 5), textcoords='offset points')
plot_path = "D:/Embedding/milvus/final.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
