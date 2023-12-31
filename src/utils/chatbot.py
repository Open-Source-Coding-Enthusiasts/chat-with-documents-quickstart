import os

from utils.utils import CheckResources
import pandas as pd
import streamlit as st
from langchain.chains.qa_with_sources.retrieval import \
    RetrievalQAWithSourcesChain

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import (
    HuggingFaceEmbeddings, OllamaEmbeddings,
    OpenAIEmbeddings,
)
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter,LLMChainExtractor

from langchain.llms import Ollama
from langchain.memory import PostgresChatMessageHistory
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient
from sqlalchemy import create_engine



class ChatBot:
    def __init__(
        self, selected_collection,
        selected_model_provider,
        selected_model,
        vector_db_client,
        embedding_model_provider,
        embedding_model,
    ) -> None:

        self.mapping = {'ai': 'assistant', 'human': 'user'}
        self.selected_collection = selected_collection
        self.vector_db_client = vector_db_client
        self.selected_model_provider = selected_model_provider
        self.selected_model = selected_model
        self.embedding_model_provider = embedding_model_provider
        self.embedding_model = embedding_model
        self.openai_api_key = os.getenv('OPENAI_APIKEY')
        self.llm_host = os.getenv('LLM_HOST')
        self.qdrant_host = os.getenv('QDRANT_HOST')
        self.database_conn_string = os.getenv('DATABASE_CONN_STRING')

    def monitor_prompt(self, qa_chain, prompt):

        handler = CheckResources.check_monitoring(return_handler=True)
        if handler is not 'Unavailable':
            return qa_chain(prompt, callbacks=[handler])
        else:
            return qa_chain(prompt)

    def _select_embedding_method(self, provider, model):
        provider_classes = {
            'HuggingFace': HuggingFaceEmbeddings,
            'OpenAI': OpenAIEmbeddings,
        }
        if model is not None and provider in provider_classes:
            if provider == 'OpenAI':
                return provider_classes[provider](openai_api_key=self.openai_api_key, model=model)
            return provider_classes[provider](model_name=model)

    def _select_model_params(self):
        with st.expander('Model Parameters'):
            col111,col222,col333 = st.columns(3)

            with col111:
                self.model_temperature = st.slider('Temperature', min_value=0.0, max_value=1.0, value=0.7)
            with col222:
                self.n_retrieved_docs = st.slider('Number of retrieved documents', min_value=1, max_value=50,value=20)
            with col333:
                self.reranker = st.checkbox('Reranker', value=False)

        st.divider()
        st.markdown('<br>', unsafe_allow_html=True)

    def _setup_llm(self):
        provider_classes = {
            'HuggingFace': Ollama,
            'OpenAI': ChatOpenAI,
        }
        if self.selected_model_provider in provider_classes:
            if self.selected_model_provider == 'OpenAI':
                return provider_classes[self.selected_model_provider](
                    model=self.selected_model, temperature=self.model_temperature,
                    openai_api_key=self.openai_api_key,
                    verbose=True,
                )

            return provider_classes[self.selected_model_provider](
                model=self.selected_model,
                base_url=self.llm_host,
                temperature=self.model_temperature,

            )

    def _connect_vector_db(self, embeddings):
        vectordb = QdrantClient(url=self.qdrant_host)
        vectordb = Qdrant(
            client=self.vector_db_client,
            collection_name=self.selected_collection,
            embeddings=embeddings,
        )


        return vectordb

    @staticmethod
    def _clear_chat(chat_history):
        with st.sidebar:
            if st.button('Reset converstaion', use_container_width=True):
                chat_history.clear()
                st.rerun()

    def _configure_qa_chain(self, llm, vector_db, embeddings):

        doc_compressor = EmbeddingsFilter(embeddings=embeddings)
        # doc_compressor = LLMChainExtractor.from_llm(llm)

        retriever = ContextualCompressionRetriever(base_compressor=doc_compressor,
                                                   base_retriever=vector_db.as_retriever(),
                                                   search_kwargs={"k": self.n_retrieved_docs}

                                                   )

        qa_chain = RetrievalQAWithSourcesChain.from_chain_type(
            llm=llm,
            retriever=retriever,
            verbose=True,

        )

        return qa_chain

    @staticmethod
    def _create_new_chat_window():
        connection_string = os.getenv('DATABASE_CONN_STRING')
        engine = create_engine(connection_string)

        with st.expander('Create New Chat'):
            form = st.form(key='new_chat_creation')

            session_id = form.text_input(
                label='New Chat', label_visibility='hidden', value='New Chat',
            )
            create = form.form_submit_button(
                'Create', use_container_width=True,
            )

            if create:
                df = pd.DataFrame()
                df['chat_name'] = [session_id]
                df['creation_date'] = [
                    pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
                ]
                df.to_sql(
                    'chat_sessions', engine,
                    if_exists='append', index=False,
                )
                st.toast('Chat Created Successfully!')
                st.rerun()

    def _get_chat_session_id(self):
        with st.sidebar:
            try:
                all_chats = pd.read_sql_table(
                    'chat_sessions', os.getenv('DATABASE_CONN_STRING'),
                )
                chat_id = st.selectbox(
                    'Select Chat', all_chats['chat_name'].unique(),
                )
                self._create_new_chat_window()
                return chat_id
            except ValueError:
                self._create_new_chat_window()
            st.divider()

    @staticmethod
    def _print_sources(sources):
        with st.expander('Sources'):
            st.write(sources)

    def start_chatting(self):
        self._select_model_params()

        embeddings = self._select_embedding_method(
            self.embedding_model_provider, self.embedding_model,
        )

        # Connect with Vector DB
        with st.spinner('Connecting to Vector DB...'):
            semantic_search = self._connect_vector_db(embeddings=embeddings)

        # Setup llm
        with st.spinner('Loading Language Model...'):
            llm = self._setup_llm()

        # Configure LLM chain
        with st.spinner('Configuring QA chain...'):
            qa_chain = self._configure_qa_chain(
                llm=llm,
                vector_db=semantic_search,
                embeddings=embeddings
            )

        current_chat = self._get_chat_session_id()

        # Initialize conversational history
        history = PostgresChatMessageHistory(
            connection_string=os.getenv('DATABASE_CONN_STRING'),
            session_id=current_chat,
        )

        # Add clear chat history as a sidebar button
        self._clear_chat(history)

        # Print each message in chat field
        for msg in history.messages:
            st.chat_message(self.mapping[msg.type]).write(msg.content)

        # Wait for user input
        if prompt := st.chat_input(placeholder='Tell me more about this document'):
            history.add_user_message(prompt)

            st.chat_message('user').write(prompt)

            with st.spinner('Thinking...'):
                # If user provides input, run the QA chain
                try:
                    if self.mapping[[msg.type for msg in history.messages][-1]] == 'user':

                        response = self.monitor_prompt(qa_chain, prompt)
                        answer = response['answer']
                        sources = response['sources']

                        history.add_ai_message(answer)
                        st.chat_message('assistant').write(answer)
                        self._print_sources(sources)

                # There are no messages in the chat written by user, do nothing
                except IndexError:
                    pass
