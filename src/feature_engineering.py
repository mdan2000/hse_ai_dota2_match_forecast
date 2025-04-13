import pandas as pd
import numpy as np


def compute_team_stat_ratios(df: pd.DataFrame, stat: str) -> pd.DataFrame:
    """
    Вычисляет отношение среднего значения статистики (stat) для команды Radiant к
    средней статистике для Dire по каждому матчу.
    
    Аргументы:
      df: DataFrame с данными игроков. Должен содержать колонки:
          - 'match_id' – идентификатор матча,
          - 'isRadiant' – булев признак (True для Radiant, False для Dire),
          - stat – статистика, по которой вычисляется отношение (например, 'gold_per_min').
      stat: имя колонки со статистикой.
      
    Возвращает:
      DataFrame с колонками 'match_id' и '{stat}_ratio', где отношение вычислено как
      (среднее значение stat для Radiant) / (среднее значение stat для Dire).
    """
    required = {'match_id', 'isRadiant', stat}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame должен содержать колонки: {required}")
    
    # Считаем среднее значение stat по командам для каждого матча
    team_means = df.groupby(['match_id', 'isRadiant'])[stat].mean().reset_index()
    # Переформатируем в виде pivot-таблицы:
    pivot = team_means.pivot(index='match_id', columns='isRadiant', values=stat).reset_index()
    # После pivot получаем столбцы: match_id, False, True, где False — Dire, True — Radiant
    pivot = pivot.rename(columns={False: f'dire_{stat}', True: f'radiant_{stat}'})
    # Вычисляем отношение – если dire_stat равен 0, результат будет NaN
    pivot[f'{stat}_ratio'] = pivot[f'radiant_{stat}'] / pivot[f'dire_{stat}'].replace(0, np.nan)
    return pivot[['match_id', f'{stat}_ratio']]


def hero_role_distribution(df: pd.DataFrame, hero_role_mapping: dict = None) -> pd.DataFrame:
    """
    Вычисляет распределение ролей для каждого hero_id как процентное соотношение матчей,
    в которых герой играл на каждой роли.
    
    Аргументы:
      df: DataFrame должен содержать колонки 'hero_id' и 'lane_role'.
          (lane_role – роль игрока на линии, например, 'carry', 'mid', 'support' и т.д.)
      hero_role_mapping: опционально, словарь, сопоставляющий hero_id с типичными ролями.
          Если передан, его можно использовать для дополнительной обработки.
          
    Возвращает:
      DataFrame, где для каждого hero_id указаны доли игр по каждому значению lane_role.
    """
    if 'hero_id' not in df.columns or 'lane_role' not in df.columns:
        raise ValueError("DataFrame должен содержать колонки 'hero_id' и 'lane_role'.")
    
    # Считаем число матчей по комбинации hero_id и lane_role
    role_counts = df.groupby(['hero_id', 'lane_role']).size().unstack(fill_value=0)
    # Вычисляем долю по каждой роли для hero_id
    role_distribution = role_counts.div(role_counts.sum(axis=1), axis=0).reset_index()
    # Если задан hero_role_mapping, можно добавить информацию, но здесь просто возвращаем распределение
    return role_distribution


def is_main_position_player(df: pd.DataFrame, main_roles: list = None) -> pd.Series:
    """
    Определяет, считается ли игрок, играющий на определенной позиции, играющим на мейн позиции.
    
    Аргументы:
      df: DataFrame, содержащий колонку 'lane_role'.
      main_roles: Список ролей, которые считаются мейн (например, ['carry', 'mid']).
                  По умолчанию, если не задан, считаем главными роли 'carry' и 'mid'.
                  
    Возвращает:
      pd.Series с булевыми значениями: True, если lane_role входит в main_roles, иначе False.
    """
    if main_roles is None:
        main_roles = ['carry', 'mid']
    if 'lane_role' not in df.columns:
        raise ValueError("DataFrame должен содержать колонку 'lane_role'.")
    return df['lane_role'].isin(main_roles)


def compute_position_winrates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисляет винрейты (winrate) для каждого hero_id по позиции (lane_role).
    
    Аргументы:
      df: DataFrame должен содержать колонки 'hero_id', 'lane_role' и 'win'
          (win – бинарный признак, где True означает победу, а False – поражение).
          
    Возвращает:
      DataFrame с колонками 'hero_id', 'lane_role' и 'winrate_position'.
    """
    if not {'hero_id', 'lane_role', 'win'}.issubset(df.columns):
        raise ValueError("DataFrame должен содержать колонки 'hero_id', 'lane_role' и 'win'.")
    
    grouped = df.groupby(['hero_id', 'lane_role'])['win'].mean().reset_index()
    grouped = grouped.rename(columns={'win': 'winrate_position'})
    return grouped


def compute_overall_hero_winrate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисляет общий винрейт для каждого hero_id.
    
    Аргументы:
      df: DataFrame должен содержать колонки 'hero_id' и 'win'.
      
    Возвращает:
      DataFrame с колонками 'hero_id' и 'hero_overall_winrate'.
    """
    if not {'hero_id', 'win'}.issubset(df.columns):
        raise ValueError("DataFrame должен содержать колонки 'hero_id' и 'win'.")
    
    overall = df.groupby('hero_id')['win'].mean().reset_index()
    overall = overall.rename(columns={'win': 'hero_overall_winrate'})
    return overall


def compare_player_vs_hero_winrate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Сравнивает винрейт игрока, играющего за определенного героя, с общим винрейтом этого героя.
    
    Аргументы:
      df: DataFrame должен содержать колонки 'player_id', 'hero_id' и 'win'.
      
    Возвращает:
      DataFrame с колонками 'player_id', 'hero_id', 'player_winrate', 'hero_overall_winrate' и 'winrate_diff'
      (разница между винрейтом игрока и общим винрейтом героя).
    """
    required = {'player_id', 'hero_id', 'win'}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame должен содержать колонки: {required}")
    
    # Вычисляем винрейт для пары player-hero
    player_hero = df.groupby(['player_id', 'hero_id'])['win'].mean().reset_index()
    player_hero = player_hero.rename(columns={'win': 'player_winrate'})
    # Вычисляем общий винрейт для каждого героя
    overall = compute_overall_hero_winrate(df)
    # Объединяем данные
    merged = pd.merge(player_hero, overall, on='hero_id', how='left')
    merged['winrate_diff'] = merged['player_winrate'] - merged['hero_overall_winrate']
    return merged


def compute_team_vs_team_winrate(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисляет винрейт команд Radiant и Dire на основе результатов матчей.
    
    Аргументы:
      matches_df: DataFrame, содержащий колонки 'match_id' и 'radiant_win'
                  (radiant_win – булев признак: True, если Radiant выиграли, False, если Dire).
                  
    Возвращает:
      DataFrame с двумя колонками: 'radiant_winrate' и 'dire_winrate'.
    """
    if not {'match_id', 'radiant_win'}.issubset(matches_df.columns):
        raise ValueError("matches_df должен содержать колонки 'match_id' и 'radiant_win'.")
    
    total_matches = matches_df.shape[0]
    radiant_wins = matches_df['radiant_win'].sum()  # True преобразуется в 1, False в 0
    dire_wins = total_matches - radiant_wins
    data = {
        'radiant_winrate': radiant_wins / total_matches,
        'dire_winrate': dire_wins / total_matches
    }
    return pd.DataFrame([data])


def aggregate_team_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Агрегирует командные метрики для каждого матча.
    
    Аргументы:
      df: DataFrame должен содержать колонки:
          - 'match_id'
          - 'isRadiant' (True для Radiant, False для Dire)
          - 'kda', 'gold_per_min', 'xp_per_min', 'tower_damage'
          
    Возвращает:
      DataFrame с суммарными и средними значениями указанных метрик для каждой команды в каждом матче.
    """
    required = {'match_id', 'isRadiant', 'kda', 'gold_per_min', 'xp_per_min', 'tower_damage'}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame должен содержать колонки: {required}")
    
    aggregated = df.groupby(['match_id', 'isRadiant']).agg({
        'kda': ['sum', 'mean'],
        'gold_per_min': ['sum', 'mean'],
        'xp_per_min': ['sum', 'mean'],
        'tower_damage': ['sum', 'mean']
    })
    # Преобразуем мультииндекс колонок в обычные имена
    aggregated.columns = ['_'.join(col) for col in aggregated.columns]
    aggregated = aggregated.reset_index()
    return aggregated


def compute_comeback_throw_stats(matches_df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Вычисляет агрегированную статистику по камбэкам (comeback) и сливам (throw) для матчей.
    Для каждого матча флаги камбэка/слива определяются по пороговому значению.
    
    Аргументы:
      matches_df: DataFrame, содержащий колонки 'match_id', 'comeback' и 'throw'
                  (значения comeback и throw – вероятности или оценки, от 0 до 1).
      threshold: пороговое значение для определения, произошёл ли камбэк или слив.
      
    Возвращает:
      DataFrame с долями матчей, в которых произошёл камбэк (comeback_rate) и слив (throw_rate).
    """
    for col in ['comeback', 'throw']:
        if col not in matches_df.columns:
            raise ValueError(f"DataFrame должен содержать колонку '{col}'")
    
    # Создаем бинарные индикаторы для камбэка и слива
    matches_df = matches_df.copy()
    matches_df['comeback_flag'] = matches_df['comeback'] >= threshold
    matches_df['throw_flag'] = matches_df['throw'] >= threshold
    comeback_rate = matches_df['comeback_flag'].mean()
    throw_rate = matches_df['throw_flag'].mean()
    data = {
        'comeback_rate': comeback_rate,
        'throw_rate': throw_rate
    }
    return pd.DataFrame([data])