import os
import streamlit as st
import requests
import base64
import pickle
import plotly.graph_objects as go
import boto3
from botocore.exceptions import ClientError
from utils.logger import logger

def app():
    st.title("Сравнение экспериментов")

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
    
    with st.spinner("Получаем список экспериментов..."):
        try:
            response = requests.get(url, json={}, headers=headers, timeout=29)
        except Exception as e:
            st.error(f"Ошибка запроса к API: {e}")
            return

    if response.status_code != 200:
        st.error(f"Ошибка запроса к API: {response.status_code}, {response.text}")
        return

    experiments_list = response.json()
    if not experiments_list:
        st.warning("Список экспериментов пуст.")
        return

    # Фильтрация экспериментов: оставляем только нужные
    allowed_models = [
        "DecisionTreeClassifier_experiment_5.pkl",
        "DecisionTreeClassifier_experiment_6.pkl",
        "LogisticRegression_experiment_1.pkl",
        "LogisticRegression_experiment_2.pkl",
        "SGDClassifier_experiment_3.pkl",
        "SGDClassifier_experiment_4.pkl"
    ]

    # Строим словарь для multiselect: ключ – отображаемое имя (последняя часть s3_key), значение – объект эксперимента
    options = {}
    for exp in experiments_list:
        s3_key = exp.get("s3_key")
        display_name = s3_key.split("/")[-1] if s3_key else exp.get("key", "Unknown")
        if display_name not in allowed_models:
            continue
        options[display_name] = exp

    if not options:
        st.warning("Нет доступных экспериментов для сравнения.")
        return

    selected_experiments = st.multiselect("Выберите эксперименты для сравнения", list(options.keys()), default=list(options.keys()))
    logger.info("Пользователь выбрал эксперименты для сравнения: %s", selected_experiments)

    if not selected_experiments:
        st.info("Выберите хотя бы один эксперимент для сравнения.")
        logger.info("Пользователь не выбрал эксперименты для сравнения")
        return

    # Получаем AWS ключи из переменных окружения
    aws_access_key_id = st.secrets["general"]["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = st.secrets["general"]["AWS_SECRET_ACCESS_KEY"]
    if not aws_access_key_id or not aws_secret_access_key:
        st.error("AWS ключи не настроены. Пожалуйста, настройте их в Streamlit Secrets.")
        return

    bucket_name = "dmyachin-new-models"
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    # Создаем пустую фигуру для построения графика
    fig = go.Figure()

    # Загружаем для каждого выбранного эксперимента данные и добавляем линию (валидационная кривая)
    for display_name in selected_experiments:
        exp_info = options[display_name]
        s3_key = exp_info.get("s3_key")
        if not s3_key:
            st.warning(f"Не найден s3_key для эксперимента {display_name}")
            continue

        with st.spinner(f"Загружаем эксперимент {display_name}..."):
            try:
                response_s3 = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                model_data = response_s3["Body"].read()
                experiment = pickle.loads(model_data)
                logger.info("Эксперимент %s успешно загружен с S3", display_name)
            except ClientError as e:
                st.error(f"Ошибка при загрузке эксперимента {display_name} с S3: {e}")
                continue
            except Exception as e:
                st.error(f"Ошибка десериализации эксперимента {display_name}: {e}")
                continue

        # Извлекаем данные кривой обучения (используем валидационные значения)
        lc = experiment.get("learning_curve")
        if not lc:
            st.warning(f"Кривая обучения отсутствует в эксперименте {display_name}")
            continue

        train_sizes = lc.get("train_sizes")
        val_scores = lc.get("val_scores")
        if not train_sizes or not val_scores:
            st.warning(f"Некорректные данные кривой обучения в эксперименте {display_name}")
            continue

        exp_label = f"{experiment.get('model', 'Unknown')} (ID {experiment.get('experiment_id', 'N/A')})"
        fig.add_trace(
            go.Scatter(
                x=train_sizes,
                y=val_scores,
                mode="lines",
                name=exp_label
            )
        )

    if fig.data:
        fig.update_layout(
            title="Сравнение кривых обучения (валидация)",
            xaxis_title="Размер обучающей выборки",
            yaxis_title="Score"
        )
        st.plotly_chart(fig)
        logger.info("Построена сравнительная кривая обучения для выбранных экспериментов")
    else:
        st.info("Нет данных для отображения сравнительной кривой обучения.")

if __name__ == "__main__":
    app()
