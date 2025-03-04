import numpy as np
import pandas as pd
import json
import functools
import os
import warnings
warnings.filterwarnings("ignore")


columns = {
    'match_id': 'Int64',
    'barracks_status_dire': 'Int16',
    'barracks_status_radiant': 'Int16',
    'cluster': 'Int32',
    'dire_score': 'Int16',
    'duration': 'Int64',
    'engine': 'Int8',
    'first_blood_time': 'Int64',
    'game_mode': 'Int8',
    'human_players': 'Int8',
    'leagueid': 'Int64',
    'lobby_type': 'Int32',
    'match_seq_num': 'Int64',
    'negative_votes': 'Int16',
    'positive_votes': 'Int16',
    'radiant_score': 'Int16',
    'radiant_win': 'bool',
    'start_time': 'datetime64[ns]',
    'tower_status_dire': 'Int16',
    'tower_status_radiant': 'Int16',
    'version': 'Int16',
    'replay_salt': 'Int32',
    'series_id': 'Int64',
    'series_type': 'Int64',
    'skill': 'category', 
    'patch': 'Int32',
    'region': 'Int32',
    'throw': 'Int64',
    'comeback': 'Int32',
    'loss': 'Int64', 
    'win': 'Int16',
    'replay_url': 'string'
}

max_drafts = 25
draft_fields = ['order', 'pick', 'active_team', 'hero_id', 'player_slot', 'extra_time', 'total_time_taken']

for i in range(max_drafts):
    columns[f'draft_order_{i}'] = 'Int8'
    columns[f'draft_pick_{i}'] = 'bool'
    columns[f'draft_active_team_{i}'] = 'Int8'
    columns[f'draft_player_slot_{i}'] = 'Int16'
    columns[f'draft_extra_time_{i}'] = 'Int32'
    columns[f'draft_hero_id_{i}'] = 'Int16'
    columns[f'draft_total_time_taken_{i}'] = 'Int16'


max_radiant_gold_adv = 180
rad_gold_adv = 'radiant_gold_adv'
max_radiant_xp_adv = 180
rad_xp_adv = 'radiant_xp_adv'
player_slots = 12

match_info = dict()

for i in range(max_radiant_gold_adv):
    columns[f'{rad_gold_adv}_{i}'] = 'Int32'
    columns[f'{max_radiant_xp_adv}_{i}'] = 'Int32'
    
players_info_fileds = ['player_slot', 'account_id', 'assists', 'camps_stacked', 'deaths', 'denies',
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


for i in range(12):
    columns[f'player_slot_{i}'] = 'Int16'
    columns[f'account_id_{i}'] = 'Int64'
    columns[f'assists_{i}'] = 'Int8'
    columns[f'camps_stacked_{i}'] = 'Int8'
    columns[f'deaths_{i}'] = 'Int8'
    columns[f'denies_{i}'] = 'Int16'
    columns[f'gold_{i}'] = 'Int32'
    columns[f'gold_per_min_{i}'] = 'Int32'
    columns[f'gold_spent_{i}'] = 'Int32'
    columns[f'hero_damage_{i}'] = 'Int32'
    columns[f'hero_healing_{i}'] = 'Int32'
    columns[f'hero_id_{i}'] = 'category'
    columns[f'item_0_{i}'] = 'category'
    columns[f'item_1_{i}'] = 'category'
    columns[f'item_2_{i}'] = 'category'
    columns[f'item_3_{i}'] = 'category'
    columns[f'item_4_{i}'] = 'category'
    columns[f'item_5_{i}'] = 'category'
    columns[f'kills_{i}'] = 'Int8'
    columns[f'last_hits_{i}'] = 'Int16'
    columns[f'leaver_status_{i}'] = 'category'
    columns[f'level_{i}'] = 'Int8'
    columns[f'obs_placed_{i}'] = 'Int8'
    columns[f'party_id_{i}'] = 'Int32'
    columns[f'hero_variant_{i}'] = 'Int64'
    columns[f'pings_{i}'] = 'Int16'
    columns[f'rune_pickups_{i}'] = 'Int8'
    columns[f'sen_placed_{i}'] = 'Int8'
    columns[f'stuns_{i}'] = 'float64'
    columns[f'tower_damage_{i}'] = 'Int32'
    columns[f'xp_per_min_{i}'] = 'Int16'
    columns[f'personaname_{i}'] = 'string'
    columns[f'name_{i}'] = 'string'
    columns[f'last_login_{i}'] = 'string'
    columns[f'isRadiant_{i}'] = 'bool'
    columns[f'total_gold_{i}'] = 'Int32'
    columns[f'total_xp_{i}'] = 'Int32'
    columns[f'kills_per_min_{i}'] = 'float64'
    columns[f'kda_{i}'] = 'float64'
    columns[f'abandons_{i}'] = 'Int8'
    columns[f'neutral_kills_{i}'] = 'Int16'
    columns[f'tower_kills_{i}'] = 'Int8'
    columns[f'courier_kills_{i}'] = 'Int8'
    columns[f'lane_kills_{i}'] = 'Int16'
    columns[f'hero_kills_{i}'] = 'Int16'
    columns[f'observer_kills_{i}'] = 'Int8'
    columns[f'sentry_kills_{i}'] = 'Int8'
    columns[f'roshan_kills_{i}'] = 'Int8'
    columns[f'necronomicon_kills_{i}'] = 'Int8'
    columns[f'ancient_kills_{i}'] = 'Int64'
    columns[f'buyback_count_{i}'] = 'Int8'
    columns[f'observer_uses_{i}'] = 'Int8'
    columns[f'sentry_uses_{i}'] = 'Int8'
    columns[f'lane_efficiency_{i}'] = 'float64'
    columns[f'lane_efficiency_pct_{i}'] = 'float64'
    columns[f'lane_{i}'] = 'category'
    columns[f'lane_role_{i}'] = 'category'
    columns[f'is_roaming_{i}'] = 'bool'
    columns[f'purchase_tpscroll_{i}'] = 'Int16'
    columns[f'actions_per_min_{i}'] = 'Int16'
    columns[f'life_state_dead_{i}'] = 'Int64'
    columns[f'rank_tier_{i}'] = 'Int16'

def outdated_data(func):
    @functools.wraps(func)  # сохраняет имя и docstring оригинальной функции
    def wrapper(self, *args, **kwargs):
        self.is_data_actual = False
        result = func(self, *args, **kwargs)
        return result
    return wrapper  # <-- ВАЖНО!

def uptodated_data(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        self.is_data_actual = True
        result = func(self, *args, **kwargs)
        return result
    return wrapper  # <-- ВАЖНО!


        
class Player:

    @uptodated_data
    def __init__(self, data: dict):
        must_data_fields = ['account_id', 'steamid', 'profileurl', 'personaname', 'cheese',
                            'fh_unavailable', 'loccountrycode', 'plus', 'name', 'country_code',
                            'fantasy_role', 'team_id', 'team_name', 'team_tag', 'is_locked',
                             'is_pro', 'locked_until']

        for field in must_data_fields:
            setattr(self, field, data.get(field))

    def __repr__(self):
        return f'Player {self.account_id} {self.profileurl} {self.personaname}\n'

    #@outdated_data
    #def add_match

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
        
        
class Match:
    def __init__(self, data: dict):
        if data == '-1':
            raise ValueErorr('It is bad match')

        if 'draft_timings' not in data:
            print(data)
            exit()
        
        if data['draft_timings'] is not None:
            data['draft_timings'] = sorted(data['draft_timings'], key=lambda d: d['order'])

        self.match_id = data['match_id']
        
        simple_fields = ['match_id', 'barracks_status_dire', 'barracks_status_radiant', 'cluster',
                         'dire_score', 'duration', 'engine', 'first_blood_time', 'game_mode',
                         'human_players', 'leagueid', 'lobby_type', 'match_seq_num', 'negative_votes',
                         'positive_votes', 'radiant_score', 'radiant_win', 'start_time', 'tower_status_dire',
                         'tower_status_radiant', 'version', 'replay_salt', 'series_id', 'series_type',
                         'skill', 'patch', 'region', 'throw', 'comeback', 'loss', 'win', 'replay_url']

        draft_fields = ['order', 'pick', 'active_team', 'hero_id', 'player_slot', 'extra_time', 'total_time_taken']
        
        players_info_fileds = ['player_slot', 'account_id', 'assists', 'camps_stacked', 'deaths', 'denies',
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
        
        max_drafts = 25
        max_picks_bans = 25
        max_radiant_gold_adv = 180
        rad_gold_adv = 'radiant_gold_adv'
        max_radiant_xp_adv = 180
        rad_xp_adv = 'radiant_xp_adv'
        player_slots = 12

        match_info = dict()

        for i in range(max_radiant_gold_adv):
            match_info[f'{rad_gold_adv}_{i}'] = None

        if data[rad_gold_adv] is not None:
            for i in range(len(data[rad_gold_adv])):
                match_info[f'{rad_gold_adv}_{i}'] = data[rad_gold_adv][i]

        for i in range(max_radiant_xp_adv):
            match_info[f'{max_radiant_xp_adv}_{i}'] = None

        if data[rad_xp_adv] is not None:
            for i in range(len(data[rad_xp_adv])):
                match_info[f'{rad_xp_adv}_{i}'] = data[rad_xp_adv][i]


        for i in range(max_drafts):
            for field in draft_fields:
                match_info[f'draft_{field}_{i}'] = None

        if data['draft_timings'] is not None:
            for draft in data['draft_timings']:
                order = draft['order']
                for field in draft:
                    match_info[f'draft_{field}_{order}'] = draft[field]


        for player_field in players_info_fileds:
            for i in range(player_slots):
                match_info[f'{player_field}_{i}'] = None

        
        for i in range(len(data['players'])):
            player = data['players'][i]
            for field in players_info_fileds:
                match_info[f'{field}_{i}'] = player[field]
        
        for field in simple_fields:
            if field in data:
                match_info[field] = data[field]

        self.match_info = match_info


    def get_data(self):
        return self.match_info
    

    def __eq__(self, other):
        if not isinstance(other, Match):
            return NotImplemented
        return self.account_id == other.account_id

    def __hash__(self):
        return hash(self.account_id)

    def __repr__(self):
        return str(self.__dict__)
        
        
        
def read_players(file='top_players.json'):
    with open(file, 'r', encoding='cp850') as file:
        players_raw_data = json.load(file)
        players = Players()
        for player_raw_data in players_raw_data:
            player = Player(player_raw_data)
            players.add_player(player)
            
    return players
    

with open(f'backup_1.json', 'r', encoding='cp850') as file:
    parsed_matches = json.load(file)
    pd_data = []
    for match in parsed_matches:
        if parsed_matches[match] == '-1' or parsed_matches[match]['game_mode'] != 22:
            continue
        match = Match(parsed_matches[match])
        pd_data.append(match.get_data())
        
    
    df = pd.DataFrame(pd_data).astype(columns)
    
print('Start main parse')
n_to_save = 2
while(os.path.exists(f'backup_{n_to_save}.json')):
    with open(f'backup_{n_to_save}.json', 'r', encoding='cp850') as file:
        
        parsed_matches = json.load(file)
        n_to_save += 1
        pd_data = []
        #print(parsed_matches[list(parsed_matches.keys())[0]])
        for match in parsed_matches:
            if parsed_matches[match] == '-1' or parsed_matches[match]['game_mode'] != 22:
                continue
            match = Match(parsed_matches[match])
            pd_data.append(match.get_data())
        if len(pd_data) == 0:
            print(f'\rRead {n_to_save} backup. Summary data is {df.size}. Empty input', end='')
            continue
        temp_df = pd.DataFrame(pd_data)
        #print(temp_df.columns.tolist())
        #print(temp_df)
        for col, dtype in columns.items():
            try:
                temp_df[col] = temp_df[col].astype(dtype)
            except TypeError as e:
                print(f"Ошибка при преобразовании столбца '{col}' в {dtype}: {e}")
                exit()
        #temp_df = temp_df.astype(columns)
        df = pd.concat([df, temp_df], ignore_index=True)
        
        print(f'\rRead {n_to_save} backup. Summary data is {df.size}', end='')

df.to_csv(f'data_{n_to_save-1}.csv')