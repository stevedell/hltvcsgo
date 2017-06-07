import re
import urllib2
import datetime
import json
import os.path
import httplib
import hashlib
teamdict = {"NiP":4411,"Virtus.pro":5378,"Liquid":5973,"Cloud9":5752,"Immortals":7010,"SK":6137,"fnatic":4991,"EnVyUs":5991,"G2":5995,"Natus Vincere":4608,"NRG":6673,"OpTic":6615,"mousesports":4494,"North":7533}
team = "G2"
team_id = teamdict[team]
start_date = "2017-03-15" #y-m-d
end_date = "2017-06-04"
max_records = 35
roster = []
keys = ['URL','MapWon','CT','T','startedCT','CTPistolWon','TPistolWon','CTPistolAndAEWon',"TPistolAndAEWon",'oCT','oT','oCTPistolWon',"oTPistolWon",'oCTPistolAndAEWon','oTPistolAndAEWon']
URL = "/stats/teams/matches/%d/%s?startDate=%s&endDate=%s" % (team_id,team,start_date,end_date)
class matchdata:
    date = datetime.datetime(2017,1,1)
    playerData = {}
    roundData = {}
def grabPageSSL(url):
    if '/mapstatsid/' in url:
        subkey = re.findall('(?<=/mapstatsid/)[0-9]*',url)[0]
    else:
        subkey = 'tmp'
    m = hashlib.md5()
    m.update(subkey)
    key = m.hexdigest()
    cacheDir = 'c:\\csgocache\\'
    if(os.path.isfile(cacheDir+key) and '/teams/matches/' not in url):
        f = open(cacheDir+key,'r')
        html = f.read()
        f.close()
        return html
    else:
        HOSTNAME = 'www.hltv.org'
        conn = httplib.HTTPSConnection(HOSTNAME)
        conn.putrequest('GET', url)
        conn.endheaders()
        response = conn.getresponse()
        html = response.read()
        f = open(cacheDir+key,'w')
        f.write(html)
        f.close()
        return html
def isTeam1(html):#matchPageHTML
    teams = re.findall("((?<=class=\"team-logo\" title=\")[0-9a-zA-Z/\\-\\?\\=&; \\.]*)",html)
    if(len(teams) < 2):
        print "problem grabbing team names..."
        exit()
    if teams[0].lower() == team.lower():
        return True
    return False
def extractRosterAndKills(mhtml):
    collect = False
    playerTable = ""
    for line in mhtml.split('\n'):
        if "st-teamname text-ellipsis" in line and team.lower() in line.lower():
            collect = True
        if collect:
            playerTable += line
        if collect and line.strip() == '</table>':
            break
    players = [x.replace('-','').replace('@','a').replace('.','').replace('_','') for x in re.findall("([0-9a-zA-Z@_\\-]*(?=</a></td>))",playerTable) if len(x)>0]
    kills = re.findall("((?<=<td class=\"st-kills\">)[0-9]*)",playerTable)
    pdict = {}
    for i in range(0,len(players)):
        pdict[players[i]] = kills[i]
    return pdict
def extractRosterList(mhtml):
    collect = False
    playerTable = ""
    for line in mhtml.split('\n'):
        if "st-teamname text-ellipsis" in line and team.lower() in line.lower():
            collect = True
        if collect:
            playerTable += line
        if collect and line.strip() == '</table>':
            break
    players = [x.replace('-','').replace('@','a').replace('.','').replace('_','') for x in re.findall("([0-9a-zA-Z@_\\-]*(?=</a></td>))",playerTable) if len(x)>0]
    return players
def extractRoundHtml(mhtml,team1):
    collect = False
    firstTimeRow = False
    team1Data = ""
    team2Data = ""
    for line in mhtml.split('\n'):
        if("round-history-team-row" in line and firstTimeRow == False and len(team1Data) == 0):
            firstTimeRow = True
            collect = True
        if("round-history-team-row" in line and len(team1Data) > 0):
            collect = True
        if collect == True and line.strip() == "</div>":
            collect = False
            firstTimeRow = False
        if collect == True and firstTimeRow == True:
            team1Data += line
        if collect == True and firstTimeRow == False:
            team2Data += line
    if team1:
        return team1Data
    return team2Data
def grabRoundData(mhtml,URL):
    team1 = extractRoundHtml(mhtml,True)
    team2 = extractRoundHtml(mhtml,False)
    team1_halves = team1.split('round-history-half')
    team2_halves = team2.split('round-history-half')
    if isTeam1(mhtml):
        n_CT = team1.count('ct_win.svg') + team1.count('stopwatch.svg') + team1.count('bomb_defused.svg')
        n_T = team1.count('/t_win.svg') + team1.count('bomb_exploded.svg')
        n_oCT = team2.count('ct_win.svg') + team2.count('stopwatch.svg') + team2.count('bomb_defused.svg')
        n_oT = team2.count('/t_win.svg') + team2.count('bomb_exploded.svg')
        rounds = team1.split('round-history-outcome')
        startedCT = "ct_win.svg" in team1_halves[1] or "stopwatch.svg" in team1_halves[1] or "bomb_defused.svg" in team1_halves[1] or "/t_win.svg" in team2_halves[1] or "bomb_exploded.svg" in team2_halves[1]
    else:
        n_CT = team2.count('ct_win.svg') + team2.count('stopwatch.svg') + team2.count('bomb_defused.svg')
        n_T = team2.count('/t_win.svg') + team2.count('bomb_exploded.svg')
        n_oCT = team1.count('ct_win.svg') + team1.count('stopwatch.svg') + team1.count('bomb_defused.svg')
        n_oT = team1.count('/t_win.svg') + team1.count('bomb_exploded.svg')
        rounds = team2.split('round-history-outcome')
        startedCT = "ct_win.svg" in team2_halves[1] or "stopwatch.svg" in team2_halves[1] or "bomb_defused.svg" in team2_halves[1] or "/t_win.svg" in team1_halves[1] or "bomb_exploded.svg" in team1_halves[1]
    tie = (n_CT + n_T) == (n_oCT + n_oT)
    if(tie):
        return -1
    if((n_CT + n_T)+(n_oCT+n_oT) <= 16):
        return -1
    if startedCT:
        CTPistolWon = 'emptyHistory.svg' not in rounds[0]
        TPistolWon = 'emptyHistory.svg' not in rounds[15]
        CTPistolAndAEWon = 'emptyHistory.svg' not in rounds[0] and 'emptyHistory.svg' not in rounds[1]
        TPistolAndAEWon = 'emptyHistory.svg' not in rounds[15] and 'emptyHistory.svg' not in rounds[16]
        oTPistolWon = CTPistolWon == False
        oCTPistolWon = TPistolWon == False
        oTPistolAndAEWon = oTPistolWon and 'emptyHistory.svg' in rounds[1]
        oCTPistolAndAEWon = oCTPistolWon and 'emptyHistory.svg' in rounds[16]
    else:
        CTPistolWon = 'emptyHistory.svg' not in rounds[15]
        TPistolWon = 'emptyHistory.svg' not in rounds[0]
        CTPistolAndAEWon = 'emptyHistory.svg' not in rounds[15] and 'emptyHistory.svg' not in rounds[16]
        TPistolAndAEWon = 'emptyHistory.svg' not in rounds[0] and 'emptyHistory.svg' not in rounds[1]
        oTPistolWon = CTPistolWon == False
        oCTPistolWon = TPistolWon == False
        oTPistolAndAEWon = oTPistolWon and 'emptyHistory.svg' in rounds[16]
        oCTPistolAndAEWon = oCTPistolWon and 'emptyHistory.svg' in rounds[1]
    MapWon = (n_CT + n_T) > (n_oCT + n_oT)
    if len(roster) == 0:
        playersnKills = extractRosterAndKills(mhtml)
        tmpRoster = extractRosterList(mhtml)
        for k in tmpRoster:
            roster.append(k)
            keys.append(k)
    else:
        playersnKills = extractRosterAndKills(mhtml)
        for k in playersnKills:
            if k not in roster:
                return -1
    retdict = {"URL":URL,"MapWon":int(MapWon),"CT":n_CT,"T":n_T,"oCT":n_oCT,"oT":n_oT,"startedCT":int(startedCT),"CTPistolWon":int(CTPistolWon),"TPistolWon":int(TPistolWon),"CTPistolAndAEWon":int(CTPistolAndAEWon),"TPistolAndAEWon":int(TPistolAndAEWon),
               "oCTPistolWon":int(oCTPistolWon),"oTPistolWon":int(oTPistolWon),"oCTPistolAndAEWon":int(oCTPistolAndAEWon),"oTPistolAndAEWon":int(oTPistolAndAEWon)}
    for k in playersnKills:
        retdict[k] = playersnKills[k]
    return retdict
html = grabPageSSL(URL)
matches = re.findall("((?<=<td class=\"time\"><a href=\")[0-9a-zA-Z/\\-\\?\\=&;]*)",html)
if(len(matches)==0):
    print "no matches"
    exit()
matchdict = []
for match in matches:
    if len(matchdict) >= max_records:
        break
    mhtml = grabPageSSL(match)
    rndict = grabRoundData(mhtml,match)
    if(rndict == -1):
        continue
    matchdict.append(rndict)
output = ""
for key in keys:
    output += key + "\r\n"
output += "\r\n"
for match in matchdict:
    for k in keys:
        output += str(match[k])+"\t"
    output += "\r\n"
print output