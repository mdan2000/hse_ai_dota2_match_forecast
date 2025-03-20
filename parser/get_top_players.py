import requests
import json

def get_top_players():
    url = "https://api.opendota.com/api/proPlayers"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return []
    
    response.encoding = 'utf-8'  # Указываем кодировку явно
    data = response.json()
    
    return data

def get_player_matches(account_id):
    url = f"https://api.opendota.com/api/players/{account_id}/matches"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Ошибка при получении матчей для {account_id}: {response.status_code}")
        return []
    
    return response.json()

if __name__ == "__main__":
    top_100_players = get_top_players()
    with open('top_players.json', 'w', encoding='utf-8') as w:
        json.dump(top_100_players, w, ensure_ascii=False, indent=4)
