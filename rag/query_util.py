from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import BaseRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.prompts import (
    ChatPromptTemplate, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate, 
    AIMessagePromptTemplate
)

import os, logging
import warnings
import json 
from google.oauth2 import service_account
from dotenv import load_dotenv
from rag.database import *

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__) 

warnings.filterwarnings("ignore", category=UserWarning, module="langchain.chains.llm")

# Load environment variables
load_dotenv()


# Authenticate Google Cloud service account
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/gcp_key.json"


service_account_info=os.getenv('GOOGLE_CREDENTIALS')

# Ensure the env is loaded correctly 
if service_account_info:
    service_account_info = json.loads(service_account_info)
    cridentials = service_account.Credentials.from_service_account_info(service_account_info)
else:
    raise ValueError(f"The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set or empty")
    

# heroku config:set GOOGLE_APPLICATION_CREDENTIALS="$(cat /gcp_key.json)" -a app-name/glacial-forest-46805
# created an env in heroku for GOOGLE_APPLICATION_CREDENTIALS.

# Connect to MongoDB
client = client
db = db
COLLECTION_NAME = collection

# Instantiate VertexAIEmbeddings
embeddings = VertexAIEmbeddings(
    model_name="text-embedding-004"
)

# Initialize conversation history
conversation_history = []

def update_conversation_history(new_entry):
    global conversation_history
    conversation_history.append(new_entry)
    # Limit the conversation history to a reasonable length
    if len(conversation_history) > 10:  # Adjust the length as needed
        conversation_history = conversation_history[-10:]


# Instantiate MongoDBAtlasVectorSearch
vector_search = MongoDBAtlasVectorSearch(
    embedding=embeddings,
    collection=COLLECTION_NAME,
    index_name=INDEX_NAME,
    text_key="text",
    embedding_key="embedding"
)

# System prompt template with conversation history
system_promt = (
"""
Answer the following questions as best you can. You have access to the following tools: {tools}

Use the following format:

Question: the specific inquiry related to customer interaction or sales data you must answer, leveraging your knowledge as a social media manager assistant.
Thought: consider the most relevant information from the user's company services, such as Outsourcing Services, Chief Financial Officers, and Financial Consulting, to ensure precise and pertinent responses.
Action: the action to take should be retrieving or generating the necessary information accurately and reliably, possibly using tools like {get_vector_search}.
Action Input: the specific data or query needed to retrieve or augment information based on verified company details.
Observation: the result of the action, ensuring only accurate and verified information is used.
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: After analyzing the information, conclude the best approach to address the customer's needs or enhance the sales strategy, without mentioning the use of contextual data.
Final Answer: the direct and relevant answer to the original input question, utilizing the knowledge of the company's services.

Begin!

Previous Conversation:
{conversation_history}

Current Question:
Question: {input}
Thought: {agent_scratchpad}
"""
    "\n\n"
    "{context}"
)

# Initialize Gemini AI model 
llm = ChatVertexAI(
    model_name="gemini-1.5-pro-001",
    maxOutputTokens=1000,  # The maximum number of tokens to generate in the response
    temperature=0.5,  # The temperature parameter controls the randomness of the output — the higher the value, the more random the output
    topP=0.9, # The topP parameter controls the diversity of the output — the higher the value, the more diverse the output
    topK=20, # The topK parameter controls the diversity of the output — the higher the value, the more diverse the output
)

# Define a compressor and compression retriever
compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor = compressor,
    base_retriever=vector_search.as_retriever()
)


# Creating the chat promt template 
promt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(system_promt),
        HumanMessagePromptTemplate.from_template("{input}")
    ]
)

# Create the question-answer chain 
question_answer_chain = create_stuff_documents_chain(llm, promt)

# Create the retrieval chain using the compression retriever
rag_chain = create_retrieval_chain(compression_retriever, question_answer_chain)

# Instantiate query_engine
def query_index(query):
    # Perform the query using the retrieval chain
    response = rag_chain.invoke({"input": query})
    return response["answer"]

# # For testing the function manually
# if __name__ == "__main__":
#     test_query = "Hello How are you doing?"
#     print(query_index(test_query))

