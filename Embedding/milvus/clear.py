from pymilvus import connections, utility

def delete_schema(collection_name):
    try:
        connections.connect("default", host="localhost", port="19530")
        utility.drop_collection(collection_name)
        print(f"Collection '{collection_name}' was deleted.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        connections.disconnect("default")

if __name__ == "__main__":
    collection_name = "articles"
    delete_schema(collection_name)