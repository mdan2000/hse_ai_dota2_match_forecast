import os
import pickle
from datetime import datetime
import numpy as np
import wandb
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

def run_anomaly_detection_experiment(model_name: str, model_pipeline, X_train, y_train, X_test, y_test, experiment_id: int, contamination=0.05):
    """
    Проводит эксперимент по обнаружению и удалению аномалий с использованием IsolationForest,
    затем обучает модель на очищенных данных.
    
    Аргументы:
      model_name: Имя модели (например, 'LogisticRegression' или 'SGDClassifier'), для формирования имени эксперимента.
      model_pipeline: Пайплайн с предобработкой и классификатором.
      X_train, y_train, X_test, y_test: Датасеты.
      experiment_id: Идентификатор эксперимента.
      contamination: Доля аномалий в данных.
    """
    wandb.init(project="ml_experiments", name=f"AnomalyDetection_{model_name}_exp_{experiment_id}", reinit=True)
    
    # Обнаружение аномалий на обучающей выборке (работает с полными данными)
    iso_forest = IsolationForest(contamination=contamination, random_state=42)
    anomaly_preds = iso_forest.fit_predict(X_train)
    # -1: аномалия, 1: нормальное наблюдение
    mask = anomaly_preds == 1
    X_train_clean = X_train[mask]
    y_train_clean = y_train[mask]
    
    # Логируем количество удалённых аномалий
    num_outliers = int(np.sum(anomaly_preds == -1))
    wandb.log({"num_anomalies_removed": num_outliers})
    
    # Обучение модели на очищенных данных
    model_pipeline.fit(X_train_clean, y_train_clean)
    y_pred = model_pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred).tolist()
    class_report = classification_report(y_test, y_pred, output_dict=True)
    
    wandb.log({
        "anomaly_test_accuracy": acc,
        "anomaly_confusion_matrix": conf_matrix,
        "anomaly_classification_report": class_report
    })
    
    experiment = {
        "model": "AnomalyDetection_" + model_name,
        "pipeline": model_pipeline,
        "test_score": acc,
        "confusion_matrix": conf_matrix,
        "classification_report": class_report,
        "num_outliers_removed": num_outliers,
        "timestamp": datetime.now().isoformat(),
        "experiment_id": experiment_id
    }
    
    if not os.path.exists("experiments"):
        os.makedirs("experiments")
    filename = os.path.join("experiments", f"AnomalyDetection_experiment_{experiment_id}.pkl")
    with open(filename, "wb") as f:
        pickle.dump(experiment, f)
    print(f"Сохранен эксперимент по обнаружению аномалий: {filename}")
    
    wandb.finish()