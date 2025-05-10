import streamlit as st
import os
import datetime
import time
import pandas as pd
import numpy as np
import io
import boto3
from botocore.exceptions import ClientError
import requests
import base64

BUCKET_NAME = "dmyachin-new-models"
DATASET_KEY = "data/small_df.csv"  # Файл small_df.csv в S3 содержит столбец target

def load_dataset_from_s3(bucket_name, key):
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id = st.secrets["general"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key = st.secrets["general"]["AWS_SECRET_ACCESS_KEY"]
    )
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        # Если файл сохранён в другой кодировке, можно сменить 'cp1251' на нужную
        content = response["Body"].read().decode('cp1251')
        df = pd.read_csv(io.StringIO(content))
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки {key} из S3: {e}")
        return None

def upload_dataset_to_s3_client(df, bucket_name, key):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id = st.secrets["general"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key = st.secrets["general"]["AWS_SECRET_ACCESS_KEY"]
    )
    try:
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=csv_buffer.getvalue())
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=3600  # ссылка действительна 1 час
        )
        return url
    except ClientError as e:
        st.error(f"Ошибка загрузки датасета в S3: {e}")
        return None

def app():
    st.title("Обучение/Дообучение модели")
    
    # Загружаем датасет small_df.csv из S3
    with st.spinner("Загружаем датасет small_df.csv из S3..."):
        df = load_dataset_from_s3(BUCKET_NAME, DATASET_KEY)
    if df is None:
        st.error("Не удалось загрузить датасет small_df.csv из S3.")
        return

    # Очистка названий столбцов
    df.columns = [col.strip() for col in df.columns]
    if 'Unnamed: 0' in df.columns:
        df.drop('Unnamed: 0', axis=1, inplace=True)
    if "target" not in df.columns:
        if "radiant_win" in df.columns:
            df["target"] = df["radiant_win"]
        else:
            st.error("В датасете отсутствует столбец 'target'.")
            return

    # Выбор режима обучения
    mode = st.radio("Выберите режим обучения", ["Обучение с нуля", "Дообучение существующей модели"])
    st.write("Режим:", mode)
    
    payload = {}
    if mode == "Обучение с нуля":
        st.subheader("Настройка модели")
        # Пользователь выбирает классификатор и задаёт гиперпараметры
        classifier_choice = st.selectbox("Выберите классификатор", ["LogisticRegression", "SGDClassifier"])
        model_params = {}
        if classifier_choice == "LogisticRegression":
            penalty = st.selectbox("Penalty", ["l2", "l1", "elasticnet", "none"])
            C = st.number_input("C (обратная регуляризация)", value=1.0, step=0.1)
            solver = st.selectbox("Solver", ["lbfgs", "saga", "liblinear", "newton-cg"])
            model_params = {"penalty": penalty, "C": C, "solver": solver, "max_iter": 200}
            model_type = "LogisticRegression"
        elif classifier_choice == "SGDClassifier":
            loss = st.selectbox("Loss", ["hinge", "log", "modified_huber", "squared_loss"])
            alpha = st.number_input("Alpha", value=0.0001, step=0.0001, format="%.5f")
            penalty = st.selectbox("Penalty", ["l2", "l1", "elasticnet"])
            learning_rate = st.selectbox("Learning rate", ["optimal", "constant", "invscaling"])
            model_params = {"loss": loss, "alpha": alpha, "penalty": penalty,
                            "learning_rate": learning_rate, "max_iter": 1000, "tol": 1e-3}
            model_type = "SGDClassifier"
        auto_model_name = f"{model_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        payload["new_model_name"] = auto_model_name
        payload["mode"] = "fit"
        payload["model_params"] = model_params
        payload["model_type"] = classifier_choice
        
        # Имитируем этап предобработки – здесь можно оставить логику как раньше
        X = df.drop(columns=['target'])
        y = df['target']
        # Для имитации оставляем исходный датасет (или можно применить реальную предобработку)
        df_preprocessed = df.copy()
        data_key_preprocessed = f"data/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_preprocessed.csv"
        data_url = upload_dataset_to_s3_client(df_preprocessed, BUCKET_NAME, data_key_preprocessed)
        if data_url:
            payload["data_path"] = data_url
        else:
            st.error("Не удалось загрузить предобработанный датасет в S3.")
            return
        
        st.write("Сформированный payload для обучения:")
        st.json(payload)
        
        # Имитация обучения – вместо реального запроса делаем задержку
        if st.button("Запустить обучение"):
            with st.spinner("Модель обучается..."):
                time.sleep(10)  # Имитируем процесс обучения 10 секунд
            dummy_response = {
                "status": "success",
                "message": "Модель успешно обучена!",
                "payload": payload,
                "model_pkl": "ZHVtbXlfbW9kZWxfZGF0YQ=="  # dummy base64 (это строка 'dummy_model_data' в base64)
            }
            st.success("Обучение успешно выполнено!")
            st.markdown("#### Результаты обучения:")
            st.json(dummy_response)
            st.download_button(
                label="Скачать обученную модель (pkl)",
                data=dummy_response["model_pkl"],
                file_name=f"{payload.get('new_model_name')}.pkl",
                mime="application/octet-stream"
            )
    else:
        # Режим "Дообучение существующей модели" – остаётся прежняя логика
        st.subheader("Выберите модель для дообучения")
        allowed_files = {"SGDClassifier_experiment_4.pkl", "LogisticRegression_experiment_1.pkl", "LogisticRegression_experiment_2.pkl"}
        available_files = [f for f in os.listdir("models") if f.endswith(".pkl") and f in allowed_files]
        if not available_files:
            st.warning("Нет сохраненных моделей для дообучения.")
            st.stop()
        selected_file = st.selectbox("Выберите модель для дообучения", available_files)
        model_name_update = selected_file.replace(".pkl", "")
        payload["model_name"] = model_name_update
        payload["mode"] = "update"
        data_path = f"s3://{BUCKET_NAME}/{DATASET_KEY}"
        payload["data_path"] = data_path
        st.write("Сформированный payload для дообучения:")
        st.json(payload)
        
        if st.button("Запустить дообучение"):
            api_url = "https://abkfijydkg.execute-api.us-east-1.amazonaws.com/dev/dev-fitmodel"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": st.secrets["general"]["API_KEY"]
            }
            with st.spinner("Модель дообучается..."):
                try:
                    response = requests.post(api_url, headers=headers, json=payload)
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
            st.success("Модель успешно дообучена!")
            st.markdown("#### Результаты дообучения:")
            st.json(response_json)
            if "model_pkl" in response_json:
                try:
                    model_pkl_bytes = base64.b64decode(response_json["model_pkl"])
                    st.download_button(
                        label="Скачать обученную модель (pkl)",
                        data=model_pkl_bytes,
                        file_name=f"{payload.get('model_name')}.pkl",
                        mime="application/octet-stream"
                    )
                except Exception as e:
                    st.error(f"Ошибка при подготовке файла модели для скачивания: {e}")

if __name__ == "__main__":
    app()
