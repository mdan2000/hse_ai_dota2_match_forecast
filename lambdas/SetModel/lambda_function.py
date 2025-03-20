import json
import logging

import boto3
from botocore.exceptions import ClientError

# Инициализация клиента для работы с S3 и ресурса для DynamoDB
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Имя таблицы DynamoDB, которая служит key-value хранилищем
TABLE_NAME = 'Models'
table = dynamodb.Table(TABLE_NAME)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _context):
    """
    Lambda для установки основной модели для предсказания.
        - Входной параметр model_name
    """
    # Ожидаем, что вызов происходит через API Gateway и данные передаются в теле запроса
    try:
        body = event.get('body')
        # Если тело запроса представлено строкой, парсим его как JSON
        if isinstance(body, str):
            body = json.loads(body)

    except Exception:  # pylint: disable=broad-exception-caught
        return {
            'statusCode': 400,
            'body': json.dumps('Неверный формат тела запроса')
        }

    # Заданные параметры: имя бакета и директория, а имя файла (модели) передается в теле запроса
    bucket = 'dmyachin-new-models'
    directory = 'models'
    file_name = body.get('model_name')

    if not file_name:
        return {
            'statusCode': 400,
            'body': json.dumps('Отсутствует необходимый параметр: model_name')
        }

    # Формируем ключ S3 (путь к файлу)
    s3_key = f"{directory}/{file_name}"

    # Проверяем наличие файла в S3 с использованием list_objects_v2
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=s3_key, MaxKeys=1)
        # Если в ответе отсутствует ключ 'Contents', файл не найден
        if 'Contents' not in response:
            empty_model_name_log = {
                'model_name_exists': False
            }
            logger.info(json.dumps(empty_model_name_log))
            return {
                'statusCode': 404,
                'body': json.dumps('Файл не найден')
            }
    except ClientError as e:  # pylint: disable=broad-exception-caught
        return {
            'statusCode': 500,
            'body': json.dumps(f'Ошибка при проверке файла: {e}')
        }

    # Если файл найден, устанавливаем значение для записи в DynamoDB (например, имя файла)
    dynamodb_value = file_name
    empty_model_name_log = {
        'model_name_exists': True,
        'model_name': file_name
    }
    logger.info(json.dumps(empty_model_name_log))

    # Записываем элемент в DynamoDB. В данном случае используется ключ 'id' с уникальным значением.
    try:
        table.update_item(
            Key={'main_model': 'real_model'},
            UpdateExpression="SET setted_model = :val",
            ExpressionAttributeValues={":val": dynamodb_value}
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            'statusCode': 500,
            'body': json.dumps(f'Ошибка при записи в DynamoDB: {e}')
        }

    return {
        'statusCode': 200,
        'body': json.dumps(f'Успех: значение "{dynamodb_value}" успешно записано в DynamoDB')
    }
