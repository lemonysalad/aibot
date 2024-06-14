from openai import AzureOpenAI
import os
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import gradio as gr
import uvicorn
from model import extract_content_based_on_query

import mysql.connector
from datetime import datetime

def create_table():
    try:
        connection = mysql.connector.connect(
            host='mysqlai.mysql.database.azure.com',
            user='azureadmin',
            password='Meridian@123',
            database='chatbot'
        )
        cursor = connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS query_responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        );
        """
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully.")
    except mysql.connector.Error as error:
        print(f"Failed to create table: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def insert_into_db(user_id, query, response):
    try:
        connection = mysql.connector.connect(
            host='mysqlai.mysql.database.azure.com',
            user='azureadmin',
            password='Meridian@123',
            database='chatbot'
        )
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO query_responses (user_id, query, response, timestamp) 
        VALUES (%s, %s, %s, %s)
        """
        timestamp = datetime.now()
        cursor.execute(insert_query, (user_id, query, response, timestamp))
        connection.commit()
        print("Data inserted successfully into MySQL database.")
    except mysql.connector.Error as error:
        print(f"Failed to insert data into MySQL table: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            
chat_client = AzureOpenAI(
                      azure_endpoint = "https://openainstance001.openai.azure.com/",  # Replace with your Azure OpenAI endpoint
                      api_key = "f619d2d04b4f44d28708e4c391039d01",  # Replace with your API key
                      api_version = "2024-02-15-preview"
                    )

# content = """Photosynthesis, the process by which green plants and certain other organisms transform light energy into chemical energy. During photosynthesis in green plants, light energy is captured and used to convert water, carbon dioxide, and minerals into oxygen and energy-rich organic compounds.

# It would be impossible to overestimate the importance of photosynthesis in the maintenance of life on Earth. If photosynthesis ceased, there would soon be little food or other organic matter on Earth. Most organisms would disappear, and in time Earth’s atmosphere would become nearly devoid of gaseous oxygen. The only organisms able to exist under such conditions would be the chemosynthetic bacteria, which can utilize the chemical energy of certain inorganic compounds and thus are not dependent on the conversion of light energy.

# All living things are composed of cells.See all videos for this article
# Energy produced by photosynthesis carried out by plants millions of years ago is responsible for the fossil fuels (i.e., coal, oil, and gas) that power industrial society. In past ages, green plants and small organisms that fed on plants increased faster than they were consumed, and their remains were deposited in Earth’s crust by sedimentation and other geological processes. There, protected from oxidation, these organic remains were slowly converted to fossil fuels. These fuels not only provide much of the energy used in factories, homes, and transportation but also serve as the raw material for plastics and other synthetic products. Unfortunately, modern civilization is using up in a few centuries the excess of photosynthetic production accumulated over millions of years. Consequently, the carbon dioxide that has been removed from the air to make carbohydrates in photosynthesis over millions of years is being returned at an incredibly rapid rate. The carbon dioxide concentration in Earth’s atmosphere is rising the fastest it ever has in Earth’s history, and this phenomenon is expected to have major implications on Earth’s climate.

# Requirements for food, materials, and energy in a world where human population is rapidly growing have created a need to increase both the amount of photosynthesis and the efficiency of converting photosynthetic output into products useful to people. One response to those needs—the so-called Green Revolution, begun in the mid-20th century—achieved enormous improvements in agricultural yield through the use of chemical fertilizers, pest and plant-disease control, plant breeding, and mechanized tilling, harvesting, and crop processing. This effort limited severe famines to a few areas of the world despite rapid population growth, but it did not eliminate widespread malnutrition. Moreover, beginning in the early 1990s, the rate at which yields of major crops increased began to decline. This was especially true for rice in Asia. Rising costs associated with sustaining high rates of agricultural production, which required ever-increasing inputs of fertilizers and pesticides and constant development of new plant varieties, also became problematic for farmers in many countries.
# """

history = ""

def get_response_from_query(query, content, history):
    message = [
        {"role": "system", "content": "You are an AI assistant that helps to answer the questions from the given content."},
        {"role": "user", "content": f"""Your task is to extract accurate answer for given user query, chat history and provided input content.\n\nInput Content : {content} \n\nUser Query : {query}\n\nChat History : {history}\n\nImportant Points while generating response:\n1. The answer of the question should be relevant to the input text.\n2. Answer complexity would be based on input content.\n3. If input content is not provided direct the user to provide content.\n4. Answers should not be harmful or spam. If there is such content give the instructions to user accordingly. \n\nExtracted Answer :"""}
    ]

    response = chat_client.chat.completions.create(
      model="gpt4", # model = "deployment_name"
      messages = message,
      temperature=0.7,
      max_tokens=800,
      top_p=0.95,
      frequency_penalty=0,
      presence_penalty=0,
      stop=None
    )
    output_str = ""
    for choice in response.choices:
        output_str += choice.message.content
    return output_str



# app = FastAPI()

# class Item(BaseModel):
#     input_string: str

# @app.post("/get-answer/")
# async def get_answer(item: Item):
#     # Here you can process the input string as needed
#     query_string = item.input_string
#     content_list = extract_content_based_on_query(query_string, 10)
#     content = " ".join(content_list)
#     reponse = get_response_from_query(query_string, content, history)
#     return reponse


# app = FastAPI()

# def respond_to_question(query_string):
#     # Placeholder response logic
#     content_list = extract_content_based_on_query(query_string, 10)
#     content = " ".join(content_list)
#     answer = get_response_from_query(query_string, content, history)
#     return answer
# # Define the Gradio interface
# interface = gr.Interface(
#     fn=respond_to_question,
#     inputs="text",
#     outputs="text",
#     title="Question Answering System",
#     description="Enter your question and get an answer along with an explanation.",
# )

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the Question Answering API"}

# @app.get("/question-answering")
# def get_gradio_interface():
#     return interface.launch(share=False)

# if __name__ == "__main__":
#     uvicorn.run(app)
import gradio as gr

def respond_to_question(query_string):
    # Placeholder response logic
    content_list = extract_content_based_on_query(query_string, 10)
    content = " ".join(content_list)
    print(content)
    answer = get_response_from_query(query_string, content, history)
     # Insert the query and answer into the database
    user_id = 1  # You can modify this to be dynamic if needed
    insert_into_db(user_id, query_string, answer)
    return answer



# Define the Gradio interface
interface = gr.Interface(
    fn=respond_to_question,
    inputs="text",
    outputs="text",
    title="Question Answering System",
    description="Enter your question and get an answer.",
)

# Launch the Gradio app
interface.launch()