import os
import pandas as pd
from azure.storage.blob import BlobServiceClient
from PyPDF2 import PdfReader
from openai import AzureOpenAI
from nltk.tokenize import sent_tokenize

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key="f619d2d04b4f44d28708e4c391039d01",
    api_version="2024-02-01",
    azure_endpoint="https://openainstance001.openai.azure.com/"
)

# Split content into chunks
def chunks_string(text, tokens):
    segments = []
    len_sum = 0
    k = 0
    raw_list = sent_tokenize(text)
    for i in range(len(raw_list)):
        x1 = len(raw_list[i].split())
        len_sum += x1
        k += 1
        if len_sum > tokens:
            j = max(0, i - (k + 1))
            if len(" ".join(raw_list[j:i + 1]).split()) > tokens:
                j = i - k
            segments.append(" ".join(raw_list[j:i]))
            len_sum = 0
            k = 0
        if i == len(raw_list) - 1:
            j = max(0, i - (k + 1))
            if len(" ".join(raw_list[j:i + 1]).split()) > tokens:
                j = i - k
            segments.append(" ".join(raw_list[j:i + 1]))
    return segments

# Function to read PDF file content and split into chunks
def read_and_split_pdf(file_path, file_name, chunk_size=200):
    reader = PdfReader(file_path)
    content_chunks = []
    for page_num, page in enumerate(reader.pages, start=1):
        page_content = page.extract_text() or ''
        chunks = chunks_string(page_content, chunk_size)
        content_chunks.extend([(page_num, file_name, chunk.strip()) for chunk in chunks if len(chunk.split()) > 2])
    return content_chunks

# Generate embeddings for a given text
def generate_embeddings(texts, model="text-embedding"):
    return client.embeddings.create(input=[texts], model=model).data[0].embedding

# Function to fetch all PDF files from Azure Blob Storage
def fetch_all_pdfs_from_blob(container_name, download_folder_path, connection_string):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs()

    if not os.path.exists(download_folder_path):
        os.makedirs(download_folder_path)

    pdf_files = []
    for blob in blob_list:
        if blob.name.lower().endswith('.pdf'):
            download_file_path = os.path.join(download_folder_path, os.path.basename(blob.name))
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)
            with open(download_file_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            pdf_files.append(download_file_path)
    
    return pdf_files

# Extract content and embedding from all PDF files in the container
def     extract_content_embedding_from_container(container_name, connection_string, download_folder_path='downloads'):
    db_path = "embedding.csv"
    old_files_list = []
    old_df = pd.DataFrame(columns=['page_no', 'file_name', 'text', "embedding"])

    # Fetch all PDFs from Azure Blob
    pdf_files = fetch_all_pdfs_from_blob(container_name, download_folder_path, connection_string)

    if os.path.exists(db_path):
        old_df = pd.read_csv(db_path)
        old_files_list = old_df['file_name'].unique()
        for old_file in old_files_list:
            if old_file not in [os.path.basename(f) for f in pdf_files]:
                print("deleting file ", old_file)
                condition = old_df['file_name'] == old_file
                old_df = old_df[~condition]

    total_chunks = []
    embedding_list = []

    # Read each PDF file, split into chunks, and display page number and chapter name
    for pdf_file in pdf_files:
        file_name = os.path.basename(pdf_file)
        if file_name not in old_files_list:
            print(f"Reading {file_name}...")
            chunks = read_and_split_pdf(pdf_file, file_name)
            total_chunks += chunks
            print("Number of chunks:", len(chunks))
            for page_num, file_name, chunk in total_chunks:
                print(f"Page {page_num} : Filename {file_name}: {chunk}")

    print("Total number of chunks from all PDF files:", len(total_chunks))
    for i, chunk in enumerate(total_chunks):
        embedding = generate_embeddings(chunk[2])
        embedding_list.append(embedding)

    data = [t for t in total_chunks if t]
    new_df = pd.DataFrame(data, columns=['page_no', 'file_name', 'text'])
    new_df['embedding'] = embedding_list
    new_df = pd.concat([new_df, old_df], ignore_index=True)
    new_df.to_csv(db_path, index=False)

    return True

def upload_files_to_blob(local_folder_path, container_name, connection_string):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    local_folder_name = os.path.basename(os.path.normpath(local_folder_path))  # Get the local folder name

    for root, _, files in os.walk(local_folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, local_folder_path)  # Get relative path
            blob_name = f"{local_folder_name}/{relative_path}".replace('\\', '/')  # Include folder name in blob path
            blob_client = container_client.get_blob_client(blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"Uploaded {file} to {container_name}/{blob_name}")

def list_pdfs_in_blob_folder(container_name, folder_name, connection_string):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with=folder_name)
    pdf_files = [blob.name for blob in blob_list if blob.name.lower().endswith('.pdf')]

    return pdf_files

def download_blobs_from_folder(container_name, folder_name, connection_string, local_download_path):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Create local download path if it doesn't exist
    if not os.path.exists(local_download_path):
        os.makedirs(local_download_path)

    blob_list = container_client.list_blobs(name_starts_with=folder_name)
    for blob in blob_list:
        blob_client = container_client.get_blob_client(blob.name)
        local_file_path = os.path.join(local_download_path, os.path.relpath(blob.name, folder_name))
        
        # Create directories if they don't exist
        local_dir = os.path.dirname(local_file_path)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        
        with open(local_file_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        print(f"Downloaded {blob.name} to {local_file_path}")

# Constants
CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=aisa0101;AccountKey=rISVuOQPHaSssHHv/dQsDSKBrywYnk6bNuXuutl4n+ILZNXx/CViS50NUn485kzsRxd5sfiVSsMi+AStga0t0g==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "aibot"
LOCAL_FOLDER_PATH = "folder1"  # Set your local folder path here

# Upload local PDF files to Azure Blob Storage
upload_files_to_blob(LOCAL_FOLDER_PATH, CONTAINER_NAME, CONNECTION_STRING)

# Ask user for the folder name
folder_name = input("Enter the folder name to download from Azure Blob Storage: ")

# Check if folder exists and list all PDF files
pdf_files = list_pdfs_in_blob_folder(CONTAINER_NAME, folder_name, CONNECTION_STRING)

if not pdf_files:
    print(f"No PDF files found in the folder '{folder_name}' in Azure Blob Storage.")
else:
    # Local path to download blobs
    local_download_path = os.path.join("downloaded_blobs", folder_name)

    # Download the blobs from the specified folder
    download_blobs_from_folder(CONTAINER_NAME, folder_name, CONNECTION_STRING, local_download_path)

    print("Downloaded PDF files:")
    for pdf_file in pdf_files:
        print(pdf_file)
