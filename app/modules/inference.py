import os
import streamlit as st
import requests
import json
import pickle
import pandas as pd
import boto3
from botocore.exceptions import ClientError
import io
from utils.logger import logger

def list_models_in_s3(bucket_name, prefix="models/"):
    aws_access_key_id = st.secrets["general"]["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = st.secrets["general"]["AWS_SECRET_ACCESS_KEY"]
    if not aws_access_key_id or not aws_secret_access_key:
        st.error("AWS ключи не настроены. Пожалуйста, настройте их в Streamlit Secrets.")
        return []
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        models = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if not key.endswith('/'):  # исключаем папки
                    models.append(key)
        return models
    except ClientError as e:
        st.error(f"Ошибка при получении списка моделей: {e}")
        return []

def upload_data_to_s3(uploaded_file, bucket_name, key):
    aws_access_key_id = st.secrets["general"]["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = st.secrets["general"]["AWS_SECRET_ACCESS_KEY"]
    if not aws_access_key_id or not aws_secret_access_key:
        st.error("AWS ключи не настроены. Пожалуйста, настройте их в Streamlit Secrets.")
        return None
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    try:
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=uploaded_file.getvalue())
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=3600  # ссылка действительна 1 час
        )
        return url
    except ClientError as e:
        st.error(f"Ошибка загрузки файла в S3: {e}")
        return None

def app():
    st.title("Инференс (получить предсказания)")
    bucket_name = "dmyachin-new-models"

    # 1. Поиск моделей в S3
    with st.spinner("Получаем список моделей из S3..."):
        models_list = list_models_in_s3(bucket_name, prefix="models/")
    if not models_list:
        st.error("Модели не найдены в бакете S3.")
        return

    # Формируем словарь для выбора: ключ – отображаемое имя (без префикса "models/"), значение – объект модели
    options = {}
    for model in models_list:
        s3_key = model  # полный путь, например, "models/LogisticRegression_experiment_1.pkl"
        display_name = s3_key.replace("models/", "")
        options[display_name] = {"s3_key": s3_key}
    
    # Оставляем только нужные модели
    allowed_models = {
        "LogisticRegression_experiment_1_inf.pkl",
        "LogisticRegression_experiment_2_inf.pkl",
        "SGDClassifier_experiment_3_inf.pkl",
        "SGDClassifier_experiment_4_inf.pkl",
        "DecisionTreeClassifier_experiment_5_inf.pkl",
        "DecisionTreeClassifier_experiment_6_inf.pkl"
    }
    filtered_options = {k: v for k, v in options.items() if k in allowed_models}
    if not filtered_options:
        st.error("Нет доступных моделей для инференса.")
        return

    # Предлагаем выбрать модель пользователю
    selected_display = st.selectbox("Выберите модель для инференса", list(filtered_options.keys()))
    selected_model_info = filtered_options[selected_display]
    logger.info("Пользователь выбрал модель для инференса: %s", selected_display)

    # 2. Загрузка данных для инференса
    st.markdown("### Загрузите CSV с данными для инференса")
    uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])
    data_path = ""
    if uploaded_file is not None:
        key = f"data/{uploaded_file.name}"
        with st.spinner("Загружаем данные в S3..."):
            data_path = upload_data_to_s3(uploaded_file, bucket_name, key)
        if data_path:
            st.success("Данные успешно загружены!")
        else:
            st.error("Не удалось загрузить данные в S3.")
            return
    else:
        st.info("Пожалуйста, загрузите CSV с данными для инференса.")

    # 3. Кнопка для вызова предикта
    if st.button("Получить предсказания"):
        if not selected_display:
            st.error("Модель не выбрана.")
            return
        if not data_path:
            st.error("Данные не загружены.")
            return
        
        model_name_payload = selected_display.replace(".pkl", "")
        payload = {
            "model_name": model_name_payload,  # передаём название модели без префикса
            "data_path": data_path
        }
        api_url = "https://abkfijydkg.execute-api.us-east-1.amazonaws.com/dev/dev-predict"
        API_KEY = st.secrets["general"]["API_KEY"]
        if not API_KEY:
            st.error("API_KEY не настроен. Пожалуйста, настройте его в Streamlit Secrets.")
            return
        headers = {
            "Content-Type": "application/json",
            "x-api-key": API_KEY
        }

        with st.spinner("Выполняется предикт через сервис..."):
            try:
                response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            except Exception as e:
                st.error(f"Ошибка при вызове API: {e}")
                return

        if response.status_code != 200:
            st.error(f"Ошибка от сервиса: {response.status_code}, {response.text}")
            return

        try:
            response_json = response.json()
        except Exception as e:
            st.error(f"Ошибка декодирования ответа: {e}")
            return

        st.success("Предикт успешно выполнен!")
        st.markdown("#### Результаты предикта:")
        st.json(response_json)

        # Если предсказания присутствуют, создаём CSV для скачивания
        if "predictions" in response_json:
            predictions = response_json["predictions"]
            df = pd.DataFrame({"isRadiant_win": predictions})
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            st.download_button(
                label="Скачать результаты предикта (CSV)",
                data=csv_data,
                file_name="predictions.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    app()
