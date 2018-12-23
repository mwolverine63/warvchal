import csv; import pandas as pd; import random;

def append(exist,new):
    #Assumes exist is a dataframe and new is a series
    #Concatenates two pandas objects together
    appended = pd.concat([exist.T,new],axis=1,ignore_index=True)
    return appended.T

def read_file(file):
    global mode
    #Given a csv file, reads it and returns the contents in array form
    with open(file,'r') as f:
        rd = csv.reader(f)
        decks = []
        for row in rd:
            if len(row) != 11:
                print(row)
                continue
            #Don't append the time
            if mode != 'all':
                if mode == row[2]:
                    decks.append(row)
            else:
                if row[2] == 'Challenge' or row[2] == 'Ladder' or row[2] == 'Tournament':
                    decks.append(row)
    return decks

def define_decks(decks):
    #Given an array of decks and a dict to store which deck ID goes to which index
    #Add to the uniqueDecks array any that match
    global uniqueDecks
    global spells
    global buildings
    global winConditions
    deckIDs = {}
    mdecks = {}
    #Loop through each deck in the array
    for indx,deck in enumerate(decks):
        cardSet = []
        match = 0
        #Loop through each card in the deck
        #If it is not a spell or a defensive building, add it to the cardSet
        for card in deck:
            if not card in spells:
                if card in buildings:
                    cardSet.append('Defensive Building')
                else:
                    cardSet.append(card)
        cardSet = sorted(cardSet)
        wC = 0
        for card in cardSet:
            if card in winConditions:
                cardSet.insert(0,card)
                wC = 1
                break

        #if wC == 0:
        #    for card in cardSet:
        #        if card in swinConditions:
        #            cardSet.remove(card)
        #            cardSet.insert(0,card)
        #            wC = 1
        #            break

        if wC == 0:
            #print(cardSet)
            card = 'Miscellaneous'
            cardSet.insert(0,card)

        #Loop through the decks in uniqueDecks
        #If the deck has 4 of the same cards as another deck in there,
        #it is considered the same
        uniqdecks = uniqueDecks.loc[uniqueDecks['Win Condition'] == cardSet[0]]
        if len(uniqdecks) == 0:
            deckIDs[indx] = len(uniqueDecks)
            add_deck(cardSet)
        else:
            for dind,deck in uniqdecks.iterrows():
                score = 0
                for ind,card in deck.iteritems():
                    if card in cardSet and ind != 'Win Condition':
                        score += 1
                if score >= 4 and cardSet[0] == deck[1]:
                    #print('Matched ' + str(deck) + ' to ' + str(cardSet))
                    deckIDs[indx] = deck['Deck ID']
                    match = 1
                    break

            if match != 1:
                deckIDs[indx] = len(uniqueDecks)
                add_deck(cardSet)
                #Set the ID for that index as the end of the uniqueDecks DataFrame

    return deckIDs

def add_deck(cardSet):
    #Add a given deck to the uniqueDeck dataframe
    global uniqueDecks
    #Set the ID as the end index
    id = len(uniqueDecks)
    #Insert the ID at the front
    cardSet.insert(0,id)
    #If there are less than 8 cards in the deck, add 'NaN' for buildings or spells
    if len(cardSet) < 10:
        num = 10-len(cardSet)
        array = ['Spell']*num
        cardSet.extend(array)
    #Add the deck
    foo = pd.Series(cardSet,
    index=['Deck ID','Win Condition','1','2','3','4','5','6','7','8'])
    uniqueDecks = append(uniqueDecks,foo)

#Initializing constants
#These cards fall into the same 'group' and should be removed from sorting
spells = ['Arrows','Zap','Fireball','Rocket','Lightning','Poison','The Log']
buildings = ['Cannon','Tesla','Bomb Tower','Inferno Tower']
winConditions = ['Goblin Barrel','Graveyard','Royal Giant','Elite Barbarians',
'Giant','Hog Rider','Battle Ram','Three Musketeers','P.E.K.K.A',
'Golem','Lava Hound','Miner','Mega Knight','X-Bow','Mortar','Prince']
swinConditions = ['Balloon','Dark Prince','Giant Skeleton','Mirror','Goblin Hut',
'Barbarian Hut','Minion Horde','Knight','Valkyrie','Inferno Dragon','Mini P.E.K.K.A','Goblin Gang','Bowler','Lumberjack',
'Executioner','Skeleton Barrel','Musketeer','Hunter','Goblins','Cannon Cart','Archers','Mega Minion','Bandit']

mode = 'all'
print('Mode is ' + mode)

#Reading in decks and opp_decks files
decks = read_file('decks.csv')
opp_decks = read_file('opp_decks.csv')
print(len(decks))
print(len(opp_decks))

decks_pd = pd.DataFrame(decks,columns=['Time','Tag','Mode','1','2','3','4','5','6','7','8'])
opp_decks_pd = pd.DataFrame(opp_decks,columns=['Time','Tag','Mode','1','2','3','4','5','6','7','8'])

num = int(len(decks_pd))/10
remove = []
for i in range(0,len(decks_pd)):
    if i % 10000 == 0:
        print(i)

    deck = decks_pd.iloc[i]
    odeck = opp_decks_pd.iloc[i]

    hometag = deck['Tag']
    opptag = odeck['Tag']
    time = deck['Time']

    if not i in remove:
        foo = decks_pd.loc[decks_pd['Tag'] == opptag]
        bar = opp_decks_pd.loc[opp_decks_pd['Tag'] == hometag]

        foo2 = foo.loc[foo['Time'] == time]
        bar2 = bar.loc[bar['Time'] == time]

        if len(foo2) > 1 or len(bar2) > 1:
            print("Too long!")
        elif len(foo2) == 1 and len(bar2) == 1:
            if foo2.iloc[0].name == bar2.iloc[0].name:
                remove.append(foo2.iloc[0].name)

print('Removed ' + str(len(remove)) + ' matches as duplicate.')
decks_pd = decks_pd.drop(remove)
opp_decks_pd = opp_decks_pd.drop(remove)

decks = [list(x[4:]) for x in decks_pd.itertuples()]
opp_decks = [list(x[4:]) for x in opp_decks_pd.itertuples()]

print(len(decks))
print(len(opp_decks))
print('Read in decks')
#Generating list of unique decks
uniqueDecks = pd.DataFrame([],columns=['Deck ID','Win Condition','1','2','3','4','5','6','7','8'])
deckIDs = define_decks(decks)
oppDeckIDs = define_decks(opp_decks)
#Storing unique decks to a csv file
uniqueDecks.to_csv('uniqueDecks_'+str(mode)+'.csv',index=False)
print('Generated list of unique deck IDs')
print('Found ' + str(len(uniqueDecks)) + ' unique decks.')

#Generating arrays of which deck IDs matched which opposing deck IDs
deckPts = []
oppDeckPts = []
for indx,deck in enumerate(decks):
    try:
        deckID = deckIDs[indx]
        oppDeckID = oppDeckIDs[indx]
    except KeyError:
        print(indx)
        continue

    deckPts.append(deckID)
    oppDeckPts.append(oppDeckID)

deckMatches = pd.DataFrame([],columns=['Deck','Opposing Deck'])
deckMatches['Deck'] = deckPts
deckMatches['Opposing Deck'] = oppDeckPts
deckMatches.to_csv('deckMatches_'+str(mode)+'.csv',index=False)
