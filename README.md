# Infraštruktúra pre spracovanie obsahu na webe

Tento repozitár obsahuje implementáciu vytvorenú v rámci bakalárskej práce zameranej na porovnanie vektorových databáz pri ukladaní a vyhľadávaní textových dát. Projekt bol navrhnutý s cieľom zhodnotiť výkonnosť troch moderných vektorových databáz: **Weaviate**, **Milvus** a **Elasticsearch**.

## Štruktúra repozitára

### Vstupné dáta
- `merged_articles.json` – súbor so vzorkou textových dokumentov, stiahnutý pomocou skriptu `get-query.py` z datasetu [rag-mini-bioasq](https://huggingface.co/datasets/rag-datasets/rag-mini-bioasq) (platforma Hugging Face)

### Skripty
- `main.py` – skript, ktorý pre každý dokument v `merged_articles.json` vypočíta embedding a uloží ho do súboru
- `get-query.py` – skript na stiahnutie dát zo vzdialeného datasetu a uloženie do súboru `merged_articles.json`
- `time.txt` – súbor obsahujúci namerané časy vkladania dokumentov do jednotlivých databáz

### Moduly podľa databázy

Každá databáza má vlastný priečinok so štyrmi základnými skriptmi:

- `*.py` – skript na nahrávanie predspracovaných dokumentov (s embeddingmi) do databázy
- `find.py` – skript na vyhľadávanie pomocou vektorových dotazov, vyhodnocovanie presnosti a výkonnosti
- `clear.py` – skript na vymazanie dát z databázy
- `docker-compose.yml` – konfigurácia na lokálne spustenie databázy pomocou Dockeru

Skript `find.py` generuje:
- `.xlsx` súbor s výsledkami vyhľadávania (pozície relevantných dokumentov),
- vizualizáciu systémových metrík (CPU, pamäť) počas vyhľadávania,
- graf precíznosti a návratnosti.

Skript `*.py` generuje:
- vizualizáciu systémových metrík počas indexovania dokumentov, vrátane CPU, pamäte a disku.

## Cieľ

Cieľom projektu je experimentálne porovnať výkonnosť vybraných vektorových databáz na základe:

- času potrebného na indexovanie dokumentov,
- rýchlosti odpovede pri vektorových dotazoch,
- presnosti a návratnosti vyhľadávania (precision a recall),
- záťaže systému počas indexovania a vyhľadávania (CPU, pamäť, disk),
- jednoduchej integrácie s Python prostredím a obslužnými knižnicami.

Merania prebiehajú automatizovane počas vykonávania skriptov a výsledky sú vizualizované vo forme `.xlsx` tabuliek a `.png` grafov.

Každá databáza je testovaná rovnakou vzorkou dát a jednotným spôsobom dotazovania. Výsledky sú porovnávané na základe zaznamenaných časových metrík.

## Použité technológie

- Python **3.13.2**
- Visual Studio Code
- Docker / Docker Compose
- Weaviate
- Milvus
- Elasticsearch
- Hugging Face (Datasets, Transformers)
- PubMed Entrez API (NCBI)

## Prostredie

Projekt bol vyvíjaný v jazyku **Python** v prostredí **Visual Studio Code**. Všetky použité knižnice sú uvedené v súbore `requirements.txt`.

## Autor

Armieiev Maksym – bakalárska práca, [FEI / TUKE] (2025)
