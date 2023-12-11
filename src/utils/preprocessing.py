import os
from typing import Any

import pandas as pd
import streamlit as st
from langchain.embeddings import (
    HuggingFaceEmbeddings,
    OpenAIEmbeddings,
)
from langchain.schema.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Qdrant
from sqlalchemy import create_engine

from utils.conf_loaders import load_config

embeddings_config = load_config(custom_key='embeddings')
embeddings_providers = embeddings_config.keys()
embeddings_models = embeddings_config


class MakeEmbeddings:
    """
    This class provides methods to create embeddings for a given text.
    """

    def __init__(self, text, collection_name) -> None:
        """
        Initializes the MakeEmbeddings class.

        Args:
            text (str): The text to create embeddings for.
            collection_name (str): The name of the collection to save the embeddings in.
        """
        self.text = text
        self.collection_name = collection_name

    def _embedding_model_params(self):
        """
        Sets the parameters for the embedding model.
        """
        self.chunk_size = st.number_input('Chunk Size', 0, 1000, 100)
        self.chunk_overlap = st.slider('Chunk Overlap', 0, 1000, 50)

    @staticmethod
    def _chunk_docs(text):
        """
        Splits the text into chunks.

        Args:
            text (str): The text to split.

        Returns:
            list: A list of Document objects, each representing a chunk of the text.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=50,
        )
        return [
            Document(page_content=x, metadata={'source': x})
            for x in text_splitter.split_text(text)
        ]

    def _select_embedding_method(self):
        """
        Selects the embedding method based on the provider and model.

        Returns:
            HuggingFaceEmbeddings or OpenAIEmbeddings: The selected embedding method.
        """
        if self.model is not None:
            if self.provider == 'HuggingFace':
                return HuggingFaceEmbeddings(model_name=self.model)

            elif self.provider == 'OpenAI':
                return OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_APIKEY'), model=self.model)

    @staticmethod
    def _create_engine():
        """
        Creates a database engine.

        Returns:
            Engine: The created database engine.
        """
        return create_engine(os.getenv('DATABASE_CONN_STRING'))

    def _save_mapping(self):
        """
        Saves the mapping of the collection to the embedding model in the database.
        """
        engine = self._create_engine()

        df = pd.DataFrame({
            'collection': [self.collection_name],
            'embedding_model_provider': [self.provider],
            'embedding_model_name': [self.model],
        })

        df.to_sql(
            'embedding_mappings', engine,
            if_exists='append', index=False,
        )

    def __call__(self) -> Any:
        """
        Calls the MakeEmbeddings class.

        Returns:
            Any: The result of the call.
        """
        self.docs = self._chunk_docs(self.text)

        self.provider = st.selectbox(
            'Select Embedding Method', embeddings_providers,
        )
        self.model = st.selectbox(
            'Select Embedding Model', [
                None,
            ] + embeddings_models[self.provider],
        )

        self.embedding_model = self._select_embedding_method()

    def save_embeddings(self):
        """
        Saves the embeddings in the Qdrant vector store and the mapping in the database.
        """
        Qdrant.from_documents(
            self.docs,
            self.embedding_model,
            url=os.getenv('QDRANT_HOST'),
            collection_name=self.collection_name,
        )

        self._save_mapping()
