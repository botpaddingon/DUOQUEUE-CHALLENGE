import os
import requests
import json
import time

API_KEY  = os.environ['RIOT_API_KEY']
PLATFORM = 'euw1'    # pour Summoner-V4
REGION   = 'europe'  # pour Match-V5

PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELMI", "Last Dance#ZAC"],
    "Team Dylan":  ["Frog biceps#CMOI", "lecheur2pied#39810"]
}

def get_puuid(riot_id: str) -> str | None:
    summoner_name = riot_id.split('#')[0]
    url = f'https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[PUUID ERROR] {riot_id} → {r.status_code}")
        return None
    return r.json().get('puuid')

def get_match_ids(puuid: str) -> list[str]:
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=20'
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
    # 1) récupérer tous les puuids
    puuids = {}
    for team, ids in PLAYERS.items():
        for rid in ids:
            puuid = get_puuid(rid)
            if puuid:
                puuids[rid] = puuid
            time.sleep(1.3)

    # 2) init stats
    stats = {team: {'players': ids, 'games':0, 'wins':0, 'losses':0} for team, ids in PLAYERS.items()}

    # 3) parcourir les matches duo
    for team, ids in PLAYERS.items():
        p1, p2 = ids
        pu1, pu2 = puuids.get(p1), puuids.get(p2)
        if not pu1 or not pu2:
            continue

        for mid in get_match_ids(pu1):
            detail = get_match_detail(mid)
            if not detail:
                continue
            info = detail['info']
            if info.get('queueId') != 420:  # Solo/Duo ranked
                continue

            parts = info['participants']
            d1 = next((p for p in parts if p['puuid']==pu1), None)
            d2 = next((p for p in parts if p['puuid']==pu2), None)
            if not d1 or not d2 or d1['teamId']!=d2['teamId']:
                continue

            stats[team]['games'] += 1
            if d1['win']:
                stats[team]['wins'] += 1
            else:
                stats[team]['losses'] += 1

            time.sleep(1.2)

    # 4) calcul winrate + dump JSON
    out = {
        team: {**v, 'winrate': round((v['wins']/v['games']*100) if v['games'] else 0,1)}
        for team, v in stats.items()
    }
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("✅ stats.json mis à jour !")

if __name__ == '__main__':
    main()
