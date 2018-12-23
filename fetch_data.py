import json
import time
import csv
import queue
import threading

import pandas as pd
import requests

class ApiRequest:
    # Class to control requests to API
    def __init__(self, base_url_in, header_in):
        self.base_url = base_url_in
        self.header = header_in
        self.rate_limit = 0
        self.get_rate_limit()

    def get_rate_limit(self):
        resp = requests.request('GET', self.base_url + '/player/Y8YJPG8',
                                headers=self.header)
        self.rate_limit = int(resp.headers['x-ratelimit-limit'])
        print('Rate limit: {}'.format(self.rate_limit))

    def get_data(self,url,params = 0):
        try:
            if params != 0:
                resp = requests.request('GET',self.base_url+url,headers=self.header,
                                        params=params,timeout=120)
            else:
                resp = requests.request('GET',self.base_url+url,
                                        headers=self.header,timeout=120)
        except requests.exceptions.Timeout:
            print('Request {} timed out, trying again'.format(url))
            return self.get_data(url,params)

        # try:
        #     self.rem_req = int(resp.headers['x-ratelimit-remaining'])
        #     #message('{} requests remaining'.format(self.rem_req))
        # except KeyError:
        #     self.rem_req -= 1

        if resp.status_code != 200:
            message('{} request failed with code {} and reason {}'.format(
                url,resp.status_code,resp.reason,resp.reason))
            return {}

        return resp.json()

class BattleData:
    def __init__(self,requester_in):
        self.decks = []
        self.clan_trophies = []
        self.trophies = []
        self.requester = requester_in
        self.player_queue = queue.Queue()

    def parse_battle(self,battle):
        #print(battle['type'])
        if battle['type'] != 'clanWarWarDay' and battle['type'] != 'PvP'\
                and battle['type'] != 'challenge' and battle['type'] != 'tournament':
            return

        try:
            self.trophies.append(battle['team'][0]['startTrophies'])
        except KeyError:
            pass
        cards = [battle['utcTime'], battle['type'], battle['team'][0]['tag']]
        for card in battle['team'][0]['deck']:
            cards.append(card['name'])
        cards.append(battle['opponent'][0]['tag'])
        for card in battle['opponent'][0]['deck']:
            cards.append(card['name'])

        self.decks.append(cards)

    def download_player_battles(self,q,request):
        while True:
            #message('Waiting for a player')
            player = q.get()
            message('Requesting battles for player {}'.format(player))
            url = '/player/{}/battles'.format(player)
            battles = request.get_data(url)
            for battle in battles:
                self.parse_battle(battle)
            q.task_done()
            time.sleep(1)

    def download_clan_battles(self, q, request):
        while True:
            #message('Waiting for a clan')
            clan = q.get()
            message('Requesting battles for {}'.format(clan['name']))
            url = '/clan/{}/battles'.format(clan['tag'])
            params = {'type': 'war'}
            battles = request.get_data(url, params)
            time.sleep(1)
            warlog = request.get_data('/clan/{}/warlog'.format(clan['tag']))
            time.sleep(1)
            clan_data = request.get_data('/clan/{}'.format(clan['tag']))
            if len(battles)== 0 or len(warlog) == 0:
                q.task_done()
                try:
                    players = clan_data['members']
                except KeyError:
                    print(json.dumps(clan_data,sort_keys=True,indent=4, separators=(',', ': ')))
                    continue

                for player in clan_data['members']:
                    self.player_queue.put(player['tag'])
                continue

            for wclan in warlog[0]['standings']:
                if wclan['tag'] == clan['tag']:
                    self.clan_trophies.append(wclan['warTrophies'])
                    # print('{}: {}'.format(clan['name'],wclan['warTrophies']))
                    break

            for battle in battles:
                self.parse_battle(battle)

            for player in clan_data['members']:
                self.player_queue.put(player['tag'])

            q.task_done()
            time.sleep(1)

def message(s):
    print('{}: {}'.format(threading.current_thread().name, s))

if __name__ == '__main__':
    ## Import my config
    with open("api_cred.secret",'r') as f:
        data = json.load(f)
        key = data["auth"]

    #Set the request address
    base_url = 'https://api.royaleapi.com'
    #Add my dev key
    headers = {
        'auth': key
        }

    ## Create the request class
    request = ApiRequest(base_url,headers)
    req_per_sec = request.rate_limit
    num_workers = req_per_sec+1

    ## Search for top war clans
    clan_tags = []
    print("Getting list of top war clans")
    top_clans = request.get_data('/top/war')
    top_clans = top_clans[0:201]
    #top_clans = top_clans[0:11]

    print('Getting battles for each clan')
    battleData = BattleData(ApiRequest)
    clan_queue = queue.Queue()

    ## Generate threads
    for i in range(1,num_workers):
        worker = threading.Thread(target=battleData.download_clan_battles,
                                  args=(clan_queue,request,),
                                  name='clan-worker-{}'.format(i),
                                  )
        worker.setDaemon(True)
        worker.start()

    for clan in top_clans:
        clan_queue.put(clan)
    clan_queue.join()

    for i in range(1,num_workers):
        worker = threading.Thread(target=battleData.download_player_battles,
                                  args=(battleData.player_queue,request,),
                                  name='player-worker-{}'.format(i))
        worker.setDaemon(True)
        worker.start()

    battleData.player_queue.join()

    #Print log info
    print('Data downloaded, now printing to file')
    print('Found ' + str(len(battleData.decks)) + ' battles.')

    decks = battleData.decks
    trophies = battleData.trophies
    clan_trophies = battleData.clan_trophies

    #Log trophy distribution to file
    with open('data/trophies.csv','a') as f:
        wr = csv.writer(f)
        for row in trophies:
            wr.writerow([row])

    with open('data/clan_trophies.csv','a') as f:
        wr = csv.writer(f)
        for row in clan_trophies:
            wr.writerow([row])

    try:
        deckExist = pd.read_csv('data/decks.csv')
    except FileNotFoundError:
        deckExist = pd.DataFrame([],columns=['Time','Mode','Home Tag','1H','2H','3H','4H','5H','6H','7H','8H',
                                             'Opponent Tag','1O','2O','3O','4O','5O','6O','7O','8O'])
    #Open the decks file and log
    bad = 0
    with open('data/decks.csv','a') as f:
        wr = csv.writer(f)
        if len(deckExist) == 0:
            wr.writerow(['Time','Mode','Home Tag','1H','2H','3H','4H','5H','6H','7H','8H',
                                             'Opponent Tag','1O','2O','3O','4O','5O','6O','7O','8O'])
        else:
            wr.writerow([])

        for indx,row in enumerate(decks):
            #Check that the battle does not already exist in the file
            foo = deckExist.loc[(deckExist['Time'] == row[0]) &
                                ((deckExist['Home Tag'] == row[2]) | (deckExist['Opponent Tag'] == row[2])) &
                                ((deckExist['Opponent Tag'] == row[11]) | (deckExist['Home Tag'] == row[11]))]
            if len(foo) == 0:
                wr.writerow(row)
            else:
                bad+=1

    print('{} repeat battles in file'.format(bad))
    #print(json.dumps(deck_data,sort_keys=True,indent=4, separators=(',', ': ')))
