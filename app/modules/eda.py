import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.logger import logger

# Функция для получения списка столбцов по префиксу
def get_columns_by_prefix(df, prefix):
    return [col for col in df.columns if col.startswith(prefix)]

# Функция для построения интерактивной гистограммы для объединённых столбцов по префиксу
def plot_group_distribution(df, prefix):
    cols = get_columns_by_prefix(df, prefix)
    if not cols:
        return None
    # Приводим данные к одному столбцу
    melted = df[cols].melt(var_name="variable", value_name="value")
    fig = px.histogram(melted, x="value", nbins=30,
                       title=f"Распределение для {prefix[:-1]} (объединено)",
                       labels={"value": prefix[:-1]})
    return fig

def app():
    st.title("Анализ данных (EDA)")
    if 'df' not in st.session_state or st.session_state.df is None:
        st.warning("Сначала загрузите датасет в разделе 'Загрузка датасета'")
        return

    with st.spinner("Грузим данные для анализа..."):
        # Копируем датасет и удаляем лишний столбец, если он есть
        data = st.session_state.df.copy()
        if 'Unnamed: 0' in data.columns:
            data.drop('Unnamed: 0', axis=1, inplace=True)

        # --- Базовый анализ ---
        st.subheader("Базовый анализ данных")
        st.write(f"**Размер датасета:** {data.shape[0]} строк, {data.shape[1]} столбцов")
        # Топ-10 столбцов с пропусками (по количеству пропусков)
        missing_counts = data.isnull().sum()
        top10_missing = missing_counts[missing_counts > 0].sort_values(ascending=False).head(10)
        st.write("**Топ-10 столбцов с пропусками:**")
        st.write(top10_missing)
        # Разбивка столбцов по проценту пропусков
        missing_percent = data.isnull().mean() * 100  # процент пропусков для каждого столбца
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = ["0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
        missing_bins = pd.cut(missing_percent, bins=bins, labels=labels, include_lowest=True)
        bin_counts = missing_bins.value_counts().sort_index()
        st.write("**Разбивка столбцов по проценту пропусков:**")
        for interval, count in bin_counts.items():
            st.write(f"{count} столбцов имеют пропуски в диапазоне {interval}")
        
        # --- Распределение класса radiant_win ---
        if 'radiant_win' in data.columns:
            st.subheader("Распределение класса **radiant_win**")
            fig = px.histogram(data, x="radiant_win", color="radiant_win",
                               title="Распределение radiant_win",
                               labels={"radiant_win": "Radiant Win"})
            st.plotly_chart(fig)
        else:
            st.warning("Столбец 'radiant_win' отсутствует в датасете.")
        
        # --- Распределение непрерывных признаков ---
        st.subheader("Распределение непрерывных признаков")
        continuous_cols = ['duration_in_min', 'first_blood_time_in_min', 'dire_score', 'radiant_score']
        for col in continuous_cols:
            if col in data.columns:
                fig = px.histogram(data, x=col, nbins=30,
                                   title=f"Распределение {col}",
                                   labels={col: col})
                st.plotly_chart(fig)
            else:
                st.info(f"Столбец {col} отсутствует в датасете.")
        
        # --- Корреляционная матрица ---
        st.subheader("Корреляционная матрица")
        cols_corr = ['barracks_status_dire', 'barracks_status_radiant', 'dire_score', 'duration', 
                     'first_blood_time', 'match_seq_num', 'radiant_score', 'radiant_win', 
                     'tower_status_dire', 'tower_status_radiant', 'patch', 'throw', 
                     'comeback', 'loss', 'win', 'duration_in_min', 'first_blood_in_min']
        cols_corr = [col for col in cols_corr if col in data.columns]
        if cols_corr:
            corr_matrix = data[cols_corr].corr(numeric_only=True)
            fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                                 title="Корреляционная матрица")
            st.plotly_chart(fig_corr)
        else:
            st.warning("Нет столбцов для построения корреляционной матрицы.")
        
        # --- Описательная статистика ---
        st.subheader("Описательная статистика")
        cols_to_drop = [col for col in data.columns if col.startswith("radiant_xp_adv") 
                        or col.startswith("draft") or col.startswith("player_slot")]
        desc_df = data.drop(columns=cols_to_drop, errors='ignore').describe(include="all")
        st.write(desc_df)
        
        # --- Графики распределения для показателей нескольких игроков (без leaver_status) ---
        st.subheader("Графики распределения для показателей нескольких игроков")
        prefixes = ["assists_", "camps_stacked_", "deaths_", "denies_", 
                    "hero_damage_", "hero_healing_", "last_hits_", "obs_placed_", "pings_"]
        for prefix in prefixes:
            fig = plot_group_distribution(data, prefix)
            if fig is not None:
                st.plotly_chart(fig)
            else:
                st.info(f"Столбцы с префиксом {prefix} не найдены.")
        
        # --- Новые парные графики (без дополнительного измерения) ---
        st.subheader("Парные графики")
        # 1. Duration in min vs First Blood Time in min
        if all(col in data.columns for col in ["duration_in_min", "first_blood_time_in_min"]):
            fig1 = px.scatter(data, x="duration_in_min", y="first_blood_time_in_min",
                              title="Duration in min vs First Blood Time in min")
            st.plotly_chart(fig1)
        else:
            st.info("Не найдены столбцы для графика 1.")
        
        # 2. Dire Score vs Radiant Score
        if all(col in data.columns for col in ["dire_score", "radiant_score"]):
            fig2 = px.scatter(data, x="dire_score", y="radiant_score",
                              title="Dire Score vs Radiant Score")
            st.plotly_chart(fig2)
        else:
            st.info("Не найдены столбцы для графика 2.")
        
        # 3. Mean Duration vs Patch (столбчатый график)
        if all(col in data.columns for col in ["patch", "duration_in_min"]):
            group_df = data.groupby("patch", as_index=False)["duration_in_min"].mean()
            fig3 = px.bar(group_df, x="patch", y="duration_in_min",
                          title="Mean Duration vs Patch",
                          labels={"duration_in_min": "Mean Duration (in min)"})
            st.plotly_chart(fig3)
        else:
            st.info("Не найдены столбцы для графика 3.")
        
        # 4. Количество пингов vs Duration in min
        pings_cols = get_columns_by_prefix(data, "pings_")
        if pings_cols and "duration_in_min" in data.columns:
            # Агрегируем значения пингов по строкам (например, суммируя все pings_*)
            data["agg_pings"] = data[pings_cols].sum(axis=1)
            fig4 = px.scatter(data, x="agg_pings", y="duration_in_min",
                      title="Aggregated Pings vs Duration in min",
                      labels={"agg_pings": "Total Pings", "duration_in_min": "Duration (min)"})
            st.plotly_chart(fig4)
        else:
            st.info("Столбцы с пингами не найдены.")

        # 5. Obs placed vs Camps Stacked
        obs_cols = get_columns_by_prefix(data, "obs_placed_")
        camps_cols = get_columns_by_prefix(data, "camps_stacked_")
        if obs_cols and camps_cols:
            # Агрегируем значения: суммарное количество obs_placed и camps_stacked для каждого матча
            data["agg_obs"] = data[obs_cols].sum(axis=1)
            data["agg_camps"] = data[camps_cols].sum(axis=1)
            fig5 = px.scatter(data, x="agg_obs", y="agg_camps",
                      title="Aggregated Obs Placed vs Camps Stacked",
                      labels={"agg_obs": "Total Obs Placed", "agg_camps": "Total Camps Stacked"})
            st.plotly_chart(fig5)
        else:
            st.info("Столбцы для Obs placed или Camps Stacked не найдены.")
        logger.info("EDA выполнено")
    st.success("Анализ данных завершён.")
