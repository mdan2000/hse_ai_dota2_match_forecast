from tpot import TPOTClassifier
import wandb
import os
import pickle
from datetime import datetime
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

def run_tpot_experiment(X_train, y_train, X_test, y_test, experiment_id: int, generations=5, population_size=20):
    """
    Запускает AutoML-эксперимент с использованием TPOTClassifier,
    настроенного через кастомную конфигурацию без тяжёлых моделей.
    """
    wandb.init(project="ml_experiments", name=f"TPOT_exp_{experiment_id}", reinit=True)
    
    # Кастомная конфигурация: ограничиваемся лёгкими моделями
    custom_config = {
        'sklearn.linear_model.LogisticRegression': {
            'penalty': ['l1', 'l2'],
            'C': [0.1, 1.0, 10],
            'solver': ['liblinear']
        },
        'sklearn.tree.DecisionTreeClassifier': {
            'criterion': ['gini', 'entropy'],
            'max_depth': [None, 5, 10]
        },
        'sklearn.naive_bayes.GaussianNB': {},
        # Можно добавить и другие легковесные модели
    }
    
    tpot = TPOTClassifier(generations=generations,
                          population_size=population_size,
                          verbosity=2,
                          config_dict=custom_config,
                          random_state=42,
                          n_jobs=-1)
    tpot.fit(X_train, y_train)
    y_pred = tpot.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred).tolist()
    class_report = classification_report(y_test, y_pred, output_dict=True)
    
    wandb.log({
        "TPOT_test_accuracy": acc,
        "TPOT_confusion_matrix": conf_matrix,
        "TPOT_classification_report": class_report
    })
    
    # Сохранение эксперимента
    if not os.path.exists("experiments"):
        os.makedirs("experiments")
    experiment = {
        "model": "TPOTClassifier",
        "pipeline": tpot.fitted_pipeline_,
        "test_score": acc,
        "confusion_matrix": conf_matrix,
        "classification_report": class_report,
        "timestamp": datetime.now().isoformat(),
        "experiment_id": experiment_id
    }
    filename = os.path.join("experiments", f"TPOT_experiment_{experiment_id}.pkl")
    with open(filename, "wb") as f:
        pickle.dump(experiment, f)
    print(f"Сохранен TPOT эксперимент: {filename}")
    wandb.finish()