import numpy as np
import pandas as pd
import json
import functools
from collections import Counter


def outdated_data(func):
    @functools.wraps(func)  # сохраняет имя и docstring оригинальной функции
    def wrapper(self, *args, **kwargs):
        self.is_data_actual = False
        result = func(self, *args, **kwargs)
        return result
    return wrapper

def uptodated_data(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        self.is_data_actual = True
        result = func(self, *args, **kwargs)
        return result
    return wrapper

['player_slot', 'account_id', 'assists', 'camps_stacked', 'deaths', 'denies',
                               'gold', 'gold_per_min', 'gold_spent', 'hero_damage', 'hero_healing',
                               'hero_id', 'item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5', 'kills',
                               'last_hits', 'leaver_status', 'level', 'obs_placed', 'party_id', 'hero_variant',
                               'pings', 'rune_pickups', 'sen_placed', 'stuns', 'tower_damage', 'xp_per_min',
                               'personaname', 'name', 'last_login', 'isRadiant', 'total_gold', 'total_xp',
                               'kills_per_min', 'kda', 'abandons', 'neutral_kills', 'tower_kills', 'courier_kills',
                               'lane_kills', 'hero_kills', 'observer_kills', 'sentry_kills', 'roshan_kills',
                               'necronomicon_kills', 'ancient_kills', 'buyback_count', 'observer_uses', 'sentry_uses',
                               'lane_efficiency', 'lane_efficiency_pct', 'lane', 'lane_role', 'is_roaming',
                               'purchase_tpscroll', 'actions_per_min', 'life_state_dead', 'rank_tier']
        
class Player:

    @uptodated_data
    def __init__(self, data: dict):
        must_data_fields = ['account_id', 'steamid', 'profileurl', 'personaname', 'cheese',
                            'fh_unavailable', 'loccountrycode', 'plus', 'name', 'country_code',
                            'fantasy_role', 'team_id', 'team_name', 'team_tag', 'is_locked',
                             'is_pro', 'locked_until']

        for field in must_data_fields:
            setattr(self, field, data.get(field))
        self.history_data = {}
        self.n_last_games = 30

    def __repr__(self):
        return f'Player {self.account_id} {self.profileurl} {self.personaname}\n'

    
    def get_collected_fileds(self):
        need_fields = ['assists', 'camps_stacked', 'deaths', 'gold', 'gold_per_min', 'gold_spent', 'hero_damage',
                       'hero_healing', 'hero_id', 'item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5',
                       'kills', 'last_hits', 'level', 'obs_placed', 'pings', 'rune_pickups', 'sen_placed',
                       'stuns', 'tower_damage', 'xp_per_min', 'total_gold', 'total_xp', 'kills_per_min',
                       'kda', 'abandons', 'neutral_kills', 'tower_kills', 'courier_kills',
                       'lane_kills', 'hero_kills', 'observer_kills', 'sentry_kills', 'roshan_kills',
                       'necronomicon_kills', 'ancient_kills', 'buyback_count', 'observer_uses', 'sentry_uses',
                       'lane_efficiency', 'lane_efficiency_pct', 'lane', 'lane_role', 'purchase_tpscroll',
                       'actions_per_min', 'life_state_dead', 'rank_tier']
        return need_fields
        
    def get_collected_fields_num(self):
        fields = ['assists', 'camps_stacked', 'deaths', 'gold', 'gold_per_min', 'gold_spent', 'hero_damage',
                  'hero_healing', 'kills', 'last_hits', 'level', 'obs_placed', 'pings', 'rune_pickups',
                  'sen_placed', 'stuns', 'tower_damage', 'xp_per_min', 'total_gold', 'total_xp', 'kills_per_min',
                  'kda', 'abandons', 'neutral_kills', 'tower_kills', 'courier_kills', 'lane_kills',
                  'hero_kills', 'observer_kills', 'sentry_kills', 'roshan_kills', 'necronomicon_kills',
                  'ancient_kills', 'buyback_count', 'observer_uses', 'sentry_uses', 'lane_efficiency',
                  'lane_efficiency_pct', 'purchase_tpscroll', 'actions_per_min', 'life_state_dead', 'rank_tier']
        
        
    def get_collected_fields_category(self):
        fields = ['hero_id', 'item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5', 'isRadiant', 'lane',
                  'lane_role']
        
    def get_stats_for_time(self, current_time: int, slot: int):
        valid_keys = [t for t in self.history_data.keys() if t < current_time]
        
        # 2) Отсортируем, чтобы понять последние n по времени/индексу
        valid_keys.sort()git 
        
        # 3) Возьмём срез последних n ключей
        relevant_keys = valid_keys[-n:]
        
        result = {}
        
        # === Обрабатываем числовые поля ===
        for field in self.get_collected_fields_num():
            values = []
            for t in relevant_keys:
                val = self.history_data[t].get(field)
                if val is not None:
                    values.append(val)
            
            if values:  # если есть хотя бы одно не-None значение
                result[field + '_' + str(slot)] = sum(values) / len(values)  # среднее
            else:
                result[field + '_' + str(slot)] = None  # или 0, или другое значение по умолчанию
        
        # === Обрабатываем категориальные поля ===
        for field in self.get_collected_fields_category():
            cat_values = []
            for t in relevant_keys:
                val = self.history_data[t].get(field)
                if val is not None:
                    cat_values.append(val)
            
            if cat_values:
                # Ищем самое частое (моду)
                freq = Counter(cat_values)
                most_common_value, _ = freq.most_common(1)[0]
                result[field + '_' + str(slot)] = most_common_value
            else:
                result[field + '_' + str(slot)] = None
        
        return result

    @outdated_data
    def add_match(self, data: dict, start_time: int, is_radiant_win: bool, player_slot: str):
        self.history_data[start_time] = {}
        for field in get_collected_fileds:
            self.history_data[start_time][field] = data[field + '_' + player_slot]
            
    def get_statistics_up_to_time(self, datetime: int):
        

    def __eq__(self, other):
        if not isinstance(other, Player):
            return NotImplemented
        return self.account_id == other.account_id

    def __hash__(self):
        return hash(self.account_id)

class Players:

    def __init__(self):
        self.players = []
        
    def add_player(self, player: Player):
        self.players.append(player)

    def __contains__(self, item):
        return item in self.players

    def __iter__(self):
        return iter(self.players)

    def __repr__(self):
        return str(self.players)