from google.cloud import storage, firestore
from datetime import datetime

COLLECTION_NAME = "fileuploader"

def set_metadata(filename, filetype, description):
    firestore_client = firestore.Client()
    doc = firestore_client.collection(COLLECTION_NAME).document(filename)
    
    description = "" if description is None else description
    metadata = {
        "filetype": filetype,
        "description": description,
        "creation_date": datetime.now(),
    }

    doc.set(metadata)

def set_tag(filename, key, value):
    firestore_client = firestore.Client()
    doc = firestore_client.collection(COLLECTION_NAME).document(filename)
    doc_data = doc.get(field_paths=["tags"])
    # Check if the document exists
    if not doc_data.exists:
        return
    doc_data = doc_data.to_dict()
    tags = [] if "tags" not in doc_data else doc_data["tags"]
    new_tag = {"key": key, "value": value}
    tags.append(new_tag)
    doc_data = {"tags": tags}
    doc.set(doc_data, merge=True)


def search(value):
    firestore_client = firestore.Client()
    col = firestore_client.collection(COLLECTION_NAME)
    results = []
    for doc in col.list_documents():
        metadata = get_metadata(doc)
        if metadata is None:
            continue
        description = metadata["description"]
        filename = doc.id
        if value in filename or value in description:
            results.append(filename)

    return results


def get_metadata(document):
    doc_data = document.get()
    # Check if the document exists
    if doc_data.exists:
        # Get the document data
        doc_data = doc_data.to_dict()
        return doc_data
    else:
        return None
    
def get_metadata_from_filename(filename):
    firestore_client = firestore.Client()
    doc = firestore_client.collection(COLLECTION_NAME).document(filename)
    return get_metadata(doc)


def upload(file, bucket_name, object_name):
    # Initialize a GCS client
    client = storage.Client()

    # Get the bucket where you want to upload the file
    bucket = client.bucket(bucket_name)

    # Upload the file to GCS
    blob = bucket.blob(object_name)
    blob.upload_from_file(file)

    # Generate the URL for the uploaded file
    file_url = f'gs://{bucket_name}/{object_name}'

    return file_url

def download(bucket_name, object_name):
    """
    Downloads a file from Google Cloud Storage and returns its content as bytes.

    Args:
        bucket_name (str): The name of the GCS bucket.
        blob_name (str): The name of the object in the bucket.

    Returns:
        bytes: The content of the downloaded file as bytes.
    """
    # Initialize a GCS client
    client = storage.Client()

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Get the blob (object) to download
    blob = bucket.blob(object_name)

    # Download the object and return its content as bytes
    content = blob.download_as_bytes()

    return content

def generate_download_url(bucket_name, object_name, expiration=3600):
    """
    Generates a signed URL for downloading a GCS object.

    Args:
        bucket_name (str): The name of the GCS bucket.
        blob_name (str): The name of the object within the bucket.
        expiration (int): Expiration time for the URL in seconds (default is 1 hour).

    Returns:
        str: The signed URL for downloading the object.
    """
    # Initialize a GCS client
    client = storage.Client()

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Get the blob (object) for which you want to generate a signed URL
    blob = bucket.blob(object_name)

    # Generate a signed URL with the specified expiration time
    signed_url = blob.generate_signed_url(expiration=expiration)

    return signed_url