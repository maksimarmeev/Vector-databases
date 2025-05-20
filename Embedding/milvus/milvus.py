from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import json
import time
import docker
import threading
import matplotlib.pyplot as plt
import shutil


container_name = "milvus-standalone"
client_docker = docker.from_env()
container = client_docker.containers.get(container_name)

cpu_usages = []
memory_usages = []
disk_usages = []
timestamps = []
stop_metrics = False

data_lock = threading.Lock()

def get_metrics():
    stats = container.stats(stream=False)
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
    cpu_usage = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100 if system_delta > 0 else 0
    memory_usage = stats["memory_stats"]["usage"] / (1024 * 1024)
    
    total, used, free = shutil.disk_usage("D:/")
    disk_usage = used / (1024 ** 3)

    return cpu_usage, memory_usage, disk_usage

def collect_metrics():
    while not stop_metrics:
        with data_lock:
            timestamps.append(time.time())
            cpu, mem, disk = get_metrics()
            cpu_usages.append(cpu)
            memory_usages.append(mem)
            disk_usages.append(disk)
        time.sleep(30)



def create_schema(client):
    collection_name = "articles"
    if not utility.has_collection(collection_name):
        fields = [
            FieldSchema(name = "id", dtype = DataType.VARCHAR, max_length = 64, is_primary = True),
            FieldSchema(name="title", dtype = DataType.VARCHAR, max_length = 65535),
            FieldSchema(name="abstract", dtype = DataType.VARCHAR, max_length = 65535),
            FieldSchema(name = "text", dtype=DataType.VARCHAR, max_length = 65535),
            FieldSchema(name = "embedding", dtype=DataType.FLOAT_VECTOR, dim = 384),
        ]
        schema = CollectionSchema(fields)
        collection = Collection(name = collection_name, schema=schema)
        return collection

def load_data_to_milvus(client, file_path, limit = 40221):
    collection_name = "articles"
    collection = Collection(collection_name)
    start_time = time.time()
    try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]
            data = data[:limit]
            for idx, article in enumerate(data, start=1):
                try:
                    article_id = str(article['pmid'])
                    collection.insert([
                        [article_id], 
                        [article['title']],
                        [article['abstract']],
                        [article['text']],   
                        [article['embedding']]  
                    ])
                    print(f"[{idx}/{limit}] Article with id {article_id} loaded to Elasticsearch")
                except KeyError as e:
                    print(f"Ошибка в файле: отсутствует поле {e} в статье {article}")
                except Exception as e:
                    print(f"Ошибка при вставке статьи с ID {article['id']}: {e}")
            print(f"Data from file added to Milvus.")
            collection.flush()
    except json.JSONDecodeError as e:
            print(f"Error in file: {e}")
    except KeyError as e:
            print(f"Error in file: missing {e}")
    end_time = time.time()
    total_time = end_time - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    time_message =f"Data was loaded into Milvus in {minutes} minutes {seconds} seconds.\n"
    with open("time1.txt", "a", encoding="utf-8") as f:
        f.write(time_message)
    

def main():
    global stop_metrics
    metric_thread = threading.Thread(target=collect_metrics)
    metric_thread.daemon = True
    metric_thread.start()
    folder_path = "D:/Embedding/merged_articles.json"
    try:
        connections.connect("default", host="localhost", port="19530")
        collection = create_schema(connections)
        load_data_to_milvus(connections, folder_path, limit=40221)
    finally:
        stop_metrics = True
        metric_thread.join(timeout=2)
        connections.disconnect("default")
    if len(timestamps) == len(cpu_usages) == len(memory_usages) == len(disk_usages):
        plt.figure(figsize=(12, 8))

        #CPU
        plt.subplot(3, 1, 1)
        plt.plot(timestamps, cpu_usages, label='CPU (%)', color='blue')
        plt.ylabel('CPU (%)')
        plt.title('CPU Usage During Indexing')
        plt.grid(True)

        #Memory
        plt.subplot(3, 1, 2)
        plt.plot(timestamps, memory_usages, label='Memory (MB)', color='green')
        plt.ylabel('Memory (MB)')
        plt.title('Memory Usage During Indexing')
        plt.grid(True)

        #Disk
        plt.subplot(3, 1, 3)
        plt.plot(timestamps, disk_usages, label='Disk Usage (GB)', color='orange')
        plt.xlabel('Timestamp (s)')
        plt.ylabel('Disk Usage (GB)')
        plt.title('Disk Usage During Indexing')
        plt.grid(True)

        plt.tight_layout()
        plt.savefig("D:/Embedding/milvus/indexing_metrics.png", dpi=300, bbox_inches='tight')
        print("Saved chart to indexing_metrics.png")
    else:
        print("Length mismatch in collected metrics")
if __name__ == "__main__":
    main()


