import ast
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI


client = AzureOpenAI(
  api_key = "f619d2d04b4f44d28708e4c391039d01",
  api_version = "2024-02-01",
  azure_endpoint = "https://openainstance001.openai.azure.com/"

)


def extract_array_of_embedding_from_file(file_name):
    df = pd.read_csv(file_name)
    
    embedding_list_final = []
    embedding_list = df.embedding.apply(ast.literal_eval)
    for temp_element in embedding_list:
        embedding_list_final.append(temp_element)
    embedding_array = np.array(embedding_list_final)    
    return embedding_array, df 


def query_array(query, model="text-embedding"):
    data = client.embeddings.create(input = [query], model=model).data[0].embedding
    query_array = np.array(data)
    query_array = query_array.reshape(1, -1)
    return query_array


def get_text_cosine_similarity(query_array, db_array, top_k, dataframe):
    cosine_sim = cosine_similarity(query_array, db_array)
    cosine_sim = cosine_sim.flatten()
    top_10_indices = np.argsort(cosine_sim)[-top_k:][::-1]
    top_10_df = dataframe.iloc[top_10_indices]
    print(top_10_df[["page_no","file_name"]])
    text_list = top_10_df["text"].to_list()
    return text_list


def extract_content_based_on_query(query,top_k):
    file_name = "embedding.csv"
    db_array, dataframe = extract_array_of_embedding_from_file(file_name)
    print(db_array)
    array_query = query_array(query)
    resulted_text = get_text_cosine_similarity(array_query, db_array, top_k, dataframe)
    print(resulted_text)
    return resulted_text