Baseline-пайплайн для прогнозирования исхода матча Dota 2
========================================================

Цель:
- Построить бейзлайн с использованием линейных моделей (Logistic Regression, RidgeClassifier)
  и нескольких лёгких моделей (LinearSVC, DecisionTreeClassifier).
- Удалить признаки, связанные с золотом, опытом и другими «сливовыми» характеристиками,
  так как они утекут в будущем (leakage).
- Разбить данные на train/test и построить полный пайплайн с предобработкой.
- Оценить модели с использованием метрики accuracy (классы примерно сбалансированы).

Описание:
- Данные загружаются из файла `clean_data.csv`.
- Из данных удаляются все признаки, в названии которых встречаются слова "gold" и "xp".
- Используется stratified train/test split с random_state=42.
- Применяется SimpleImputer для заполнения числовых пропусков (стратегия = 'median').
- Используется StandardScaler для нормализации числовых признаков.
- Реализованы четыре модели: Logistic Regression, RidgeClassifier, LinearSVC и DecisionTreeClassifier.
- Для каждой модели производится кросс-валидация и оценка на тестовой выборке.
- Строятся графики: ROC-кривые, confusion matrix, сравнение accuracy.
- Дополнительно проводится GridSearchCV для логистической регрессии для подбора гиперпараметров.
- Метрика accuracy выбрана, так как классы целевой переменной примерно сбалансированы и она легко интерпретируема.

Результаты вышли около 0.52 из-за нехватки достаточного времени на Feature Engineering. Тем не менее, есть большое пространство для улучшения модели!