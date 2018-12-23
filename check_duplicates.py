import pandas as pd; import csv;

mode = 'all'
deckMatches = pd.read_csv('deckMatches_'+str(mode)+'.csv')
uniqueDecks = pd.read_csv('uniqueDecks_'+str(mode)+'.csv')

decks = pd.read_csv('decks.csv')
odecks = pd.read_csv('opp_decks.csv')

duplicate = 0
num = int(len(decks))/10
for i in range(0,len(decks)):
    if i % 10000 == 0:
        print(i)

    deck = decks.iloc[i]
    odeck = odecks.iloc[i]

    hometag = deck['Tag']
    opptag = odeck['Tag']
    time = deck['Time']

    foo = decks.loc[decks['Tag'] == opptag]
    bar = odecks.loc[odecks['Tag'] == hometag]

    indxs = []
    foo2 = foo.loc[foo['Time'] == time]
    bar2 = bar.loc[bar['Time'] == time]

    if len(foo2) > 1 or len(bar2) > 1:
        print("Too long!")
    elif len(foo2) == 1 and len(bar2) == 1:
        if foo2.iloc[0].name == bar2.iloc[0].name:
            duplicate += 1

        # for j in range(0,len(foo)):
        #     indx = foo.iloc[j].name
        #     if foo.iloc[j]['Time'] == time:
        #         indxs.append(indx)
        #
        # bas = bar.loc[bar.n]
        # for j in range(0,len(bar)):
        #     indx = bar.iloc[j].name
        #     if indx in indxs:
        #         duplicate += 1

print(duplicate)
