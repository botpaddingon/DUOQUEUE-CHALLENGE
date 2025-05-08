import os
import requests
import json
import time

# Ta clé Riot stockée dans le secret RIOT_API_KEY
API_KEY = os.environ['RIOT_API_KEY']

# === CORRECTION ICI ===
PLAYERS = {
    "Team Octave":   ["KIFFEUR2BALTROUS#SLURP",   "kawakino#51928"],
    "Team Justin":   ["cra feu 200#HELMI",        "Last Dance#ZAC"],
    "Team Dylan":    ["Frog biceps#CMOI",         "lecheur2pied#39810"]
}
# =======================

PLATFORM = 'euw1'    # pour l’endpoint account-v1
REGION   = 'europe'  # pour match-v5

def get_puuid(riot_id):
    name, tag = riot_id.split('#')
    url = f'https://{PLATFORM}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[PUUID ERROR] {riot_id} → {r.status_code}")
        return None
    return r.json().get('puuid')

def get_match_ids(puuid):
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=20'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[MATCHLIST ERROR] {puuid} → {r.status_code}")
        return []
    return r.json()

def get_match_detail(match_id):
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"[MATCHDETAIL ERROR] {match_id} → {r.status_code}")
        return None
    return r.json()

def main():
    # 1) Récupérer les PUUIDs
    puuids = {}
    for team, ids in PLAYERS.items():
        for rid in ids:
            puuid = get_puuid(rid)
            if puuid:
                puuids[rid] = puuid
            time.sleep(1.3)

    # 2) Initialiser les stats
    stats = {team: {'players': ids, 'games': 0, 'wins': 0, 'losses': 0}
             for team, ids in PLAYERS.items()}

    # 3) Pour chaque équipe, ne compter que les matchs Duo Queue où les deux joueurs étaient ensemble
    for team, ids in PLAYERS.items():
        rid1, rid2 = ids
        p1 = puuids.get(rid1)
        p2 = puuids.get(rid2)
        if not p1 or not p2:
            continue

        for mid in get_match_ids(p1):
            detail = get_match_detail(mid)
            if not detail:
                continue

            info = detail['info']
            # Filtrer solo/duo ranked
            if info.get('queueId') != 420:
                continue

            parts = info['participants']
            # Chercher les deux participants
            d1 = next((p for p in parts if p['puuid'] == p1), None)
            d2 = next((p for p in parts if p['puuid'] == p2), None)
            if not d1 or not d2:
                continue

            # Vérifier qu'ils étaient dans la même équipe
            if d1['teamId'] != d2['teamId']:
                continue

            stats[team]['games'] += 1
            if d1['win']:
                stats[team]['wins'] += 1
            else:
                stats[team]['losses'] += 1

            time.sleep(1.2)

    # 4) Calculer le winrate
    out = {
        team: {
            **v,
            'winrate': round((v['wins'] / v['games'] * 100) if v['games'] else 0, 1)
        }
        for team, v in stats.items()
    }

    # 5) Écrire stats.json
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("✅ stats.json mis à jour !")

if __name__ == '__main__':
    main()
