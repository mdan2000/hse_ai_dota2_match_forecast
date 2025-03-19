import json
import pickle

import pandas as pd
from sklearn.linear_model import LogisticRegression, SGDClassifier

import boto3
from botocore.exceptions import ClientError


s3 = boto3.client('s3')
BUCKET_NAME = "dmyachin-new-models"


def lambda_handler(event, _context):  # pylint: disable=too-many-return-statements
    """
    Лямбда-функция для работы с моделями:

    1. Если в event передан параметр "model_name":
       - Загружает из S3 объект по ключу "models/{model_name}".
       - Если файла нет, возвращает ошибку.
       - Если найден, возвращает сообщение об успешной загрузке.

    2. Если "model_name" отсутствует:
       - Ожидает наличие параметров "new_model_name", "model_params" и "model_type".
       - Параметр "model_type" может принимать значения "LogisticRegression" или "SGDClassifier".
       - Загружает данные из S3 по пути "data/small_df.csv".
         В данных целевая переменная должна быть в столбце "target",
         а остальные столбцы используются как признаки.
       - Создаёт модель соответствующего типа, передавая model_params в конструктор.
       - Обучает модель (fit).
       - Сериализует модель в pickle и сохраняет её в S3 по ключу "models/{new_model_name}".
       - Возвращает "OK".
    """
    try:
        body = event.get('body')
        # Если тело запроса представлено строкой, парсим его как JSON
        if isinstance(body, str):
            event = json.loads(body)
    except Exception:  # pylint: disable=broad-exception-caught
        return {
            'statusCode': 400,
            'body': json.dumps('Неверный формат тела запроса')
        }

    try:
        data_key = "data/small_df.csv"
        response = s3.get_object(Bucket=BUCKET_NAME, Key=data_key)
        df = pd.read_csv(response['Body'])

        # Проверяем наличие целевого столбца
        if "target" not in df.columns:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "В данных отсутствует столбец 'target'."})
            }

        y = df["target"]
        X = df.drop(columns=["target"])

        # Если передан параметр model_name, загружаем модель
        if "model_name" in event:
            model_name = event["model_name"]
            new_model_name = model_name
            key = f"models/{model_name}.pkl"
            try:
                response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            except ClientError as e:
                if e.response['Error']['Code'] == "NoSuchKey":
                    return {
                        "statusCode": 404,
                        "body": json.dumps({"error": f"Файл с именем {model_name} не найден."})
                    }
                return {
                    "statusCode": 501,
                    "body": json.dumps({"error": str(e)})
                }

            # Десериализуем модель, если требуется
            model = pickle.loads(response['Body'].read())['pipeline']

        # Если параметр model_name отсутствует, создаём и обучаем новую модель
        else:
            new_model_name = event.get("new_model_name")
            model_params = event.get("model_params", {})
            model_type = event.get("model_type")

            if not new_model_name or not model_params or not model_type:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {"error": "Отсутствуют необходимые параметры new_model_name, model_params или model_type."})
                }

            # Проверяем, что model_type корректный
            if model_type not in ["LogisticRegression", "SGDClassifier"]:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "model_type должен быть LogisticRegression или SGDClassifier."})
                }

            # Создаем модель в зависимости от model_type
            if model_type == "LogisticRegression":
                model = LogisticRegression(**model_params)
            elif model_type == "SGDClassifier":
                model = SGDClassifier(**model_params)
            else:
                return {
                    "statusCode": 502,
                    "body": json.dumps({"error": "Strange model type input"})
                }

            # Обучаем модель
        model.fit(X, y)

        # Сериализуем модель в pickle
        model_pickle = pickle.dumps(model)

        # Сохраняем модель в S3
        dest_key = f"models/{new_model_name}.pkl"
        s3.put_object(Bucket=BUCKET_NAME, Key=dest_key, Body=model_pickle)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "OK"})
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
