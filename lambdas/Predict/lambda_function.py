# pylint: disable=R0914, R0911, R0912

import io
import json
import pickle
import pandas as pd

import boto3


def lambda_handler(event, _context):
    """
    Лямбда для получения предсказания на данных
        - Входные параметры:
            - model_name - используемая для predict модель
            - data_path - путь к данным на s3 bucket
    """
    s3_bucket = "dmyachin-new-models"
    s3_client = boto3.client("s3")

    # Если вызов через API Gateway, тело запроса передается в event["body"]
    if "body" in event:
        try:
            body = json.loads(event["body"])
        except Exception as e:  # pylint: disable=broad-exception-caught
            return {
                "statusCode": 400,
                "body": json.dumps(f"Неверный формат JSON в body: {str(e)}")
            }
    else:
        body = event

    # Получаем model_name из запроса.
    model_name = body.get("model_name")
    if not model_name:
        # Если параметр model_name отсутствует, пытаемся получить его из DynamoDB
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table("Models")
            response = table.get_item(Key={"main_model": "real_model"})
            item = response.get("Item")
            if item and "setted_model" in item:
                model_name = item["setted_model"]
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps("Не передан model_name и не удалось получить его из DynamoDB")
                }
        except Exception as e:  # pylint: disable=broad-exception-caught
            return {
                "statusCode": 500,
                "body": json.dumps(f"Ошибка доступа к DynamoDB: {str(e)}")
            }

    # Формируем ключ для доступа к pickle файлу модели в S3
    model_key = f"models/{model_name}.pkl"

    # Пытаемся получить модель из S3
    try:
        model_obj = s3_client.get_object(Bucket=s3_bucket, Key=model_key)
        model_bytes = model_obj['Body'].read()
        model = pickle.loads(model_bytes)
    except s3_client.exceptions.NoSuchKey:
        return {
            "statusCode": 404,
            "body": json.dumps(f"Модель {model_name} не существует.")
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            "statusCode": 500,
            "body": json.dumps(f"Ошибка при получении модели из S3: {str(e)}")
        }

    # Получаем data_path из запроса
    data_path = body.get("data_path")
    if not data_path:
        return {
            "statusCode": 400,
            "body": json.dumps("Не передан параметр data_path")
        }

    # Читаем данные. Если data_path начинается с s3://, читаем их из S3, иначе предполагаем локальный путь.
    if data_path.startswith("s3://"):
        try:
            parts = data_path.replace("s3://", "").split("/", 1)
            data_bucket = parts[0]
            data_key = parts[1]
            data_obj = s3_client.get_object(Bucket=data_bucket, Key=data_key)
            data_bytes = data_obj['Body'].read()
            data = pd.read_csv(io.BytesIO(data_bytes))
        except Exception as e:  # pylint: disable=broad-exception-caught
            return {
                "statusCode": 500,
                "body": json.dumps(f"Ошибка при чтении файла данных из S3: {str(e)}")
            }
    else:
        try:
            data = pd.read_csv(data_path)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return {
                "statusCode": 500,
                "body": json.dumps(f"Ошибка при чтении локального файла данных: {str(e)}")
            }

    # Выполнение предсказания
    try:
        predictions = model['pipeline'].predict(data)
        if hasattr(predictions, "tolist"):
            predictions = predictions.tolist()
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            "statusCode": 500,
            "body": json.dumps(f"Ошибка при выполнении предсказания: {str(e)}")
        }

    # Возвращаем результат
    return {
        "statusCode": 200,
        "body": json.dumps({"predictions": predictions})
    }
