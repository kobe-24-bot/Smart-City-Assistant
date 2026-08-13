#load pdf
#split into chunks
#create embeddings
#store them in chroma database


from langchain_community.document_loaders import TextLoader,PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv

load_dotenv()


#load data
data = PyPDFLoader("document_loaders/deeplearning.pdf")
docs = data.load()

##split of data
splitter=RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks=splitter.split_documents(docs)


#embeddings done
embedding_model=HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
)


##database created
vectorstore=Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory="chroma_db"
)


