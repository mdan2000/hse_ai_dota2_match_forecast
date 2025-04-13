import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.decomposition import TruncatedSVD  # Используем TruncatedSVD вместо PCA

import wandb

from src.data_preprocessing import load_data, get_features, get_numeric_categorical_features, build_preprocessor
from src.models import run_experiment
from src.auto_ml import run_tpot_experiment
from src.anomaly_detection import run_anomaly_detection_experiment

def main():
    # Загрузка данных
    df = load_data('/kaggle/input/daotka/result.csv')
    X, y = get_features(df)
    
    # Разбиение данных на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    numeric_features, categorical_features = get_numeric_categorical_features(X_train)
    
    experiment_counter = 1  # Счетчик экспериментов
    
    models_experiments = [
        ("LogisticRegression", LogisticRegression, [
            {"C": 1.0, "penalty": "l2", "solver": "lbfgs", "max_iter": 200},
            {"C": 0.8, "penalty": "l2", "solver": "lbfgs", "max_iter": 200}
        ]),
        ("SGDClassifier", SGDClassifier, [
            {"loss": "hinge", "max_iter": 1000, "tol": 1e-3},
            {"loss": "log", "max_iter": 1000, "tol": 1e-3}
        ]),
        ("DecisionTreeClassifier", DecisionTreeClassifier, [
            {"max_depth": 5, "criterion": "gini"},
            {"max_depth": 7, "criterion": "gini"}
        ])
    ]
    
    # 6 экспериментов без редукции размерности
    for model_name, model_class, params_list in models_experiments:
        for params in params_list:
            classifier = model_class(**params)
            preprocessor = build_preprocessor(numeric_features, categorical_features)
            full_pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', classifier)
            ])
            run_experiment(model_name, full_pipeline, X_train, y_train, X_test, y_test, experiment_counter)
            experiment_counter += 1
            
    # 6 экспериментов с редукцией размерности (используем TruncatedSVD вместо PCA, но имя шага оставляем "pca")
    for model_name, model_class, params_list in models_experiments:
        for params in params_list:
            classifier = model_class(**params)
            preprocessor = build_preprocessor(numeric_features, categorical_features)
            full_pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('pca', TruncatedSVD(n_components=10)),
                ('classifier', classifier)
            ])
            run_experiment(model_name + "_PCA", full_pipeline, X_train, y_train, X_test, y_test, experiment_counter)
            experiment_counter += 1

    # 6 экспериментов по обнаружению аномалий (для каждого набора параметров)
    for model_name, model_class, params_list in models_experiments:
        for params in params_list:
            classifier = model_class(**params)
            preprocessor = build_preprocessor(numeric_features, categorical_features)
            full_pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', classifier)
            ])
            # Передаём model_name для формирования имени эксперимента
            run_anomaly_detection_experiment(model_name, full_pipeline, X_train, y_train, X_test, y_test, experiment_counter, contamination=0.05)
            experiment_counter += 1

    # Эксперимент TPOT
    run_tpot_experiment(X_train, y_train, X_test, y_test, experiment_counter)
    experiment_counter += 1

if __name__ == '__main__':
    main()