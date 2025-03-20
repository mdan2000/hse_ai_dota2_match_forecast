import streamlit as st
import pandas as pd
from utils.logger import logger

def app():
    st.title("Загрузка датасета")
    uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])
    if uploaded_file is not None:
        with st.spinner("Грузим данные..."):
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.df = df  # сохраняем датасет в session_state
                st.success("Датасет успешно загружен!")
                st.subheader("Превью датасета")
                st.dataframe(df.head())
                st.text(f"Размер датасета: {df.shape[0]} строк, {df.shape[1]} столбцов")
                logger.info("Датасет загружен: shape=%s", df.shape)
            except Exception as e:
                st.error("Ошибка при загрузке файла")
                logger.error("Ошибка при загрузке датасета: %s", e)
    else:
        if 'df' in st.session_state:
            st.info("Датасет уже загружен. Используем текущий датасет.")
            df = st.session_state.df
            st.subheader("Превью датасета")
            st.dataframe(df.head())
            st.text(f"Размер датасета: {df.shape[0]} строк, {df.shape[1]} столбцов")