import weaviate

client = weaviate.connect_to_local()
collections = client.collections.list_all()
for collection_name in collections:
    collection = client.collections.get(collection_name)
    
    for obj in collection.iterator():
        collection.data.delete_by_id(obj.uuid)
        print(f"Removed object with ID: {obj.uuid}")
    client.collections.delete(collection_name)
    print(f"Collection '{collection_name}' removed.")

client.close()
print("Weaviate cleared.")
