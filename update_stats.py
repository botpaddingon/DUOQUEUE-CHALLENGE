import os
import requests
import json
import time
from urllib.parse import quote

# Ta clé Riot stockée dans les Secrets GitHub Actions
API_KEY  = os.environ['RIOT_API_KEY']
# Plate-forme (pour Summoner-V4)
PLATFORM = 'euw1'
# Région (pour Match-V5)
REGION   = 'europe'

# Tes équipes : Riot-ID = "SummonerName#Tag"
PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELMI",     "Last Dance#ZAC"],
    "Team Dylan":  ["Frog biceps#CMOI",      "lecheur2pied#39810"]
}

def get_puuid(riot_id: str) -> str | None:
    """
    Récupère le puuid à partir du Riot-ID en utilisant Summoner-V4 par nom.
    On prend la partie avant '#' comme summonerName, on l'URL-encode,
    et on appelle /lol/summoner/v4/summoners/by-name/{nameEnc}.
    """
    summoner_name = riot_id.split('#', 1)[0]
    name_enc = quote(summoner_name, safe='')
    url = (
        f'https://{PLATFORM}.api.riotgames.com'
        f'/lol/summoner/v4/summoners/by-name/{name_enc}'
    )
    res = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not res.ok:
        print(f"[PUUID ERROR] {riot_id} → {res.status_code}")
        return None
    return res.json().get('puuid')

def get_match_ids(puuid: str) -> list[str]:
    url = (
        f'https://{REGION}.api.riotgames.com'
        f'/lol/match/v5/matches/by-puuid/{puuid}/ids'
        f'?type=ranked&start=0&count=20'
    )
    res = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not res.ok:
        print(f"[MATCHLIST ERROR] {puuid} → {res.status_code}")
        return []
    return res.json()

def get_match_detail(match_id: str) -> dict | None:
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    res = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not res.ok:
        print(f"[MATCHDETAIL ERROR] {match_id} → {res.status_code}")
        return None
    return res.json()

def main():
    # 1) Récupérer les PUUIDs
    puuids: dict[str,str] = {}
    for ids in PLAYERS.values():
        for riot_id in ids:
            puuid = get_puuid(riot_id)
            if puuid:
                puuids[riot_id] = puuid
            time.sleep(1.2)

    # 2) Initialiser les stats
    stats = {
        team: {'players': ids, 'games': 0, 'wins': 0, 'losses': 0}
        for team, ids in PLAYERS.items()
    }

    # 3) Parcourir chaque duo
    for team, ids in PLAYERS.items():
        id1, id2 = ids
        pu1, pu2 = puuids.get(id1), puuids.get(id2)
        if not pu1 or not pu2:
            continue

        for mid in get_match_ids(pu1):
            detail = get_match_detail(mid)
            if not detail:
                continue

            info = detail['info']
            # Solo/Duo Ranked → queueId 420
            if info.get('queueId') != 420:
                continue

            parts = info['participants']
            p1 = next((p for p in parts if p['puuid'] == pu1), None)
            p2 = next((p for p in parts if p['puuid'] == pu2), None)
            if not p1 or not p2 or p1['teamId'] != p2['teamId']:
                continue

            stats[team]['games'] += 1
            if p1['win']:
                stats[team]['wins'] += 1
            else:
                stats[team]['losses'] += 1

            time.sleep(1.2)

    # 4) Calculer le winrate et exporter JSON
    out = {
        team: {
            **v,
            'winrate': round((v['wins'] / v['games'] * 100) if v['games'] else 0, 1)
        }
        for team, v in stats.items()
    }
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("✅ stats.json mis à jour !")

if __name__ == '__main__':
    main()
