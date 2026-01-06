"""Pinecone Vector Store Client"""
import os
import pinecone

class PineconeClient:
    def __init__(self):
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
    
    def search(self, query_vector, top_k=5):
        """Semantic search"""
        index = pinecone.Index(self.index_name)
        return index.query(query_vector, top_k=top_k)
