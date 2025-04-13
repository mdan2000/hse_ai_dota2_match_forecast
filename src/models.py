import os
import pickle
from datetime import datetime
import numpy as np
import wandb
from sklearn.model_selection import learning_curve
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

def run_experiment(model_name: str, model_pipeline, X_train, y_train, X_test, y_test, experiment_id: int):
    """
    Запускает эксперимент: вычисляет learning curve, обучает модель, делает прогнозы,
    сохраняет результаты эксперимента, а также логирует метрики в wandb.
    """
    wandb.init(project="ml_experiments", name=f"{model_name}_exp_{experiment_id}", reinit=True)
    
    train_sizes, train_scores, val_scores = learning_curve(
        model_pipeline, X_train, y_train,
        cv=3, train_sizes=np.linspace(0.1, 1.0, 10)
    )
    train_scores_mean = np.mean(train_scores, axis=1)
    val_scores_mean = np.mean(val_scores, axis=1)
    
    model_pipeline.fit(X_train, y_train)
    
    y_pred = model_pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred).tolist()
    class_report = classification_report(y_test, y_pred, output_dict=True)
    
    wandb.log({
        "train_sizes": train_sizes.tolist(),
        "train_scores": train_scores_mean.tolist(),
        "val_scores": val_scores_mean.tolist(),
        "test_accuracy": acc,
        "confusion_matrix": conf_matrix,
        "classification_report": class_report,
    })
    
    experiment = {
        "model": model_name,
        "pipeline": model_pipeline,
        "params": model_pipeline.named_steps['classifier'].get_params(),
        "learning_curve": {
            "train_sizes": train_sizes.tolist(),
            "train_scores": train_scores_mean.tolist(),
            "val_scores": val_scores_mean.tolist(),
        },
        "test_score": acc,
        "confusion_matrix": conf_matrix,
        "classification_report": class_report,
        "timestamp": datetime.now().isoformat(),
        "experiment_id": experiment_id
    }
    
    if not os.path.exists("experiments"):
        os.makedirs("experiments")
    filename = os.path.join("experiments", f"{model_name}_experiment_{experiment_id}.pkl")
    with open(filename, "wb") as f:
        pickle.dump(experiment, f)
    print(f"Сохранен эксперимент: {filename}")
    
    wandb.finish()