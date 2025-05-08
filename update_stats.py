import os
import requests
import json
import time

# On lit la clé depuis les Secrets de GitHub Actions
API_KEY = os.environ['RIOT_API_KEY']

# Vos équipes et Riot-IDs
PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELM", "Last Dance#ZAC"],
    "Team Dylan": ["Frog biceps#CMOI", "lecheur2pied#39810"]
}

# Plate-forme pour account-v1 (EU West)
PLATFORM = 'euw1'
# Région pour match-v5 (Europe)
REGION = 'europe'

def get_puuid(riot_id: str) -> str | None:
    name, tag = riot_id.split('#')
    url = f'https://{PLATFORM}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"Erreur get_puuid {riot_id}: {r.status_code}")
        return None
    return r.json().get('puuid')

def get_match_ids(puuid: str) -> list[str]:
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=20'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"Erreur get_match_ids {puuid}: {r.status_code}")
        return []
    return r.json()

def get_match_detail(match_id: str) -> dict | None:
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if not r.ok:
        print(f"Erreur get_match_detail {match_id}: {r.status_code}")
        return None
    return r.json()

def main():
    # 1) Récup des PUUIDs
    puuids: dict[str,str] = {}
    for team, ids in PLAYERS.items():
        for rid in ids:
            puuid = get_puuid(rid)
            if puuid:
                puuids[rid] = puuid
            time.sleep(1.2)  # pour éviter rate-limit

    # 2) Init stats
    stats = {
        team: {'players': ids, 'games': 0, 'wins': 0, 'losses': 0}
        for team, ids in PLAYERS.items()
    }

    # 3) Boucle match par match
    for team, ids in PLAYERS.items():
        p1, p2 = ids
        puuid1 = puuids.get(p1)
        puuid2 = puuids.get(p2)
        if not puuid1 or not puuid2:
            continue

        for mid in get_match_ids(puuid1):
            detail = get_match_detail(mid)
            if not detail:
                continue
            participants = detail['metadata']['participants']
            # On ne garde que les parties où p2 était aussi présent
            if puuid2 not in participants:
                continue
            # On récupère le résultat pour p1
            p1data = next((p for p in detail['info']['participants'] if p['puuid']==puuid1), None)
            if not p1data:
                continue

            stats[team]['games'] += 1
            if p1data['win']:
                stats[team]['wins'] += 1
            else:
                stats[team]['losses'] += 1

            time.sleep(1.2)

    # 4) On écrit stats.json (le front calculera winrate + affichera défaites)
    out = {
        team: {
            **v,
            'winrate': round((v['wins']/v['games']*100) if v['games'] else 0, 1)
        }
        for team, v in stats.items()
    }
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print("stats.json mis à jour ✅")

if __name__ == '__main__':
    main()
