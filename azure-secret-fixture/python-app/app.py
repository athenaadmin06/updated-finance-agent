from azure.storage.blob import BlobServiceClient
from config import STORAGE_CONNECTION_STRING

def list_containers():
    client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    return [c.name for c in client.list_containers()]
