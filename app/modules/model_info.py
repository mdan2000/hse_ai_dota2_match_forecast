import os
import streamlit as st
import requests
import base64
import pickle
import plotly.express as px
import plotly.graph_objects as go
import boto3
from botocore.exceptions import ClientError
from utils.logger import logger

def app():
    st.title("Информация о модели и кривые обучения")
    
    # Получаем API ключ из переменных окружения
    API_KEY = st.secrets["general"]["API_KEY"]
    if not API_KEY:
        st.error("API_KEY не настроен. Пожалуйста, настройте его в Streamlit Secrets.")
        return

    url = 'https://abkfijydkg.execute-api.us-east-1.amazonaws.com/dev/dev-getmodel'
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    with st.spinner("Получаем список моделей из API..."):
        try:
            response = requests.get(url, json={}, headers=headers, timeout=29)
        except Exception as e:
            st.error(f"Ошибка запроса к API: {e}")
            return
    
    if response.status_code != 200:
        st.error(f"Ошибка запроса к API: {response.status_code}, {response.text}")
        return
    
    models_info = response.json()
    if not models_info:
        st.warning("Список моделей пуст.")
        return

    # Фильтрация моделей: оставляем только нужные
    allowed_models = [
        "DecisionTreeClassifier_experiment_5.pkl",
        "DecisionTreeClassifier_experiment_6.pkl",
        "LogisticRegression_experiment_1.pkl",
        "LogisticRegression_experiment_2.pkl",
        "SGDClassifier_experiment_3.pkl",
        "SGDClassifier_experiment_4.pkl"
    ]

    # Строим выпадающий список. Для отображения используем имя файла из s3_key
    options = {}
    for model in models_info:
        s3_key = model.get("s3_key")
        if s3_key:
            display_name = s3_key.split("/")[-1]
        else:
            display_name = model.get("key", "Unknown")
        if display_name not in allowed_models:
            continue
        options[display_name] = model

    if not options:
        st.warning("Нет доступных моделей для отображения.")
        return

    selected_display = st.selectbox("Выберите эксперимент", list(options.keys()))
    selected_model = options[selected_display]
    logger.info("Пользователь выбрал эксперимент: %s", selected_display)

    # Получаем AWS ключи из переменных окружения
    aws_access_key_id = st.secrets["general"]["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = st.secrets["general"]["AWS_SECRET_ACCESS_KEY"]
    if not aws_access_key_id or not aws_secret_access_key:
        st.error("AWS ключи не настроены. Пожалуйста, настройте их в Streamlit Secrets.")
        return

    bucket_name = "dmyachin-new-models"
    s3_key = selected_model.get("s3_key")
    if not s3_key:
        st.error("Не найден s3_key для выбранной модели.")
        return

    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    with st.spinner(f"Загружаем модель {selected_display} из S3..."):
        try:
            response_s3 = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            model_data = response_s3["Body"].read()
            experiment = pickle.loads(model_data)
            logger.info("Файл успешно загружен с S3: %s", s3_key)
        except ClientError as e:
            st.error(f"Ошибка при загрузке файла с S3: {e}")
            return
        except Exception as e:
            st.error(f"Ошибка десериализации модели: {e}")
            return

    # Отображаем информацию о модели
    st.write("**Модель:**", experiment.get("model"))
    st.write("**Гиперпараметры:**", experiment.get("params"))
    st.write("**Доля правильных ответов (Accuracy):**", experiment.get("test_score"))

    precision = experiment.get("classification_report", {}).get("weighted avg", {}).get("precision", None)
    if precision is not None:
        st.write("**Точность (Precision):**", precision)
    else:
        st.write("**Отчет по классификации:**", experiment.get("classification_report"))
    
    st.write("**Время эксперимента:**", experiment.get("timestamp"))
    st.write("**ID эксперимента:**", experiment.get("experiment_id"))
    logger.info("Отображены детали эксперимента ID %s", experiment.get("experiment_id"))

    # Построение матрицы ошибок
    cm = experiment.get("confusion_matrix")
    if cm and isinstance(cm, list) and len(cm) >= 2 and len(cm[0]) >= 2:
        if len(cm) == 2 and len(cm[0]) == 2:
            TN, FP = cm[0]
            FN, TP = cm[1]
            annotations = [[f"TN\n{TN}", f"FP\n{FP}"],
                           [f"FN\n{FN}", f"TP\n{TP}"]]
            fig_cm = go.Figure(data=go.Heatmap(
                z=cm,
                x=["Predicted Negative", "Predicted Positive"],
                y=["True Negative", "True Positive"],
                colorscale='Blues',
                showscale=True
            ))
            for i in range(2):
                for j in range(2):
                    fig_cm.add_annotation(dict(
                        x=["Predicted Negative", "Predicted Positive"][j],
                        y=["True Negative", "True Positive"][i],
                        text=annotations[i][j],
                        showarrow=False,
                        font=dict(color="black")
                    ))
            fig_cm.update_layout(title="Матрица ошибок")
        else:
            fig_cm = px.imshow(cm,
                               text_auto=True,
                               color_continuous_scale='Blues',
                               labels={'x': "Predicted", 'y': "True"},
                               title="Матрица ошибок")
        st.plotly_chart(fig_cm)
        logger.info("Отображена матрица ошибок для эксперимента ID %s", experiment.get("experiment_id"))
    else:
        st.warning("Матрица ошибок отсутствует или имеет некорректный формат.")

    # Построение кривой обучения
    lc = experiment.get("learning_curve")
    if lc:
        fig = px.line(x=lc.get("train_sizes"), y=lc.get("train_scores"),
                      labels={"x": "Размер обучающей выборки", "y": "Score"},
                      title="Кривая обучения")
        fig.add_scatter(x=lc.get("train_sizes"), y=lc.get("val_scores"), mode="lines", name="Validation")
        fig.add_scatter(x=lc.get("train_sizes"), y=lc.get("train_scores"), mode="lines", name="Train")
        st.plotly_chart(fig)
        logger.info("Построена кривая обучения для эксперимента ID %s", experiment.get("experiment_id"))
    else:
        st.warning("Кривая обучения отсутствует или имеет некорректный формат.")

if __name__ == "__main__":
    app()
