import os


def using_azure_blob() -> bool:
    enabled = os.getenv("ENABLE_AZURE_BLOB", "False").lower() == "true"
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "")
    return enabled and bool(account_name and account_key and container_name)
