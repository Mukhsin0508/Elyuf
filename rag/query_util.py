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

# Instantiate MongoDBAtlasVectorSearch
vector_search = MongoDBAtlasVectorSearch(
    embedding=embeddings,
    collection=COLLECTION_NAME,
    index_name=INDEX_NAME,
    text_key="text",
    embedding_key="embedding"
)

# Define a promt for the system 
system_promt = (
    """
   You are an assistant specializing in answering questions about the Top 300 University Rankings accepted by the El-Yurt Umidi Foundation of Uzbekistan. 
   If you can’t find the university rankings or even the name in the database, politely inform the user that the university is most likely not in the top 300 universities list of the EYUF Foundation.

Please remember:

	•	You are only supposed to know the rankings for universities within the 2024 top 300 list accepted by EYUF.
	•	It is perfectly fine to admit when you don’t have information.

When providing answers, follow this format:

	•	Greet the user first!
	•	QS World University Rank: [rank]
	•	Times Higher Education Rank: [rank]
	•	US News & World Report Rank: [rank]

Occasionally, ask if there are any other universities they would like to know about, and use some emojis to make the interaction friendly and engaging.
    
    """
    "\n\n"
    "{context}"
)
# Initialize Gemini AI model 
llm = ChatVertexAI(
    model_name="gemini-1.5-pro-001",
    maxOutputTokens=500,  # The maximum number of tokens to generate in the response
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

