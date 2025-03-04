import requests as req
import json
import time

def get_pro_matches(less_than_match_id):
    url = f'https://api.opendota.com/api/proMatches?less_than_match_id={less_than_match_id}'
    response = req.get(url)
    
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []
    
    response.encoding = 'utf-8'  # Указываем кодировку явно
    data = response.json()
    
    return data

if __name__ == "__main__":
    
    with open('top_matches.json', 'r', encoding='cp850') as file:
        matches = json.load(file)
    
    matches_count = len(matches)
    try:
        while len(matches) < 100000:
            time.sleep(0.2)
            new_matches = get_pro_matches(matches[-1]['match_id'])
            
            for match in new_matches:
                matches.append(match)
            
            with open('top_matches.json', 'w', encoding='utf-8') as w:
                json.dump(matches, w, ensure_ascii=False, indent=4)
            print(len(matches))
    except Exception as e:
        print(e)
        with open('top_matches_result.json', 'w', encoding='utf-8') as w:
                json.dump(matches, w, ensure_ascii=False, indent=4)
    exit()
    
    players_data = {}
    for player in top_100_players:
        account_id = player.get("account_id")
        if account_id:
            players_data[account_id] = {
                "player_info": player,
                "matches": get_player_matches(account_id)
            }
    
    with open('top_players_matches.json', 'w', encoding='utf-8') as w:
        json.dump(players_data, w, ensure_ascii=False, indent=4)