import datetime as dt

# Print elements of a field in an RCLC history structure
def printUnique(loot, field, nIndent=2):
    pad = ' '*nIndent + '- '
    print(pad + ('\n'+pad).join([i for i in set([l[field] for l in loot])]))


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
