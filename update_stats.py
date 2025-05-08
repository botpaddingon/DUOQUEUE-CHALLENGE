import os
import requests
import json
import time

# Récupère la clé Riot depuis le secret GitHub Actions
API_KEY = os.environ['RIOT_API_KEY']

# Tes équipes et Riot IDs
PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELM", "Last Dance#ZAC"],
    "Team Dylan": ["Frog biceps#CMOI", "lecheur2pied#39810"]
}

# Plateau pour account-v1
PLATFORM = 'euw1'
# Région pour match-v5
REGION = 'europe'

def get_puuid(riot_id: str) -> str | None:
    name, tag = riot_id.split('#')
    url = f'https://{PLATFORM}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}'
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
    # 1) Récupérer tous les PUUIDs
    puuids: dict[str,str] = {}
    for team, ids in PLAYERS.items():
        for rid in ids:
            puuid = get_puuid(rid)
            if puuid:
                puuids[rid] = puuid
            time.sleep(1.3)

    # 2) Initialiser les stats
    stats = {
        team: {'players': ids, 'games': 0, 'wins': 0, 'losses': 0}
        for team, ids in PLAYERS.items()
    }

    # 3) Parcourir chaque équipe
    for team, ids in PLAYERS.items():
        rid1, rid2 = ids
        puuid1 = puuids.get(rid1)
        puuid2 = puuids.get(rid2)
        if not puuid1 or not puuid2:
            continue

        # Pour chaque match listé pour le premier joueur
        for mid in get_match_ids(puuid1):
            detail = get_match_detail(mid)
            if not detail:
                continue

            info = detail.get('info', {})
            # Filtrer uniquement Solo/Duo queue (queueId 420)
            if info.get('queueId') != 420:
                continue

            participants = info.get('participants', [])
            # Trouver les deux participants
            p1 = next((p for p in participants if p['puuid'] == puuid1), None)
            p2 = next((p for p in participants if p['puuid'] == puuid2), None)
            if not p1 or not p2:
                continue

            # Vérifier qu'ils étaient dans la même équipe
            if p1.get('teamId') != p2.get('teamId'):
                continue

            # Jouable en duo validé
            stats[team]['games'] += 1
            if p1.get('win'):
                stats[team]['wins'] += 1
            else:
                stats[team]['losses'] += 1

            time.sleep(1.2)

    # 4) Générer le JSON final avec calcul du winrate
    out = {
        team: {
            **v,
            'winrate': round((v['wins'] / v['games'] * 100) if v['games'] else 0, 1)
        }
        for team, v in stats.items()
    }

    # 5) Sauvegarder stats.json
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("✅ stats.json mis à jour !")

if __name__ == '__main__':
    main()
