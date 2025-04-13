import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

def load_data(file_path: str) -> pd.DataFrame:
    """
    Загружает данные из CSV и оставляет только нужные колонки согласно шаблону.
    """
    df = pd.read_csv(file_path)
    if 'Unnamed: 0' in df.columns:
        df.drop('Unnamed: 0', axis=1, inplace=True)
    patterns = [
        "draft", "account_id_", "party_id", "hero_variant", "name_", 
        "isRadiant_", "rank_tier_", "game_mode", "lobby_type", "start_time",
        "lane_", "is_roaming", "version", "series_type", "patch", "region", 
        "radiant_win"
    ]
    cols_to_keep = [col for col in df.columns if any(pattern in col for pattern in patterns)]
    df = df[cols_to_keep]
    return df

def get_features(df: pd.DataFrame):
    """
    Разделяет признаки и целевую переменную.
    """
    X = df.drop(columns=['radiant_win'])
    y = df['radiant_win']
    return X, y

def get_numeric_categorical_features(X: pd.DataFrame):
    """
    Определяет числовые и категориальные признаки.
    """
    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X.select_dtypes(exclude=[np.number]).columns.tolist()
    return numeric_features, categorical_features

def build_preprocessor(numeric_features, categorical_features):
    """
    Создает ColumnTransformer для числовых и категориальных признаков.
    """
    numeric_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])
    
    categorical_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_pipeline, numeric_features),
            ('cat', categorical_pipeline, categorical_features)
        ]
    )
    return preprocessor