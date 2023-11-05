from google.cloud import storage

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