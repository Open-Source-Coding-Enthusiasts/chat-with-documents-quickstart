import base64
import os

import requests
import streamlit as st
from dotenv import load_dotenv
from psycopg2.errors import OperationalError
from sqlalchemy import create_engine
from langfuse.callback import CallbackHandler
import pandas as pd

load_dotenv('../.env')


def clear_cache():
    st.legacy_caching.caching.clear_cache()

# flake8: noqa: E501


def show_pdf_uplaoded(bytes_data):
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="100" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


class CheckResources:
    @staticmethod
    @st.cache_data
    def check_qdrant():
        try:
            response = requests.get(os.getenv('QDRANT_HOST'))
            if response.status_code == 200:
                return 'Running'
        except requests.exceptions.ConnectionError:
            return 'Unavailable'

    def check_db():
        try:
            conn_string = os.getenv('DATABASE_CONN_STRING')
            engine = create_engine(conn_string)
            engine.connect()
            return 'Running'

        except OperationalError:
            return 'Unavailable'

    @staticmethod
    def check_llm():
        try:
            response = requests.get(os.getenv('LLM_HOST'))
            if response.status_code == 200:
                return 'Running'
        except requests.exceptions.ConnectionError:
            return 'Unavailable'

    def check_monitoring():
        engine = create_engine(os.getenv('DATABASE_CONN_STRING'))
        df = pd.read_sql_table('monitoring', engine)
        monitoring_dict = df.to_dict(orient='records')[0]
        print(monitoring_dict)
        try:
            handler = CallbackHandler(
                host=monitoring_dict['LANGFUSE_SERVER_URL'],
                public_key=monitoring_dict['LANGFUSE_PUBLIC_KEY'],
                secret_key=monitoring_dict['LANGFUSE_SECRET_KEY'],
            )

            if handler.auth_check() == True:
                return 'Running'
        except Exception as e:
            return 'Unavailable'
