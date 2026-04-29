# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 20:11:17 2024

@author: Austin
"""

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from websocket import WebSocketApp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import copy
import time
import NFLqueries
import pymysql 
import random

"""
### The following will pull a player's game log and print out their season stats ###
req = requests.get('https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/4362628/gamelog')
print(req.json())      #looking for 200
test = req.json()       #creating a test variable of output for convenience
print(test['seasonTypes'])      


#Use the following link to get a list of IDs
req = requests.get('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes?limit=1000&active=true')
print(req.json())      #looking for 200
fullDict = req.json()       #creating a test variable of output for convenience
IDdict = fullDict['items']
IDlist = []
for athlete in IDdict:
    tempList = []
    temp = str(athlete.values())    #Pulling the link from the dictionary
    chunks = temp.split("/")
    chunk = chunks[-1]          #Pulling the last element of the list, which is the one I want
    chunks = chunk.split("?")
    tempList.append(chunks[0])
    
    #Next, I need to take the player info link format, and input my ID into that link to find the player's name.
    link = 'http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/' + tempList[0] + '?lang=en&region=us'
    req2 = requests.get(link)
    data = req2.json()
    fname = data['firstName']       #Pulling the first name of the player
    tempList.append(fname)
    lname = data['lastName']        #Pulling the last name of the player
    tempList.append(lname)
    position = data['position']
    abbr = position['abbreviation']     #Pulling the player's position
    tempList.append(abbr)
    IDlist.append(tempList)         #Adding my temp list of ID, Fname, Lname, and Position to my main list.

IDlist = pd.DataFrame(IDlist)
IDlist.columns = ["ID", "FirstName", "LastName", "Position"]
IDlist.to_csv('D:/Data Science Stuff/Betting Project 3/ESPNplayerIDs.csv')
"""
def UnpackList(mainList, unpackList):
    for ob in unpackList:
        mainList.append(ob)
    return mainList

def arrayToTable(array, cols):
    table = []
    x = 0
    while x < len(array):
        temp = array[x:x+cols]
        table.append(temp)
        x+=cols
    return table

def StringContains(string, char):
    truth = 0
    for x in string:
        if x == char:
            truth+=1
        else:
            pass
    if(truth>0):
        return True
    else:
        return False

### ESPN API limits pull to 1000 players with no way of switching list of players. Need to do a team based approach instead.###
#https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/1/roster
#That link houses all of the data I could need for each player. It has ID, name, and position. All I need to do is change the number in the url to change teams
#Use 1-30, then 33&34
def GetPlayerInfo():    
    PlayerList = []
    for x in range(1,35):
        link = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(x) + '/roster'
        if(x != 31 and x != 32):
            req = requests.get(link)
            data = req.json()
            athletes = data['athletes']
            athletes = athletes[0]
            items = athletes['items']
            team = data['team']
            for player in items:
                tempList = []
                tempList.append(player['fullName'])
                tempList.append(team['abbreviation'])
                tempList.append(player['id'])
                position = player['position']
                abbr = position['abbreviation']
                tempList.append(abbr)
                PlayerList.append(tempList)
    PlayerList = pd.DataFrame(PlayerList)
    PlayerList.columns = ["Name", "Team", "EspnID", "Position"]
    return PlayerList


#PlayerList = GetPlayerInfo()
#SendEspnIDs(PlayerList)


### Time to grab player data ###

#IDs = LoadEspnIDs()
#recIDs = IDs[(IDs['Position'] == 'WR') | (IDs['Position'] == 'TE')]
#passIDs = IDs[(IDs['Position'] == 'QB')]
#rushIDs = IDs[(IDs['Position'] == 'RB')]



#This function will call the ESPN API to get the gamelog data I need for the week. The only variable that needs to be passed is a dataframe with ESPN ID, name, and position.
def GetWeeklyRecData(IDs):
    dataHeaders = ['Name', 'Team', 'Week', 'Opp', 'EspnID', 'REC','TGTS','Rec YDS', 'Yds per Rec', 'Rec TD', 'Rec LNG', 'CAR', 'Rush YDS', 'Rush AVG', 'Rush LNG', 'Rush TD', 'FUM', 'LST', 'FF', 'KB', 'Games Played', 'Career REC', 'Career TGTS', 'Career YDS', 'Career AVG', 'Career TD', 'Career LNG', 'Career FD', 'Career FUM', 'Career LST']
    logs = []
    logs.append(dataHeaders)
    for x in range(0,len(IDs)):
        espnID = str(int(IDs.iloc[x,2]))
        #The chunk below will be building out the dataset for the career statistics
        carURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/stats'
        req = requests.get(carURL)
        carData = req.json()
        try:
            categories = carData['categories']
        except:
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            categories = categories[0]
            totals = categories['totals']
            print(totals)
        
        #Everything below will be building out the dataset for the game log data
        logURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/gamelog'
        req = requests.get(logURL)
        glData = req.json()       #creating a test variable of output for convenience
        try:
            seasonTypes = glData['seasonTypes']
        except:
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            #If a player has not played so far in 2025, the stats from their most recent season will appear.
            temp = seasonTypes[0]
            if(temp['displayName'] == '2024 Regular Season' or temp['displayName'] == '2023 Regular Season' or temp['displayName'] == '2024 Postseason'):
                print(IDs.iloc[x,0], "has no stats for this season")
            else:
                seasonTypes = seasonTypes[0]
                
                categories = seasonTypes['categories']
                categories = categories[0]
                events = categories['events']
                for log in events:
                    gameID = log['eventId']
                    fullLogs = glData['events']
                    game = fullLogs[gameID]
                    gameInfo = []
                    gameInfo.append(IDs.iloc[x,0])
                    team = game['team']
                    team = team['abbreviation']
                    gameInfo.append(team)
                    gameInfo.append(game['week'])
                    opp = game['opponent']
                    opp = opp['abbreviation']
                    gameInfo.append(opp)
                    gameInfo.append(espnID)
                    gameInfo = UnpackList(gameInfo, log['stats'])
                    gameInfo = UnpackList(gameInfo, totals)
                    logs.append(gameInfo)
                    print(gameInfo)
    logs = pd.DataFrame(logs)
    logs.columns = logs.iloc[0]
    logs = logs[1:]
    return logs

#RecGameLogs = GetWeeklyRecData(recIDs)


def GetWeeklyPassData(IDs):
    dataHeaders = ['Name', 'Team', 'Week', 'Opp', 'EspnID', 'CMP','ATT','Pass YDS', 'CMP%', 'YDS per CMP', 'TDs', 'INT', 'Pass LNG', 'Sacks', 'RTG', 'QBR', 'CAR', 'Rush YDS', 'YDs Per Rush', 'Rush TDs', 'Rush LNG', 'Games Played', 'Career CMP', 'Career ATT', 'Career CMP%', 'Career YDS', 'Career YDS per CMP', 'Career TD', 'Career INT', 'Career LNG', 'Career Sacks', 'Career RTG']
    logs = []
    logs.append(dataHeaders)
    for x in range(0,len(IDs)):
        espnID = str(int(IDs.iloc[x,2]))
        #The chunk below will be building out the dataset for the career statistics
        carURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/stats'
        req = requests.get(carURL)
        carData = req.json()
        try:
            categories = carData['categories']
        except:
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            categories = categories[0]
            totals = categories['totals']
            print(totals)
        
        #Everything below will be building out the dataset for the game log data
        logURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/gamelog'
        req = requests.get(logURL)
        glData = req.json()       #creating a test variable of output for convenience
        try:
            seasonTypes = glData['seasonTypes']
        except: 
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            #If a player has not played so far in 2025, the stats from their most recent season will appear.
            temp = seasonTypes[0]
            if(temp['displayName'] == '2024 Regular Season' or temp['displayName'] == '2023 Regular Season' or temp['displayName'] == '2024 Postseason'):
                print(IDs.iloc[x,0], "has no stats for this season")
            
            else:
                seasonTypes = seasonTypes[0] #If the player was in the postseason, it adds an additional seasonType at the beginning.
                categories = seasonTypes['categories']
                categories = categories[0]
                events = categories['events']
                for log in events:
                    gameID = log['eventId']
                    fullLogs = glData['events']
                    game = fullLogs[gameID]
                    gameInfo = []
                    gameInfo.append(IDs.iloc[x,0])
                    team = game['team']
                    team = team['abbreviation']
                    gameInfo.append(team)
                    gameInfo.append(game['week'])
                    opp = game['opponent']
                    opp = opp['abbreviation']
                    gameInfo.append(opp)
                    gameInfo.append(espnID)
                    gameInfo = UnpackList(gameInfo, log['stats'])
                    gameInfo = UnpackList(gameInfo, totals)
                    logs.append(gameInfo)
                    print(gameInfo)
    logs = pd.DataFrame(logs)
    logs.columns = logs.iloc[0]
    logs = logs[1:]
    logs = logs.iloc[:,:-1]
    return logs

#PassGameLogs = GetWeeklyPassData(passIDs)



def GetWeeklyRushData(IDs):
    dataHeaders = ['Name', 'Team', 'Week', 'Opp', 'EspnID', 'CAR','RUSH YDS','RUSH AVG', 'RUSH TD', 'RUSH LNG', 'REC', 'TGTS', 'REC YDS', 'REC AVG', 'REC TD', 'REC LNG', 'FUM', 'LST', 'FF', 'KB', 'Games Played', 'Career CAR', 'Career YDS', 'Career AVG', 'Career TD', 'Career LNG', 'Career FD', 'Career FUM', 'Career FUM LST']
    logs = []
    logs.append(dataHeaders)
    for x in range(0,len(IDs)):
        espnID = str(int(IDs.iloc[x,2]))
        #The chunk below will be building out the dataset for the career statistics
        carURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/stats'
        req = requests.get(carURL)
        carData = req.json()
        try:
            categories = carData['categories']
        except:
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            categories = categories[0]
            totals = categories['totals']
            print(totals)
        
        #Everything below will be building out the dataset for the game log data
        logURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/gamelog'
        req = requests.get(logURL)
        glData = req.json()       #creating a test variable of output for convenience
        try:
            seasonTypes = glData['seasonTypes']
        except: 
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            #If a player has not played so far in 2025, the stats from their most recent season will appear.
            temp = seasonTypes[0]
            if(temp['displayName'] == '2024 Regular Season' or temp['displayName'] == '2023 Regular Season' or temp['displayName'] == '2024 Postseason' or temp['displayName'] == '2022 Regular Season'):
                print(IDs.iloc[x,0], "has no stats for this season")
            
            else:
                seasonTypes = seasonTypes[0] #If the player was in the postseason, it adds an additional seasonType at the beginning.
                categories = seasonTypes['categories']
                categories = categories[0]
                events = categories['events']
                for log in events:
                    gameID = log['eventId']
                    fullLogs = glData['events']
                    game = fullLogs[gameID]
                    gameInfo = []
                    gameInfo.append(IDs.iloc[x,0])
                    team = game['team']
                    team = team['abbreviation']
                    gameInfo.append(team)
                    gameInfo.append(game['week'])
                    opp = game['opponent']
                    opp = opp['abbreviation']
                    gameInfo.append(opp)
                    gameInfo.append(espnID)
                    gameInfo = UnpackList(gameInfo, log['stats'])
                    gameInfo = UnpackList(gameInfo, totals)
                    logs.append(gameInfo)
                    print(gameInfo)
    logs = pd.DataFrame(logs)
    logs.columns = logs.iloc[0]
    logs = logs[1:]
    logs = logs.iloc[:,:-1]
    return logs

#RushGameLogs = GetWeeklyRushData(rushIDs)




### DEBUG ###

#Need to do some data cleaning...
def CleanScapedData(data, stat):
    
    if(stat == "Rec Yds"):
        #Converting columns that should be numeric to numeric
        data = data.drop(['FF', 'KB'], axis=1)
        data['Career YDS'] = data['Career YDS'].str.replace(',', '', regex=True)     #Removing the ',' from yards that get into the thousands
        data.iloc[:,5:] = data.iloc[:,5:].apply(pd.to_numeric, errors='coerce')
        data = data.iloc[:,0:30]
    
    if(stat == "Pass Yds"):
        #Passing Data cleanup
        data = data.dropna()
        data['Career YDS'] = data['Career YDS'].str.replace(',', '', regex=True)     #Removing the ',' from yards that get into the thousands
        data.iloc[:,5:] = data.iloc[:,5:].apply(pd.to_numeric, errors='coerce')
        
    if(stat == "Rush Yds"):
        #Rushing Data cleanup
        data = data.drop(['FF', 'KB'], axis=1)
        data['Career YDS'] = data['Career YDS'].str.replace(',', '', regex=True)     #Removing the ',' from yards that get into the thousands
        data.iloc[:,5:] = data.iloc[:,5:].apply(pd.to_numeric, errors='coerce')
    
    data = data.dropna()
    return data



#Trimming down the data to just last week's
def GetLastWeek(GameLogs):
    return GameLogs[GameLogs['Week'] == GameLogs['Week'].max()]     
       
    
    
#Creating a series of new columns with per game, career averages
def GetRecCareerAves(GameLogs):
    GameLogs['Yards/G'] = GameLogs['Career YDS']/GameLogs['Games Played']
    GameLogs['TDS/G'] = GameLogs['Career TD']/GameLogs['Games Played']
    GameLogs['TGTS/G'] = GameLogs['Career TGTS']/GameLogs['Games Played']
    GameLogs['REC/G'] = GameLogs['Career REC']/GameLogs['Games Played']
    return GameLogs

#RecGameLogs = GetRecCareerAves(RecGameLogs)


def GetPassCareerAves(GameLogs):
    GameLogs['Yards/G'] = GameLogs['Career YDS']/GameLogs['Games Played']
    GameLogs['TDS/G'] = GameLogs['Career TD']/GameLogs['Games Played']
    GameLogs['INT/G'] = GameLogs['Career INT']/GameLogs['Games Played']
    GameLogs['ATT/G'] = GameLogs['Career ATT']/GameLogs['Games Played']
    return GameLogs

#PassGameLogs = GetPassCareerAves(PassGameLogs)


def GetRushCareerAves(GameLogs):
    GameLogs['Yards/G'] = GameLogs['Career YDS']/GameLogs['Games Played']
    GameLogs['TDS/G'] = GameLogs['Career TD']/GameLogs['Games Played']
    GameLogs['CAR/G'] = GameLogs['Career CAR']/GameLogs['Games Played']
    GameLogs['FD/G'] = GameLogs['Career FD']/GameLogs['Games Played']
    return GameLogs

#RushGameLogs = GetRushCareerAves(RushGameLogs)



#Initializing columns for my Last 5 Games statistics
def InitLast5Rec(GameLogs):
    GameLogs['L5Yards/G'] = 0
    GameLogs['L5TDS/G'] = 0
    GameLogs['L5TGTS/G'] = 0
    GameLogs['L5REC/G'] = 0
    return GameLogs
#RecGameLogs = InitLast5Rec(RecGameLogs)

def InitLast5Pass(GameLogs):
    GameLogs['L5Yards/G'] = 0
    GameLogs['L5TDS/G'] = 0
    GameLogs['L5INT/G'] = 0
    GameLogs['L5ATT/G'] = 0
    GameLogs['L5CMP%/G'] = 0
    GameLogs['L5RTG/G'] = 0
    GameLogs['L5QBR/G'] = 0
    return GameLogs
#PassGameLogs = InitLast5Pass(PassGameLogs)

def InitLast5Rush(GameLogs):
    GameLogs['L5Yards/G'] = 0
    GameLogs['L5TDS/G'] = 0
    GameLogs['L5CAR/G'] = 0
    return GameLogs
#RushGameLogs = InitLast5Rush(RushGameLogs)

### Last 5 Stats ###
#This is used to fix an error with ID's in the gamelogs
#RecPlayerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RecPlayerIDwithTeam.csv')


def RecLast5(GameLogs):
    NewLogs = pd.DataFrame()
    players = GameLogs['EspnID'].unique().tolist()
    for player in players:
        temp = GameLogs[GameLogs['EspnID'] == player]
        temp = temp.sort_values(['Year', 'Week'], ascending=[True,True])
        print(temp)
        temp.reset_index(drop=True, inplace=True)
        for x in range(0,len(temp)):
            if(x<5):
                if(x==0):
                    temp.loc[x,'L5Yards/G'] = 0
                    temp.loc[x,'L5TDS/G'] = 0
                    temp.loc[x,'L5TGTS/G'] = 0
                    temp.loc[x,'L5REC/G'] = 0
                else:
                    temp.loc[x,'L5Yards/G'] = sum(temp.loc[0:x-1,'Rec YDS'])/(x)
                    temp.loc[x,'L5TDS/G'] = sum(temp.loc[0:x-1,'Rec TD'])/(x)
                    temp.loc[x,'L5TGTS/G'] = sum(temp.loc[0:x-1,'TGTS'])/(x)
                    temp.loc[x,'L5REC/G'] = sum(temp.loc[0:x-1,'REC'])/(x) 
            else:
                temp.loc[x,'L5Yards/G'] = sum(temp.loc[x-4:x,'Rec YDS'])/5
                temp.loc[x,'L5TDS/G'] = sum(temp.loc[x-4:x,'Rec TD'])/5
                temp.loc[x,'L5TGTS/G'] = sum(temp.loc[x-4:x,'TGTS'])/5
                temp.loc[x,'L5REC/G'] = sum(temp.loc[x-4:x,'REC'])/5
        NewLogs = pd.concat([NewLogs,temp], axis=0, ignore_index=True)
    return NewLogs
        
#RecGameLogs = RecLast5(RecGameLogs)  
#RecGameLogs = pd.merge(RecGameLogs, RecPlayerIDs, how='left', on=['Name','Team'])
#RecGameLogs['EspnID'] = RecGameLogs['ID']
#RecGameLogs = RecGameLogs.drop(columns = 'ID', axis=1)
#RecGameLogs = RecGameLogs.dropna() 
#RecGameLogs = RecGameLogs.reset_index(drop=True)



#PassPlayerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/PassPlayerIDwithTeam.csv')


def PassLast5(GameLogs):
    NewLogs = pd.DataFrame()
    players = GameLogs['EspnID'].unique().tolist()
    for player in players:
        temp = GameLogs[GameLogs['EspnID'] == player]
        temp = temp.sort_values(['Year', 'Week'], ascending=[True,True])
        temp.reset_index(drop=True, inplace=True)
        for x in range(0,len(temp)):
            if(x<5):
                if(x==0):
                    temp.loc[x,'L5Yards/G'] = 0
                    temp.loc[x,'L5TDS/G'] = 0
                    temp.loc[x,'L5INT/G'] = 0
                    temp.loc[x,'L5ATT/G'] = 0
                    temp.loc[x,'L5CMP%/G'] = 0
                    temp.loc[x,'L5RTG/G'] = 0
                    temp.loc[x,'L5QBR/G'] = 0
                else:
                    temp.loc[x,'L5Yards/G'] = sum(temp.loc[0:x-1,'Pass YDS'])/(x)
                    temp.loc[x,'L5TDS/G'] = sum(temp.loc[0:x-1,'TDS'])/(x)
                    temp.loc[x,'L5INT/G'] = sum(temp.loc[0:x-1,'INT'])/(x)
                    temp.loc[x,'L5ATT/G'] = sum(temp.loc[0:x-1,'ATT'])/(x)
                    temp.loc[x,'L5CMP%/G'] = sum(temp.loc[0:x-1,'CMP%'])/(x)
                    temp.loc[x,'L5RTG/G'] = sum(temp.loc[0:x-1,'RTG'])/(x)
                    temp.loc[x,'L5QBR/G'] = sum(temp.loc[0:x-1,'QBR'])/(x)
            else:
                temp.loc[x,'L5Yards/G'] = sum(temp.loc[x-4:x,'Pass YDS'])/5
                temp.loc[x,'L5TDS/G'] = sum(temp.loc[x-4:x,'TDS'])/5
                temp.loc[x,'L5INT/G'] = sum(temp.loc[x-4:x,'INT'])/5
                temp.loc[x,'L5ATT/G'] = sum(temp.loc[x-4:x,'ATT'])/5
                temp.loc[x,'L5CMP%/G'] = sum(temp.loc[x-4:x,'CMP%'])/5
                temp.loc[x,'L5RTG/G'] = sum(temp.loc[x-4:x,'RTG'])/5
                temp.loc[x,'L5QBR/G'] = sum(temp.loc[x-4:x,'QBR'])/5
        NewLogs = pd.concat([NewLogs,temp], axis=0, ignore_index=True)
        print(temp)   
    return NewLogs
        
#PassGameLogs = PassLast5(PassGameLogs)  
#PassGameLogs = pd.merge(PassGameLogs, PassPlayerIDs, how='left', on=['Name','Team'])
#PassGameLogs['EspnID'] = PassGameLogs['ID']
#PassGameLogs = PassGameLogs.drop(columns = 'ID', axis=1) 
#PassGameLogs = PassGameLogs.dropna()
#PassGameLogs = PassGameLogs.reset_index(drop=True)


#RushPlayerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RushPlayerIDwithTeam.csv')

 
def RushLast5(GameLogs):
    NewLogs = pd.DataFrame()
    players = GameLogs['EspnID'].unique().tolist()
    for player in players:
        temp = GameLogs[GameLogs['EspnID'] == player]
        temp = temp.sort_values(['Year', 'Week'], ascending=[True,True])
        temp.reset_index(drop=True, inplace=True)
        for x in range(0,len(temp)):
            if(x<5):
                if(x==0):
                    temp.loc[x,'L5Yards/G'] = 0
                    temp.loc[x,'L5TDS/G'] = 0
                    temp.loc[x,'L5Car/G'] = 0
                else:
                    temp.loc[x,'L5Yards/G'] = sum(temp.loc[0:x-1,'Rush YDS'])/(x)
                    temp.loc[x,'L5TDS/G'] = sum(temp.loc[0:x-1,'Rush TD'])/(x)
                    temp.loc[x,'L5Car/G'] = sum(temp.loc[0:x-1,'Car'])/(x)
            else:
                temp.loc[x,'L5Yards/G'] = sum(temp.loc[x-4:x,'Rush YDS'])/5
                temp.loc[x,'L5TDS/G'] = sum(temp.loc[x-4:x,'Rush TD'])/5
                temp.loc[x,'L5Car/G'] = sum(temp.loc[x-4:x,'Car'])/5
        NewLogs = pd.concat([NewLogs,temp], axis=0, ignore_index=True)
        print(temp)   
    return NewLogs
        
#RushGameLogs = RushLast5(RushGameLogs) 
#RushGameLogs = pd.merge(RushGameLogs, RushPlayerIDs, how='left', on=['Name','Team'])
#RushGameLogs['EspnID'] = RushGameLogs['ID']
#RushGameLogs = RushGameLogs.drop(columns = 'ID', axis=1) 
#RushGameLogs = RushGameLogs.dropna()
#RushGameLogs = RushGameLogs.reset_index(drop=True) 

#Initializing columns for my Last Game stats.
def InitLastRec(GameLogs):
    GameLogs['LYards/G'] = 0
    GameLogs['LTDS/G'] = 0
    GameLogs['LTGTS/G'] = 0
    GameLogs['LREC/G'] = 0
    return GameLogs
#RecGameLogs = InitLastRec(RecGameLogs)
#Setting the year, which is the last column in the dataset.
#RecGameLogs = RecGameLogs.drop('Year', axis=1)
#RecGameLogs['Year'] = 2024 

def InitLastPass(GameLogs):
    GameLogs['LYards/G'] = 0
    GameLogs['LTDS/G'] = 0
    GameLogs['LINT/G'] = 0
    GameLogs['LATT/G'] = 0
    GameLogs['LCMP%/G'] = 0
    GameLogs['LRTG/G'] = 0
    GameLogs['LQBR/G'] = 0
    return GameLogs
#PassGameLogs = InitLastPass(PassGameLogs)
#Setting the year, which is the last column in the dataset.
#PassGameLogs = PassGameLogs.drop('Year', axis=1)
#PassGameLogs['Year'] = 2024

def InitLastRush(GameLogs):
    GameLogs['LYards/G'] = 0
    GameLogs['LTDS/G'] = 0
    GameLogs['LCAR/G'] = 0
    return GameLogs
#RushGameLogs = InitLastRush(RushGameLogs)
#Setting the year, which is the last column in the dataset.
#RushGameLogs = RushGameLogs.drop('Year', axis=1)
#RushGameLogs['Year'] = 2024 


###Last Start###

def RecLast(GameLogs):
    for x in range(0,len(GameLogs)):
        try:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']): 
                print("")
            
        except:
            print("No prior data for this player")
        
        else:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']):
                GameLogs.loc[x, 'LYards'] = GameLogs.loc[x-1, 'Rec YDS']
                GameLogs.loc[x, 'LTDS'] = GameLogs.loc[x-1, 'Rec TD']
                GameLogs.loc[x, 'LTGTS'] = GameLogs.loc[x-1, 'TGTS']
                GameLogs.loc[x, 'LREC'] = GameLogs.loc[x-1, 'REC']
                
    return GameLogs
#RecGameLogs = RecLast(RecGameLogs)

def PassLast(GameLogs):
    for x in range(0,len(GameLogs)):
        try:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']): 
                print("")
            
        except:
            print("No prior data for this player")
        
        else:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']):
                GameLogs.loc[x, 'LYards'] = GameLogs.loc[x-1, 'Pass YDS']
                GameLogs.loc[x, 'LTDS'] = GameLogs.loc[x-1, 'TDS']
                GameLogs.loc[x, 'LINT'] = GameLogs.loc[x-1, 'INT']
                GameLogs.loc[x, 'LATT'] = GameLogs.loc[x-1, 'ATT']
                GameLogs.loc[x, 'LCMP%'] = GameLogs.loc[x-1, 'CMP%']
                GameLogs.loc[x, 'LRTG'] = GameLogs.loc[x-1, 'RTG']
                GameLogs.loc[x, 'LQBR'] = GameLogs.loc[x-1, 'QBR']
                
    return GameLogs
#PassGameLogs = PassLast(PassGameLogs)
    
def RushLast(GameLogs):
    for x in range(0,len(GameLogs)):
        try:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']): 
                print("")
            
        except:
            print("No prior data for this player")
        
        else:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']):
                GameLogs.loc[x, 'LYards'] = GameLogs.loc[x-1, 'Rush YDS']
                GameLogs.loc[x, 'LTDS'] = GameLogs.loc[x-1, 'Rush TD']
                GameLogs.loc[x, 'LCAR'] = GameLogs.loc[x-1, 'Car']
                
    return GameLogs
#RushGameLogs = RushLast(RushGameLogs)

#Can use my SendGameLogs function here to send data to the DB
#SendRecGameLogs(RecGameLogs)
#SendRushGameLogs(RushGameLogs)
#SendPassGameLogs(PassGameLogs)


### Betting Lines Scraper ###
time.sleep(random.uniform(2, 5))

def LinesScraper(URL):
    req = requests.get(URL)
    print(req)
    
    parser = bs(req.content, 'html.parser')   #Parsing page content (which is written in html).
    
    pull = parser.find('div', class_='leagueTablesContainer-RmVef')    #Finding my desired class.
    
    content = pull.find_all('a')
    
    linkList = []
    for stuff in content:
        temp = str(stuff)   #I want to turn the path into text, and then I'll be able to parse the data and pull the correct link.
        link1, link2 = temp.split("href=\"")
        link, link1 = link2.split("\"></a>")     
        link, link1 = link.split("/?egid")      
        link1 = link1.replace("amp;", "")    #This is the last processing of the scraped link. Both the first and second splits will be used.
        link = link.replace("/matchup", "")
        print(link)
        link = "https://www.oddstrader.com" + link + '/player-props/?egid' + link1
        linkList.append(link)
        print(link)
    
    #The following code will need to use selenium to at least click onto the pop up.
    games = []
    failed = []
    finalLinks = []
    
    for link in linkList:
        #options = Options()
        
        #options.add_argument("--disable-extensions") options=options
        
        driver = webdriver.Edge()
        try:
            driver.get(link)
            
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'showMore-Q3CX0')))
       
        except: 
            print("Connection Failed")
            
            failed.append(link)
            
        else:
            button = driver.find_element(By.CLASS_NAME, 'showMore-Q3CX0')
            
            button.click()
            
            time.sleep(random.randrange(2,10))
            
            button = driver.find_element(By.CLASS_NAME, 'showMore-Q3CX0')
            
            button.click()
            
            time.sleep(random.randrange(2,10))
            
            data = driver.find_elements(By.CLASS_NAME, 'content-PgEMq')
            games.append(data[0].text)
            
            
            time.sleep(random.randrange(2,10))
            
            finalLinks.append(link)
        
    finalLinks.extend(failed)
    return games, finalLinks, failed

def FailScraper(failedLinks, games):
    failed = []
    for link in failedLinks:
        #options = Options()
        
        #options.add_argument("--disable-extensions") options=options
        
        driver = webdriver.Edge()
        try:
            driver.get(link)
            
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'showMore-Q3CX0')))
        except:
            print("Connection Failed")
            failed.append(link)
        else:
            
            button = driver.find_element(By.CLASS_NAME, 'showMore-Q3CX0')
            
            button.click()
            
            time.sleep(random.randrange(2,10))
            
            button = driver.find_element(By.CLASS_NAME, 'showMore-Q3CX0')
            
            button.click()
            
            time.sleep(random.randrange(2,10))
            
            data = driver.find_elements(By.CLASS_NAME, 'content-PgEMq')
            games.append(data[0].text)
            
            
            time.sleep(random.randrange(2,10))
    
    
    return games, failed


#week1 = 'https://www.oddstrader.com/nfl/?egid=10&eid=4733141&seid=42499'

def ParseTeamsFromLink(data):
    teamList = []
    for team in data:
        temp1, temp2 = team.split("-vs-")
        tempx, temp1 = temp1.split("/event/")
        temp2, tempx = temp2.split("/player-props/")
        teamList.append([temp1, temp2])
    teamList = pd.DataFrame(teamList, columns=["Team 1", "Team 2"])
    return teamList

#This function will add playerIDs to the scraped and formatted betting data.
def AddPlayerID(data, teamNames, playerIDs):
    #print(data)
    fullNameT1 = data[data['Player'].str.contains('.', regex = False) == False]
    fullNameT2 = fullNameT1
    fullNameT1 = fullNameT1.drop('Team 2', axis=1)
    fullNameT2 = fullNameT2.drop('Team 1', axis=1)
    
    fullNameT1 = pd.merge(fullNameT1, teamNames, left_on='Team 1', right_on='Long Name')
    fullNameT1 = fullNameT1.drop(['Team 1', 'Long Name'], axis=1)
    #print(fullNameT1)
    
    fullNameT2 = pd.merge(fullNameT2, teamNames, left_on='Team 2', right_on='Long Name')
    fullNameT2 = fullNameT2.drop(['Team 2', 'Long Name'], axis=1)
    #print(fullNameT2)
    
    abbrNameT1 = data[data['Player'].str.contains('.', regex = False)]
    abbrNameT2 = abbrNameT1
    
    abbrNameT1 = abbrNameT1.drop('Team 2', axis=1)
    abbrNameT2 = abbrNameT2.drop('Team 1', axis=1)
    
    abbrNameT1 = pd.merge(abbrNameT1, teamNames, left_on='Team 1', right_on='Long Name')
    abbrNameT1 = abbrNameT1.drop(['Team 1', 'Long Name'], axis=1)
    #print(abbrNameT1)
    
    abbrNameT2 = pd.merge(abbrNameT2, teamNames, left_on='Team 2', right_on='Long Name')
    abbrNameT2 = abbrNameT2.drop(['Team 2', 'Long Name'], axis=1)
    #print(abbrNameT2)

    #Full Name joins. These will be much easier to do.
    fullNameT1 = pd.merge(fullNameT1, playerIDs, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    #print(fullNameT1)
    fullNameT2 = pd.merge(fullNameT2, playerIDs, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    #print(fullNameT2)
    
    #Abbr joins. Will abbreviate the playerID table names, then join them to the abbr tables
    playerIDsAbbr = playerIDs.copy()
    playerIDsAbbr.reset_index(drop=True, inplace=True)

    for x in range(0, len(playerIDsAbbr)):
        name = playerIDsAbbr.loc[x,'Name'].split(' ')
        print(name)

        #Abbreviating the first name
        abbr = name[0]
        abbr = abbr[0] + '.'
        name[0] = abbr
        #Taking care of the case where the player has a suffix in their name
        if(len(name) > 2):
            full = name[0] + ' ' + name[1] + ' ' + name[2]
        else:
            full = name[0] + ' ' + name[1]
        #Putting the abbreviated name in place of the unabbreviated
        playerIDsAbbr.loc[x,'Name'] = full

    #print(playerIDsAbbr)
    abbrNameT1 = pd.merge(abbrNameT1, playerIDsAbbr, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    abbrNameT2 = pd.merge(abbrNameT2, playerIDsAbbr, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    
    #Combine the 4 tables and return the final product
    finalTable = pd.concat([abbrNameT1, abbrNameT2, fullNameT1, fullNameT2] , ignore_index=True)
    finalTable = finalTable.drop('Name', axis=1)
    return finalTable

#This function will take the list of Strings from my line scraping function and parse it how I want.
def ParseRecLinesData(data, teamList, teamNames, playerIDs, week, year):
    trial = []
    gameCount = 0
    for game in data:
        dataList = game.split("\n")             #Each data point is seperated by new lines.

        for x in range(0, len(dataList)):

            if(dataList[x] == "RECEIVING YARDS OVER/UNDER" or dataList[x] == "RECEIVING YARDS"):   #The data point that begins the section I'm interested in is this.
                x+=1
                teamCount = 0
                
                while(dataList[x] != "PASSING TOUCHDOWNS OVER/UNDER" and dataList[x] != "PASSING TOUCHDOWNS" and dataList[x] != "RECEPTIONS" and dataList[x] != "PLAYER TO SCORE FIRST TOUCHDOWN" and dataList[x] != "PLAYER LONGEST RECEPTION"):       #The data point that ends the section I'm interested in is this.
                    temp = dataList[x]
                    
                    if(temp == '-' or temp[0] == '-' or '%' in temp or temp == 'EV' or temp == 'EXPECTED VALUE' or temp == 'COVER PROB.' or temp == 'BEST LINE' or StringContains(temp, '/') == True or temp == 'UNLOCK' or temp == 'Turbo Exclusive Picks' or temp == 'BET RATING' or temp == 'These picks are reserved for Turbo users.'):
                        if(temp == 'Turbo Exclusive Picks'):
                            trial.pop()
                            trial.pop()
                            teamCount = 0
                            pass
                        else:
                            pass
                    else:
                        trial.append(temp)
                        teamCount += 1
                        if(teamCount == 6):
                            trial.append(teamList.loc[gameCount, 'Team 1'])
                            teamCount += 1
                        if(teamCount == 7):
                            trial.append(teamList.loc[gameCount, 'Team 2'])
                            teamCount = 0
                    x+=1
                    
        gameCount += 1
    trial = arrayToTable(trial, 8)
    trial = pd.DataFrame(data=trial, columns=["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Team 1", "Team 2"])
    helper = trial.copy()
    trial["Week"] = week 
    trial = AddPlayerID(trial, teamNames, playerIDs)  
    trial["Year"] = year           
    return trial, helper

### Passing lines scraper ###


def ParsePassLinesData(data, teamList, teamNames, playerIDs, week, year):
    trial = []
    gameCount = 0
    for game in data:
        dataList = game.split("\n")             #Each data point is seperated by new lines.
        for x in range(0, len(dataList)):
            
            if(dataList[x] == "PASSING YARDS OVER/UNDER" or dataList[x] == "PASSING YARDS"):   #The data point that begins the section I'm interested in is this.
                x+=1
                teamCount = 0
                print(dataList[x])
                
                while(dataList[x] != "RUSHING YARDS OVER/UNDER" and dataList[x] != "RUSHING YARDS" and dataList[x] != "PASSING COMPLETIONS" and dataList[x] != "PASSING ATTEMPTS" and dataList[x] != "PASSING TOUCHDOWNS"):       #The data point that ends the section I'm interested in is this.
                    temp = dataList[x]
                    if(temp == '-' or temp[0] == '-' or '%' in temp or temp == 'EV' or temp == 'EXPECTED VALUE' or temp == 'COVER PROB.' or temp == 'BEST LINE' or StringContains(temp, '/') == True or temp == 'UNLOCK' or temp == 'Turbo Exclusive Picks' or temp == 'BET RATING' or temp == 'These picks are reserved for Turbo users.'):
                        if(temp == 'Turbo Exclusive Picks'):
                            trial.pop()
                            trial.pop()
                            teamCount = 0
                            pass
                        else:
                            pass
                    else:
                        if(temp == 'B. Allen'):
                            x+=2
                        else:
                            trial.append(temp)
                            teamCount += 1
                            if(teamCount == 6):
                                trial.append(teamList.loc[gameCount, 'Team 1'])
                                teamCount += 1
                            if(teamCount == 7):
                                trial.append(teamList.loc[gameCount, 'Team 2'])
                                teamCount = 0
                    x+=1
        gameCount += 1
    trial = arrayToTable(trial, 8)
    trial = pd.DataFrame(data=trial, columns=["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Team 1", "Team 2"]) 
    trial["Week"] = week
    helper = trial.copy()
    trial = AddPlayerID(trial, teamNames, playerIDs)          
    trial["Year"] = year   
    return trial, helper


### Rushing lines ###

def ParseRushLinesData(data, teamList, teamNames, playerIDs, week, year):
    trial = []
    gameCount = 0
    for game in data:
        dataList = game.split("\n")             #Each data point is seperated by new lines.
        for x in range(0, len(dataList)):
            
            if(dataList[x] == "RUSHING YARDS OVER/UNDER" or dataList[x] == "RUSHING YARDS"):   #The data point that begins the section I'm interested in is this.
                x+=1
                teamCount = 0
                
                while dataList[x] != "RECEIVING YARDS OVER/UNDER" and dataList[x] != "RECEIVING YARDS":       #The data point that ends the section I'm interested in is this.
                    temp = dataList[x]
                    if(temp == '-' or temp[0] == '-' or '%' in temp or temp == 'EV' or temp == 'EXPECTED VALUE' or temp == 'COVER PROB.' or temp == 'BEST LINE' or StringContains(temp, '/') == True or temp == 'UNLOCK' or temp == 'Turbo Exclusive Picks' or temp == 'BET RATING'):
                        if(temp == 'Turbo Exclusive Picks'):
                            trial.pop()
                            trial.pop()
                            teamCount = 0
                            pass
                        else:
                            pass
                    else:
                        if(temp == 'not needed'):
                            x+=3
                        else:
                            trial.append(temp)
                            teamCount += 1
                            if(teamCount == 6):
                                trial.append(teamList.loc[gameCount, 'Team 1'])
                                teamCount += 1
                            if(teamCount == 7):
                                trial.append(teamList.loc[gameCount, 'Team 2'])
                                teamCount = 0
                    x+=1
        gameCount += 1
    trial = arrayToTable(trial, 8)
    trial = pd.DataFrame(data=trial, columns=["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Team 1", "Team 2"]) 
    helper = trial.copy()
    trial["Week"] = week 
    trial = AddPlayerID(trial, teamNames, playerIDs)    
    trial["Year"] = year      
    return trial, helper



### Lines Processing ###
#games, links, failedLinks = LinesScraper('https://www.oddstrader.com/nfl/?egid=26&seid=42499')
#games, failedLinks = FailScraper(failedLinks, games)

 
#teamList = ParseTeamsFromLink(links)     

#teamNames = pd.read_csv('D:/Data Science Stuff/Betting Project 3/LongNameAndAbbr.csv', header=0)

#RecPlayerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RecPlayerIDwithTeam.csv')
#PassPlayerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/PassPlayerIDwithTeam.csv')
#RushPlayerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RushPlayerIDwithTeam.csv')

#RecGamesDF, test1 = ParseRecLinesData(games, teamList, teamNames, RecPlayerIDs, 17) 
#PassGamesDF, test2 = ParsePassLinesData(games, teamList, teamNames, PassPlayerIDs, 17) 
#RushGamesDF, test3 = ParseRushLinesData(games, teamList, teamNames, RushPlayerIDs, 17) 

#SendRecBettingLines(RecGamesDF)
#SendPassBettingLines(PassGamesDF)
#SendRushBettingLines(RushGamesDF)       
        





### DEF STATS SCRAPER ###

#https://www.pro-football-reference.com/years/2024/opp.htm

def DefRushScraper(URL, Year, TeamNames):
    table = []
    driver = webdriver.Edge()
    try:
        driver.get(URL)
            
        stats = driver.find_elements(By.ID, 'rushing')
    except:
        print("Connection Failed")
        
    else:
        
        stats = stats[0].text.split('\n')
        print(stats)
        for x in range(len(stats)):
            temp = stats[x].split(' ')
            if(len(temp) == 10):
                temp[1] = temp[1] + ' ' + temp[2]
                del temp[2]
            if(len(temp) == 11):
               temp[1] = temp[1] + ' ' + temp[2] + ' ' + temp[3]
               del temp[2:4]
            table.append(temp)
    
    table = pd.DataFrame(table)
    table.columns = table.iloc[0]
    table['Year'] = Year
    table = table.drop([0,33,34,35],axis=0)
    table.reset_index(inplace=True)
    table = table.drop(['index', 'Rk', 'G'],axis=1)
    
    table = pd.merge(table, TeamNames, how='left', left_on='Tm', right_on='Long Name')
    table['Tm'] = table['Short Name']
    table = table.drop(['Long Name', 'Short Name'], axis=1)
    
    return table



def DefPassScraper(URL, Year, TeamNames):
    table1 = []
    table2 = []
    driver = webdriver.Edge()
    try:
        driver.get(URL)
            
        advDef = driver.find_elements(By.ID, 'div_advanced_defense')
        passDef = driver.find_elements(By.ID, 'div_passing')
    except:
        print("Connection Failed")
        
    else:
        
        advDef = advDef[0].text.split('\n')
        passDef = passDef[0].text.split('\n')
        #print(passDef)
        for x in range(len(advDef)):
            temp = advDef[x].split(' ')
            if(len(temp) == 20):
                temp[0] = temp[0] + ' ' + temp[1]
                del temp[1]
            if(len(temp) == 21):
               temp[0] = temp[0] + ' ' + temp[1] + ' ' + temp[2]
               del temp[1:3]
            table1.append(temp)
        table1 = pd.DataFrame(table1)
        table1.columns = table1.iloc[0]
        table1 = table1.drop(0,axis=0)
        table1 = table1.drop(['G', 'Att', 'Cmp', 'Yds', 'TD', 'Air', 'YAC',	'Bltz', 'Hrry', 'QBKD', 'Sk', 'Prss', 'MTkl'],axis=1)
        #print(table1)
            
        for x in range(len(passDef)):
            temp = passDef[x].split(' ')
            #The following if statements deal with the case where the defense has no interceptions on the season. When this happens, the table has blank space where a zero will be needed.
            if(len(temp) == 24 and temp[0] != 'Avg'):
                temp.insert(10, '0')
                temp.insert(12, '0')
            if(len(temp) == 25 and temp[0] != 'Rk'):
                temp.insert(11, '0')
                temp.insert(13, '0')
            #The following if statements deal with compacting the team name
            print(temp)
            if(len(temp) == 26):
                temp[1] = temp[1] + ' ' + temp[2]
                del temp[2]
            if(len(temp) == 27):
                temp[1] = temp[1] + ' ' + temp[2] + ' ' + temp[3]
                del temp[2:4]
            table2.append(temp)
        table2 = pd.DataFrame(table2)
        table2.columns = table2.iloc[0]
        table2 = table2.drop([0,33,34,35],axis=0)
        table2 = table2.drop(['Rk', 'G', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'PD', 'Sk', 'Yds', 'QBHits', 'TFL'],axis=1)
        #print(table2)
    
    table1 = pd.merge(table1, TeamNames, how='left', left_on='Tm', right_on='Long Name')
    table1['Tm'] = table1['Short Name']
    table1 = table1.drop(['Long Name', 'Short Name'], axis=1)
    
    
    table2 = pd.merge(table2, TeamNames, how='left', left_on='Tm', right_on='Long Name')
    table2['Tm'] = table2['Short Name']
    table2 = table2.drop(['Long Name', 'Short Name'], axis=1)
    
    
    table = pd.merge(table1, table2, on='Tm')
    table['Year'] = Year
    table.reset_index(inplace=True)
    table = table.drop("index", axis=1)
    
    #Removing % symbols from my table before passing it on.
    table['Bltz%'] = table['Bltz%'].str.replace('%', '')
    table['Hrry%'] = table['Hrry%'].str.replace('%', '')
    table['QBKD%'] = table['QBKD%'].str.replace('%', '')
    table['Prss%'] = table['Prss%'].str.replace('%', '')
    
    return table



#DefRush = DefRushScraper('https://www.pro-football-reference.com/years/2024/opp.htm', 2024)

#DefPass = DefPassScraper('https://www.pro-football-reference.com/years/2024/opp.htm', 2024)

#SendDefRushing(DefRush,2024)

#SendDefPassing(DefPass,2024)




"""
    
### PART 1 ### 

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'}   
req = requests.get('https://www.pro-football-reference.com/teams/', headers=headers)
print(req)

parser = bs(req.content, 'html.parser')   #Parsing page content (which is written in html).

pull = parser.find('div', id='div_teams_active')    #Finding my desired class.

content = pull.find_all('a')                #Finding all the p tags, which have the information I need.

   
linkList = []
for stuff in content:
    temp = str(stuff)
    if("teams" in temp):
        link = temp.split("\"") 
        link = link[1]
        link = "https://www.pro-football-reference.com" + link + "2024.htm"
        linkList.append(link)
        
### PART 2 ###
#Need to determine if the player is a wr or TE, then pull their link.
count = 0
for item in linkList:
     if(count == 0):
         req = requests.get(item)
         print(req)
         parser = bs(req.content, 'html.parser')   #Parsing page content (which is written in html).
         pull = parser.find('div', id='div_rushing_and_receiving')    #Finding my desired class.
         content = pull.find_all('tr')                #Finding all the p tags, which have the information I need
         #Pulling the links for each of the skill players
         for stuff in content:
             link = stuff.find_all('a')
             temp = str(link)
             link = temp.split("\"")
             if(len(link) > 1):
                 link = link[1]
                 link = "https://www.pro-football-reference.com" + link
             tdTags = stuff.find_all('td')
             #Loop which will advance if the player is a WR or TE.
             for things in tdTags:
                 temp = things.string
                 if(temp == "WR" or temp == "TE"):
                     req = requests.get(link)
                     parser = bs(req.content, 'html.parser')   #Parsing page content (which is written in html).
                     pull = parser.find('div', id='content')    #Finding my desired class.
                     gL = pull.find('div', id='all_last5')
                     gameLog = pull.find_all('tr')
                     playerData = pull.find_all('tr')                #Finding all the p tags, which have the information I need.
                     #Working on collecting game logs
                     gLcounter = 0
                     tableCounter = 0
                     gLheaders = []
                     for game in gameLog:          ###Run from here to gLCounter += 1 to test
                         if(gLcounter == 1):
                             gLheaderData = game.find_all('th')       
                             for gLhead in gLheaderData:                  #Cycling through headers                  
                                 gLheaders.append(gLhead.string)
                             gLheaders.pop(0)   
                             gLtableLen = len(gLheaders)                     #Keeping track of the number of columns      
                             gLdata = pd.DataFrame(columns=gLheaders)           #Creating my table with proper column names and filler zeros (for the first row)
                             
                         if(gLcounter > 1):
                             test = game.find("th")
                             if "2024-" in test.text:
                                 gLtableData = game.find_all('td')
                                 filler = [0]*gLtableLen
                                 filler = [str(element) for element in filler]
                                 gLobsCounter = 0
                                 for gLobs in gLtableData:
                                     obs = gLobs.string
                                     filler[gLobsCounter] = obs
                                     gLobsCounter += 1
                                     if(gLobsCounter == gLtableLen-1):
                                         gLdata.loc[tableCounter] = filler
                                         tableCounter += 1
                                         gLobsCounter = 0
                                         print(gLdata)
                                     print(tableCounter)
                         gLcounter += 1                         
                  
                     ###Now for player stats###
                     #NEED TO FIND DIFFERENTIATOR FOR THE HEADER. SEASON DOES NOT WORK...
                     headers = []
                     for data in playerData:
                         headerTest = data.find('th')
                         print(headerTest.text)
                         if(headerTest.text == "Season"):
                             headerData = data.find_all('th')       
                             for head in headerData:                  #Cycling through headers                  
                                 headers.append(head.string)   
                             tableLen = len(headers)                     #Keeping track of the number of columns      
                             pData = pd.DataFrame(columns=headers)
                             #print(pData)
                         
                         test = str(data)
                         test = test[8:32]     #Turning the tr into a string and pulling characters 9-32 will always get "receiving_and_rushing.20" for the standard rushing and receiving
                         if(test == "receiving_and_rushing.20"):            
                             playerStats = data.find_all('td')
                             print("HAHAHAHAHAHHA")
                             for stats in playerStats:

          
         count = count+1
    
        
      
        
      
 """       
