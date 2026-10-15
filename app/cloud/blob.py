class BlobStore:
 def __init__(self,connection_string=None,container="datasets"): self.enabled=bool(connection_string); self.connection_string=connection_string; self.container=container
 def upload(self,data,name):
  if not self.enabled: return {"stored":"local","name":name}
  from azure.storage.blob import BlobServiceClient
  client=BlobServiceClient.from_connection_string(self.connection_string); c=client.get_container_client(self.container)
  try:c.create_container()
  except Exception:pass
  c.upload_blob(name=name,data=data,overwrite=True); return {"stored":"azure_blob","name":name}
