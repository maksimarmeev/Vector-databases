from Bio import Entrez
import json
import time
from datasets import load_dataset

def format_time(total_time):
    minutes = int(total_time // 60) 
    seconds = int(total_time % 60)  
    milliseconds = int((total_time - int(total_time)) * 1000)  
    if milliseconds >= 1000:
        seconds += milliseconds // 1000
        milliseconds = milliseconds % 1000

    return minutes, seconds, milliseconds


Entrez.email = "maksym.armieiev@student.tuke.sk"
dataset = load_dataset("rag-datasets/rag-mini-bioasq", "text-corpus")['passages']
unique_ids = [item['id'] for item in dataset][30000:]
all_articles = []
failed_articles = []
start_time = time.time()
for article_id in unique_ids:
    try:
        handle = Entrez.efetch(db="pubmed", id = article_id, rettype = "medline", retmode = "text")
        records = handle.read()
        title = []
        abstract = []
        current_field = None
        for line in records.split("\n"):
            if line.startswith("TI  - "):
                current_field = "TI"
                title.append(line[6:].strip())
            elif line.startswith("AB  - "):
                current_field = "AB"
                abstract.append(line[6:].strip())
            elif line.startswith("      "):
                if current_field == "TI":
                    title.append(line[6:].strip())
                elif current_field == "AB":
                    abstract.append(line[6:].strip())
            else:
                current_field = None
        full_title = " ".join(title)
        full_abstract = " ".join(abstract)
        text = f"{full_title} {full_abstract}"
        all_articles.append({
                "pmid": article_id,
                "title": " ".join(title),
                "abstract": " ".join(abstract),
                "text": text
            })
        print(f"Added article PMID: {article_id}")
    except Exception as e:
        print(f"Error with article {article_id}: {str(e)}")
with open("merged_articles.json", "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=4)
end_time = time.time()
total_time = end_time - start_time
minutes, seconds, milliseconds = format_time(total_time)
print(f"Downloading completed in {minutes} minutes {seconds} seconds {milliseconds} milliseconds.")