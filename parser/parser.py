import requests
import json
import time

# Новый SQL-запрос (кодируем URL для запроса)
SQL_QUERY = "SELECT match_id FROM public_matches WHERE avg_rank_tier >= 80 ORDER BY match_id DESC LIMIT 10"
TOP_MATCHES_URL = f"https://api.opendota.com/api/explorer?sql={SQL_QUERY.replace(' ', '+')}"
MATCH_DETAILS_URL = "https://api.opendota.com/api/matches/"

# Получаем список матчей топ-игроков
def get_top_matches():
    response = requests.get(TOP_MATCHES_URL)
    if response.status_code == 200:
        data = response.json()
        return [match["match_id"] for match in data.get("rows", [])]
    else:
        print(f"Ошибка при получении списка матчей: {response.status_code}")
        print(response.text)
        return []

# Получаем детальную информацию по каждому матчу
def get_match_details(match_id):
    response = requests.get(f"{MATCH_DETAILS_URL}{match_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка при получении данных матча {match_id}: {response.status_code}")
        return None

# Главная функция парсинга
def main():
    match_ids = get_top_matches()

    # Сохраняем список матчей
    with open("top_matches_list.json", "w", encoding="utf-8") as file:
        json.dump(match_ids, file, indent=4, ensure_ascii=False)

    detailed_matches = []
    i = 0
    for match_id in match_ids:
        i += 1
        print(i)
        details = get_match_details(match_id)
        if details:
            detailed_matches.append(details)
            time.sleep(1)  # Задержка, чтобы не спамить API

    # Сохраняем детальные данные по матчам
    with open("top_match_details.json", "w", encoding="utf-8") as file:
        json.dump(detailed_matches, file, indent=4, ensure_ascii=False)

    print("Данные сохранены в файлы top_matches_list.json и top_match_details.json")

if __name__ == "__main__":
    main()
