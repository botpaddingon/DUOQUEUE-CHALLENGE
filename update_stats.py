import requests, json, time

API_KEY = 'RGAPI-ace61a9c-169f-4f8e-a463-cb84539c967b'
PLAYERS = {
    "Team Octave": ["KIFFEUR2BALTROUS#SLURP", "kawakino#51928"],
    "Team Justin": ["cra feu 200#HELM", "Last Dance#ZAC"],
    "Team Dylan": ["Frog biceps#CMOI", "lecheur2pied#39810"]
}
REGION = 'europe'

def get_puuid(riot_id):
    name, tag = riot_id.split('#')
    url = f'https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    r.raise_for_status()
    return r.json()['puuid']

def get_match_ids(puuid):
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=20'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    return r.json() if r.ok else []

def get_match_detail(match_id):
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}'
    r = requests.get(url, headers={'X-Riot-Token': API_KEY})
    return r.json() if r.ok else None

def main():
    puuids = {}
    for team, ids in PLAYERS.items():
        for rid in ids:
            puuids[rid] = get_puuid(rid)
            time.sleep(1.3)

    stats = {team: {'players': ids, 'games': 0, 'wins': 0} for team, ids in PLAYERS.items()}

    for team, ids in PLAYERS.items():
        p1, p2 = ids
        for mid in get_match_ids(puuids[p1]):
            detail = get_match_detail(mid)
            if not detail: continue
            if puuids[p2] not in detail['metadata']['participants']:
                continue
            part = next(p for p in detail['info']['participants'] if p['puuid']==puuids[p1])
            stats[team]['games'] += 1
            if part['win']: stats[team]['wins'] += 1
            time.sleep(1.2)

    out = {team: {**v, 'winrate': round((v['wins']/v['games']*100) if v['games'] else 0, 1)} for team, v in stats.items()}
    with open('stats.json','w') as f:
        json.dump(out, f, indent=2)

if __name__=='__main__':
    main()