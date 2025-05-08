import os
import requests
import json
import time
from urllib.parse import quote

# Clé Riot stockée dans le secret Actions RIOT_API_KEY
API_KEY  = os.environ['RIOT_API_KEY']
# Plate-forme pour Summoner-V4
PLATFORM = 'euw1'
# Région pour Match-V5
REGION   = 'europe'

# Tes équipes : Riot-ID = "SummonerName#TAG"
PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELMI",      "Last Dance#ZAC"],
    "Team Dylan":  ["Frog biceps#CMOI",       "lecheur2pied#39810"]
}

def get_puuid(riot_id: str) -> str | None:
    """
    Récupère le puuid à partir du Riot-ID (Name#Tag),
    en URL-encodant correctement Name et Tag pour éviter les 403.
    """
    name, tag = riot_id.split('#', 1)
    name_enc = quote(name, safe='')
    tag_enc  = quote(tag,  safe='')
    url = (
        f'https://{PLATFORM}.api.riotgames.com'
        f'/riot/account/v1/accounts/by-riot-id/{name_enc}/{tag_enc}'
    )
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[PUUID ERROR] {riot_id} → {r.status_code}")
        return None
    return r.json().get('puuid')

def get_match_ids(puuid: str) -> list[str]:
    url = (
        f'https://{REGION}.api.riotgames.com'
        f'/lol/match/v5/matches/by-puuid/{puuid}'
        f'/ids?type=ranked&start=0&count=20'
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
    # 1) Récupérer tous les PUUIDs
    puuids: dict[str,str] = {}
    for ids in PLAYERS.values():
        for rid in ids:
            puuid = get_puuid(rid)
            if puuid:
                puuids[rid] = puuid
            time.sleep(1.2)

    # 2) Initialiser les stats
    stats = {
        team: {'players': ids, 'games': 0, 'wins': 0, 'losses': 0}
        for team, ids in PLAYERS.items()
    }

    # 3) Pour chaque équipe, analyser les matchs Solo/Duo
    for team, ids in PLAYERS.items():
        rid1, rid2 = ids
        pu1 = puuids.get(rid1)
        pu2 = puuids.get(rid2)
        if not pu1 or not pu2:
            continue

        for match_id in get_match_ids(pu1):
            detail = get_match_detail(match_id)
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
