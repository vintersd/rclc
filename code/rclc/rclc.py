import csv
import datetime as dt


# Read multiple RCLC history files and remove duplicates
def load(fnames):
    lootAll = []
    for f in fnames:
        lootAll += loadFile(f)
    return [dict(y) for y in set(tuple(x.items()) for x in lootAll)]
    

# Read RCLootCouncil history from csv
def loadFile(fname):
    reader = csv.DictReader(open(fname, 'r'), skipinitialspace=True)
    loot = [line for line in reader]

    # Associate tokens with equipLocs
    tokenLocs = {'Chest': 'Chest', 'Cloak': 'Back', 'Gauntlets': 'Hands',
                 'Helm': 'Head', 'Leggings': 'Legs', 'Shoulders': 'Shoulder'}
    # Associate classes with armor types and tier groups
    armorTypes = {}
    armorTypes.update(dict.fromkeys(['MAGE','WARLOCK','PRIEST'],'Cloth'))
    armorTypes.update(dict.fromkeys(['ROGUE','DRUID','DEMONHUNTER','MONK'],'Leather'))
    armorTypes.update(dict.fromkeys(['HUNTER','SHAMAN'],'Mail'))
    armorTypes.update(dict.fromkeys(['PALADIN','WARRIOR','DEATHKNIGHT'],'Plate'))
    tierGroups = {}
    tierGroups.update(dict.fromkeys(['PALADIN', 'PRIEST', 'WARLOCK', 'DEMONHUNTER'],'Conqueror'))
    tierGroups.update(dict.fromkeys(['WARRIOR', 'HUNTER', 'SHAMAN', 'MONK'],'Protector'))
    tierGroups.update(dict.fromkeys(['ROGUE', 'DEATHKNIGHT', 'MAGE', 'DRUID'], 'Vanquisher'))

    # Loot structure processing
    for i, l in enumerate(loot):
        # Assign an equipLoc to armor tokens
        for t, s in tokenLocs.iteritems():
            if l['subType'] == 'Armor Token' and t in l['item']:
                loot[i]['equipLoc'] = s
        # Assign an equipLoc to relics
        if l['subType'] == 'Artifact Relic':
            loot[i]['equipLoc'] = 'Relic'
        # Rename "Miscellaneous" to "Misc"
        if l['subType'] == 'Miscellaneous':
            loot[i]['subType'] = 'Misc'
        # Trim server names from player names and deal with special chars
        loot[i]['player'] = l['player'].split('-')[0].decode('cp1252').encode('utf-8')
        # Convert timestamps to a useable format
        # datestr = l['date'] + ' ' + l['time']
        datestr = l['date'] + ' ' + '00:00:00'  # ignore time of day
        loot[i]['time'] = dt.datetime.strptime(datestr, '%m/%d/%y %H:%M:%S')
        # Assign armor types to classes
        loot[i]['armorType'] = armorTypes[loot[i]['class']]
        # Assign tier groups to classes
        loot[i]['tierGroup'] = tierGroups[loot[i]['class']]
        
    return loot


# Filter an RCLC loot history struct
def filter(loot, filters):
    for f in filters:
        loot = {
            'include': [l for l in loot if any(v in l[f['field']] for v in f['value'])],
            'exclude': [l for l in loot if not any(v in l[f['field']] for v in f['value'])],
        }[f['type']]
    return loot


# Create and print a table from an RCLC data struct. Define rows and columns as
# elements of the specified fields. Add a totals column; use the "row" column as
# the left-most column. Results are sorted by descending totals.
def printTotals(loot,row,col,groupBy=''):
    if groupBy:
        # Separate loot into groups by specified field and filter
        groups = sorted(list(set([l[groupBy] for l in loot])))
        filters = [{'type': 'include', 'field': groupBy, 'value': [g]}
                   for g in groups]
    else:
        # dummy group w/ identity filter
        groups = ['']
        filters = [{'type': 'include', 'field': 'item', 'value': ['']}]
    for i,g in enumerate(groups):
        # narrow loot to group
        gLoot = filter(loot,[filters[i]])
        # identify unique rows and columns
        rows = sorted(list(set([l[row] for l in gLoot])))
        cols = sorted(list(set([l[col] for l in gLoot])))
        # create table structure
        table = [{} for r in rows]
        for i,r in enumerate(rows):
            for c in cols:
                table[i][c] = sum([
                    1 for l in loot
                    if l[row]==r and l[col]==c
                ])
            table[i]['Total'] = sum([table[i][c] for c in cols])
            table[i][row] = r
        # Sort by total
        table = sorted(table, key=lambda t: t['Total'], reverse=True)        
        # Print table
        printTable(table,[row] + cols + ['Total'],title=g)


# Print a table (use org table format for easy export)
def printTable(table,cols,title=''):
    hline = '|' + '-+'*(len(cols)) + '-|'
    header = '|' + '|'.join([c.capitalize() for c in cols]) + '|'

    if title:
        print('\n- ' + title)
    print('\n' + hline)
    print(header)
    print(hline)
    for row in table:
        print('|' + '|'.join(['{}'.format(row[c]) for c in cols]) + '|')
    print(hline)


# Print elements of a field in an RCLC history structure
def printUnique(loot, field, nIndent=2):
    pad = ' '*nIndent + '- '
    print(pad + ('\n'+pad).join([i for i in set([l[field] for l in loot])]))


def printDropsByWeek(loot, startDate, nWeeks, raidDays):
    drops = sorted([l['time'] for l in loot if l['time'] > startDate])
    dayNames = ['Tu','W','Th','F','Sa','Su','M']
    table = [{} for i in range(nWeeks)]
    cols = ['Week'] + [dayNames[d] for d in raidDays] + ['Total']
    for i in range(nWeeks):
        table[i]['Total'] = 0
        rweek = startDate + dt.timedelta(7*i)
        table[i]['Week'] = '{0:02d} ({1})'.format(i+1,rweek.strftime('%m/%d/%y'))
        for d in raidDays:
            day = rweek + dt.timedelta(d)
            nDay = sum([1 for date in drops if date == day])
            table[i][dayNames[d]] = nDay if nDay > 0 else '-'
            table[i]['Total'] += nDay
    printTable(table,cols)


def wowheadLink(item):
    return '[[http://www.wowhead.com/item={}&bonus={}:{}][{}]]'.format(
        item['itemString'].split(':')[1],
        item['itemString'].split(':')[14],
        item['itemString'].split(':')[-2],
        item['item'][1:-1]
    )
    


def printPlayerHistories(loot,cols=['date','item','response','note']):
    players = sorted(list(set([l['player'] for l in loot])))
    for p in players:
        pFilt = {'type':'include', 'field':'player', 'value':[p]}
        pLoot = filter(loot,[pFilt])
        pLoot = sorted(pLoot, key=lambda t: t['time'])
        table = [{} for l in pLoot];
        for i,row in enumerate(table):
            for c in cols:
                table[i][c] = pLoot[i][c]
            table[i]['item'] = wowheadLink(pLoot[i])
        print('\n*** ' + p)
        printTable(table,cols)


def printBiSKeywords(loot,nIndent=2,keywords=['best','bis']):
    cols = ['Player','Total Pieces','"BiS" Comments','Percent']
    players = sorted(list(set([l['player'] for l in loot])))
    table = [{} for p in players]

    for i,p in enumerate(players):
        table[i]['Player'] = p
        table[i]['Total Pieces'] = sum([1 for l in loot if l['player']==p])
        table[i]['"BiS" Comments'] = sum([1 for l in loot if 
                                          l['player']==p and
                                          any([kw in l['note'].lower() for kw in keywords])
        ])
        table[i]['Percent'] = 100*table[i]['"BiS" Comments']/table[i]['Total Pieces']
    table = sorted(table, key=lambda t: t['Percent'], reverse=True)
    printTable(table,cols)
