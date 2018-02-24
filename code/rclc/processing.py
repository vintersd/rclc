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

