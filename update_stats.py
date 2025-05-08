import os
import requests
import json
import time
from urllib.parse import quote

# Récupère la clé depuis le secret GitHub Actions
API_KEY  = os.environ['RIOT_API_KEY']
# Hosts pour les endpoints
PLATFORM = 'euw1'    # Summoner-V4
REGION   = 'europe'  # Match-V5

# Tes duos Riot-ID = "Nom#Tag"
PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELMI",     "Last Dance#ZAC"],
    "Team Dylan":  ["Frog biceps#CMOI",      "lecheur2pied#39810"]
}

def get_puuid(riot_id: str) -> str | None:
    # On ne garde que la partie avant '#' pour Summoner-V4
    name = riot_id.split('#', 1)[0]
    name_enc = quote(name, safe='')
    url = f'https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name_enc}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[PUUID ERROR] {riot_id} → {r.status_code}")
        return None
    return r.json().get('puuid')

def get_match_ids(puuid: str) -> list[str]:
    url = (
        f'https://{REGION}.api.riotgames.com'
        f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
        f'?type=ranked&start=0&count=20'
    )
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[MATCHLIST ERROR] {puuid} → {r.status_code}")
        return []
    return r.json()

def get_match_detail(match_id: str) -> dict | None:
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[MATCHDETAIL ERROR] {match_id} → {r.status_code}")
        return None
    return r.json()

def main():
    # 1) Récupérer les PUUIDs de tous les joueurs
    puuids = {}
    for duo in PLAYERS.values():
        for riot_id in duo:
            puuid = get_puuid(riot_id)
            if puuid:
                puuids[riot_id] = puuid
            time.sleep(1.2)

    # 2) Init stats
    stats = {
        team: {'players': duo, 'games': 0, 'wins': 0, 'losses': 0}
        for team, duo in PLAYERS.items()
    }

    # 3) Comptage des parties Solo/Duo jouées ensemble
    for team, duo in PLAYERS.items():
        id1, id2 = duo
        p1, p2 = puuids.get(id1), puuids.get(id2)
        if not p1 or not p2:
            continue

        for match_id in get_match_ids(p1):
            detail = get_match_detail(match_id)
            if not detail:
                continue

            info = detail['info']
            # Filtrer Solo/Duo Ranked (queueId=420)
            if info.get('queueId') != 420:
                continue

            parts = info['participants']
            d1 = next((p for p in parts if p['puuid'] == p1), None)
            d2 = next((p for p in parts if p['puuid'] == p2), None)
            if not d1 or not d2 or d1['teamId'] != d2['teamId']:
                continue

            stats[team]['games'] += 1
            if d1['win']:
                stats[team]['wins'] += 1
            else:
                stats[team]['losses'] += 1

            time.sleep(1.2)

    # 4) Calcul du winrate et export JSON
    out = {
        team: {
            **v,
            'winrate': round( (v['wins'] / v['games'] * 100) if v['games'] else 0, 1 )
        }
        for team, v in stats.items()
    }
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("✅ stats.json mis à jour !")

if __name__ == '__main__':
    main()
