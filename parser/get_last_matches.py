import requests as req
import json
import time
import os

def get_last_matches(account_id):
    url = f'https://api.opendota.com/api/players/{account_id}/matches?api_key=38b38644-892a-4eb4-a2b1-06bedea541c3'
    #print(response.text)
    data = -1
    while data == -1:
        try:
            time.sleep(0.1)
            response = req.get(url)
            if response.status_code != 200:
                print(f"Ошибка: {response.status_code}")
                raise ValueError(f'bad request, {response.text}')
            
            response.encoding = 'utf-8'  # Указываем кодировку явно
            data = response.json()
        except BaseException as e:
            print(e, e.args)
            time.sleep(6)
    return data
    
def get_match_info(match_id):
    url = f'https://api.opendota.com/api/matches/{match_id}?api_key=38b38644-892a-4eb4-a2b1-06bedea541c3'
    white_list_of_match_fields = ['match_id', 'barracks_status_dire', 'barracks_status_radiant', 'cluster', 'dire_score', 'draft_timings', 'duration', 'engine',
                            'first_blood_time', 'game_mode', 'human_players', 'leagueid', 'lobby_type', 'match_seq_num', 'negative_votes',
                            'picks_bans', 'positive_votes', 'radiant_gold_adv', 'radiant_score', 'radiant_win', 'radiant_xp_adv', 'start_time', 'tower_status_dire',
                            'tower_status_radiant', 'version', 'replay_salt', 'series_id', 'series_type', 'radiant_team', 'dire_team', 'league', 'skill',
                            'patch', 'region', 'throw', 'comeback', 'loss', 'win', 'replay_url']
    white_list_of_heroes_fields = ['player_slot', 'account_id', 'assists', 'camps_stacked', 'creeps_stacked', 'deaths', 'denies', 'gold', 'gold_per_min', 'gold_spent',
                                   'hero_damage', 'hero_healing', 'hero_id', 'item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5', 'kills', 'last_hits', 'leaver_status',
                                   'level', 'obs_placed', 'party_id', 'hero_variant', 'pings', 'rune_pickups', 'sen_placed', 'stuns', 'tower_damage', 'xp_per_min', 'personaname',
                                   'name', 'last_login', 'isRadiant', 'total_gold', 'total_xp', 'kills_per_min', 'kda', 'abandons', 'neutral_kills', 'tower_kills', 'courier_kills',
                                   'lane_kills', 'hero_kills', 'observer_kills', 'sentry_kills', 'roshan_kills', 'necronomicon_kills', 'ancient_kills', 'buyback_count',
                                   'observer_uses', 'sentry_uses', 'lane_efficiency', 'lane_efficiency_pct', 'lane', 'lane_role', 'is_roaming', 'purchase_tpscroll', 'actions_per_min',
                                   'life_state_dead', 'rank_tier']
    players_field = 'players'
    
    data = -1
    
    while data == -1:
        try:
            time.sleep(0.3)
            response = req.get(url, timeout=2)
            if response.status_code == 404:
                return '-1'
            
            if response.status_code != 200:
                print(f"Ошибка: {response.status_code}")
                raise ValueError(f'bad request, {response.text}')
            
            response.encoding = 'utf-8'  # Указываем кодировку явно
            data = response.json()
        except BaseException as e:
            print(e, e.args)
            time.sleep(6)
    
    heroes_info = []
    for heroe_info in data[players_field]:
        heroe_result = dict()
        for field in white_list_of_heroes_fields:
            if field not in heroe_info:
                heroe_result[field] = None
                continue
            heroe_result[field] = heroe_info[field]
        heroes_info.append(heroe_result)
    
    
    match_result_info = dict()
    for field in white_list_of_match_fields:
        if field not in data:
            match_result_info[field] = None
        else:
            match_result_info[field] = data[field]
           
    match_result_info[players_field] = heroes_info 
    
    return match_result_info

if __name__ == "__main__":
    
    oldest_top_match = 1622931977
    
    with open('bad_matches.json', 'r', encoding='cp850') as file:
        bad_matches = json.load(file)
    
    parsed_ids = set()
    
    #backup_count = 38
    
    n_to_save = 1
    
    while(os.path.exists(f'backup_{n_to_save}.json')):
        with open(f'backup_{n_to_save}.json', 'r', encoding='cp850') as file:
            print(f'\rRead {n_to_save} backup', end='')
            parsed_matches = json.load(file)
            n_to_save += 1
            parsed_ids |= set([i for i in parsed_matches])
    print() 
    
    with open('already_parsed_matches.json', 'r', encoding='cp850') as file:
        parsed_matches = json.load(file)
    
    print(f'Already parsed {len(parsed_matches)} matches')
    
    with open('top_players.json', 'r', encoding='cp850') as file:
        players = json.load(file)

    with open('already_parsed_players.json', 'r', encoding='cp850') as file:
        parsed_players = json.load(file)

    players = [player['account_id'] for player in players]
    
    
    
    
    
    save_count = 50
    last_checkpoint = 0
    already_parsed = 70
    count_for_save = 670
    
    
    player_count = already_parsed
    for player in players[already_parsed:]:
        player_count += 1
        print(f'Parsing {player_count}/{len(players)}')
        player_matches = get_last_matches(player)
        player_matches = [match for match in player_matches if match['start_time'] > oldest_top_match]
        
        match_count = 0
        
        for match in player_matches:
            match_count += 1
            match_id = str(match['match_id'])
            print(f'\rParsing match {match_count}/{len(player_matches)} with id {match["match_id"]}', end='')
            
            if match_count % save_count == 0 and match_count > last_checkpoint:
                with open('already_parsed_matches.json', 'w', encoding='utf-8') as w:
                    json.dump(parsed_matches, w, ensure_ascii=False, indent=4)
                with open('bad_matches.json', 'w', encoding='utf-8') as w:
                    json.dump(bad_matches, w, ensure_ascii=False, indent=4)
            
            if  match_id not in parsed_matches and match_id not in bad_matches and match_id not in parsed_ids:
                time.sleep(0.2)
                match_info = get_match_info(match['match_id'])
                if match_info == '-1':
                    bad_matches.append(match['match_id'])
                    
                parsed_matches[match['match_id']] = match_info
            
            if len(parsed_matches) >= count_for_save:
                with open(f'backup_{n_to_save}.json', 'w', encoding='utf-8') as w:
                    json.dump(parsed_matches, w, ensure_ascii=False, indent=4)
                    parsed_ids |= set([i for i in parsed_matches])
                    print(f'Save backup {n_to_save}')
                    n_to_save += 1
                    parsed_matches = dict()
                with open('already_parsed_matches.json', 'w', encoding='utf-8') as w:
                    json.dump(parsed_matches, w, ensure_ascii=False, indent=4)            
                
        last_checkpoint = 0