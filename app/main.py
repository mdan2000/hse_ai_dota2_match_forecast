import streamlit as st
from modules import load_dataset, eda, train_model, model_info, inference, experiments

st.sidebar.title("Навигация по приложению")
page = st.sidebar.radio("Выберите страницу", 
    ["Загрузка датасета", "EDA", "Обучение модели", "Информация о модели", "Инференс", "Сравнение экспериментов"])

if page == "Загрузка датасета":
    load_dataset.app()
elif page == "EDA":
    eda.app()
elif page == "Обучение модели":
    train_model.app()
elif page == "Информация о модели":
    model_info.app()
elif page == "Инференс":
    inference.app()
elif page == "Сравнение экспериментов":
    experiments.app()