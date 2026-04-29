# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 21:25:22 2025

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


# NFL Player Statistics and Betting Lines Scraper
# This script fetches player data from ESPN API and scrapes betting lines from OddsTrader

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def UnpackList(mainList, unpackList):
    """
    Appends all items from unpackList to mainList.
    
    Args:
        mainList: The list to append items to
        unpackList: The list containing items to be unpacked and added
    
    Returns:
        The mainList with all items from unpackList appended
    """
    for ob in unpackList:
        mainList.append(ob)
    return mainList

def arrayToTable(array, cols):
    """
    Converts a flat array into a 2D table with specified number of columns.
    
    Args:
        array: Flat list of elements
        cols: Number of columns for the resulting table
    
    Returns:
        2D list organized into rows with 'cols' columns each
    """
    table = []
    x = 0
    while x < len(array):
        temp = array[x:x+cols]  # Extract slice of 'cols' elements
        table.append(temp)
        x+=cols
    return table

def StringContains(string, char):
    """
    Checks if a character exists in a string.
    
    Args:
        string: The string to search in
        char: The character to search for
    
    Returns:
        True if character is found, False otherwise
    """
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

# ============================================================================
# ESPN API DATA RETRIEVAL
# ============================================================================

### ESPN API limits pull to 1000 players with no way of switching list of players. Need to do a team based approach instead.###
#https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/1/roster
#That link houses all of the data I could need for each player. It has ID, name, and position. All I need to do is change the number in the url to change teams
#Use 1-30, then 33&34

def GetPlayerInfo():
    """
    Fetches all NFL player information from ESPN API by iterating through team rosters.
    ESPN limits data pulls, so this function queries each team individually (teams 1-34, excluding 31 & 32).
    
    Returns:
        DataFrame with columns: Name, Team, EspnID, Position
    """
    PlayerList = []
    for x in range(1,35):
        link = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(x) + '/roster'
        if(x != 31 and x != 32):  # Teams 31 and 32 don't exist in the API
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

# ============================================================================
# WEEKLY RECEIVING DATA
# ============================================================================

def GetWeeklyRecData(IDs):
    """
    Retrieves weekly receiving statistics for players from ESPN API.
    Fetches both game log data and career totals for receivers (WR/TE).
    
    Args:
        IDs: DataFrame containing player information (Name, Team, EspnID, Position)
    
    Returns:
        DataFrame with weekly receiving stats including receptions, targets, yards, TDs, etc.
    """
    dataHeaders = ['Name', 'Team', 'Week', 'Opp', 'EspnID', 'REC','TGTS','Rec YDS', 'Yds per Rec', 'Rec TD', 'Rec LNG', 'CAR', 'Rush YDS', 'Rush AVG', 'Rush LNG', 'Rush TD', 'FUM', 'LST', 'FF', 'KB', 'Games Played', 'Career REC', 'Career TGTS', 'Career YDS', 'Career AVG', 'Career TD', 'Career LNG', 'Career FD', 'Career FUM', 'Career LST']
    logs = []
    logs.append(dataHeaders)
    
    for x in range(0,len(IDs)):
        espnID = str(int(IDs.iloc[x,2]))
        
        # Fetch career statistics
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
        
        # Fetch game log data
        logURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/gamelog'
        req = requests.get(logURL)
        glData = req.json()
        try:
            seasonTypes = glData['seasonTypes']
        except:
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            # Check if player has 2025 stats (skip if only 2024/2023 data available)
            temp = seasonTypes[0]
            if(temp['displayName'] == '2024 Regular Season' or temp['displayName'] == '2023 Regular Season' or temp['displayName'] == '2024 Postseason'):
                print(IDs.iloc[x,0], "has no stats for this season")
            else:
                seasonTypes = seasonTypes[0]
                
                categories = seasonTypes['categories']
                categories = categories[0]
                events = categories['events']
                
                # Process each game in the season
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
    logs = logs[1:]  # Remove header row from data
    return logs

# ============================================================================
# WEEKLY PASSING DATA
# ============================================================================

def GetWeeklyPassData(IDs):
    """
    Retrieves weekly passing statistics for quarterbacks from ESPN API.
    Fetches both game log data and career totals.
    
    Args:
        IDs: DataFrame containing QB information (Name, Team, EspnID, Position)
    
    Returns:
        DataFrame with weekly passing stats including completions, attempts, yards, TDs, INTs, etc.
    """
    dataHeaders = ['Name', 'Team', 'Week', 'Opp', 'EspnID', 'CMP','ATT','Pass YDS', 'CMP%', 'YDS per CMP', 'TDs', 'INT', 'Pass LNG', 'Sacks', 'RTG', 'QBR', 'CAR', 'Rush YDS', 'YDs Per Rush', 'Rush TDs', 'Rush LNG', 'Games Played', 'Career CMP', 'Career ATT', 'Career CMP%', 'Career YDS', 'Career YDS per CMP', 'Career TD', 'Career INT', 'Career LNG', 'Career Sacks', 'Career RTG']
    logs = []
    logs.append(dataHeaders)
    
    for x in range(0,len(IDs)):
        espnID = str(int(IDs.iloc[x,2]))
        
        # Fetch career statistics
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
        
        # Fetch game log data
        logURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/gamelog'
        req = requests.get(logURL)
        glData = req.json()
        try:
            seasonTypes = glData['seasonTypes']
        except: 
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            # Check if player has 2025 stats
            temp = seasonTypes[0]
            if(temp['displayName'] == '2024 Regular Season' or temp['displayName'] == '2023 Regular Season' or temp['displayName'] == '2024 Postseason'):
                print(IDs.iloc[x,0], "has no stats for this season")
            
            else:
                seasonTypes = seasonTypes[0]  # If the player was in the postseason, it adds an additional seasonType at the beginning
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
    logs = logs.iloc[:,:-1]  # Remove last column
    return logs

# ============================================================================
# WEEKLY RUSHING DATA
# ============================================================================

def GetWeeklyRushData(IDs):
    """
    Retrieves weekly rushing statistics for running backs from ESPN API.
    Fetches both game log data and career totals.
    
    Args:
        IDs: DataFrame containing RB information (Name, Team, EspnID, Position)
    
    Returns:
        DataFrame with weekly rushing stats including carries, yards, TDs, receptions, etc.
    """
    dataHeaders = ['Name', 'Team', 'Week', 'Opp', 'EspnID', 'CAR','RUSH YDS','RUSH AVG', 'RUSH TD', 'RUSH LNG', 'REC', 'TGTS', 'REC YDS', 'REC AVG', 'REC TD', 'REC LNG', 'FUM', 'LST', 'FF', 'KB', 'Games Played', 'Career CAR', 'Career YDS', 'Career AVG', 'Career TD', 'Career LNG', 'Career FD', 'Career FUM', 'Career FUM LST']
    logs = []
    logs.append(dataHeaders)
    
    for x in range(0,len(IDs)):
        espnID = str(int(IDs.iloc[x,2]))
        
        # Fetch career statistics
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
        
        # Fetch game log data
        logURL = 'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/' + espnID + '/gamelog'
        req = requests.get(logURL)
        glData = req.json()
        try:
            seasonTypes = glData['seasonTypes']
        except: 
            print(IDs.iloc[x,0], "has no stats for this season")
        else:
            # Check if player has current season stats
            temp = seasonTypes[0]
            if(temp['displayName'] == '2024 Regular Season' or temp['displayName'] == '2023 Regular Season' or temp['displayName'] == '2024 Postseason' or temp['displayName'] == '2022 Regular Season'):
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
    logs = logs.iloc[:,:-1]  # Remove last column
    return logs

# ============================================================================
# DATA CLEANING FUNCTIONS
# ============================================================================

def CleanScapedData(data, stat):
    """
    Cleans scraped NFL statistics data by converting columns to numeric types
    and handling formatting issues like commas in large numbers.
    
    Args:
        data: DataFrame containing raw scraped statistics
        stat: Type of statistic ("Rec Yds", "Pass Yds", or "Rush Yds")
    
    Returns:
        Cleaned DataFrame with proper data types and removed invalid rows
    """
    if(stat == "Rec Yds"):
        # Remove unnecessary columns and convert to numeric
        data = data.drop(['FF', 'KB'], axis=1)
        data['Career YDS'] = data['Career YDS'].str.replace(',', '', regex=True)  # Remove commas from thousands
        data.iloc[:,5:] = data.iloc[:,5:].apply(pd.to_numeric, errors='coerce')
        data = data.iloc[:,0:30]
    
    if(stat == "Pass Yds"):
        # Passing data cleanup
        data = data.dropna()
        data['Career YDS'] = data['Career YDS'].str.replace(',', '', regex=True)
        data.iloc[:,5:] = data.iloc[:,5:].apply(pd.to_numeric, errors='coerce')
        
    if(stat == "Rush Yds"):
        # Rushing data cleanup
        data = data.drop(['FF', 'KB'], axis=1)
        data['Career YDS'] = data['Career YDS'].str.replace(',', '', regex=True)
        data.iloc[:,5:] = data.iloc[:,5:].apply(pd.to_numeric, errors='coerce')
    
    data = data.dropna()
    return data

def GetLastWeek(GameLogs):
    """
    Filters game logs to return only Week 18 data.
    
    Args:
        GameLogs: DataFrame containing all game logs
    
    Returns:
        DataFrame filtered to the most recent week's games
    """
    return GameLogs[GameLogs['Week'] == GameLogs['Week'].max()]

# ============================================================================
# CAREER AVERAGE CALCULATIONS
# ============================================================================

def GetRecCareerAves(GameLogs):
    """
    Calculates per-game career averages for receiving statistics.
    
    Args:
        GameLogs: DataFrame with receiving game logs
    
    Returns:
        DataFrame with added columns for Yards/G, TDS/G, TGTS/G, REC/G
    """
    GameLogs['Yards/G'] = GameLogs['Career YDS']/GameLogs['Games Played']
    GameLogs['TDS/G'] = GameLogs['Career TD']/GameLogs['Games Played']
    GameLogs['TGTS/G'] = GameLogs['Career TGTS']/GameLogs['Games Played']
    GameLogs['REC/G'] = GameLogs['Career REC']/GameLogs['Games Played']
    return GameLogs

def GetPassCareerAves(GameLogs):
    """
    Calculates per-game career averages for passing statistics.
    
    Args:
        GameLogs: DataFrame with passing game logs
    
    Returns:
        DataFrame with added columns for Yards/G, TDS/G, INT/G, ATT/G
    """
    GameLogs['Yards/G'] = GameLogs['Career YDS']/GameLogs['Games Played']
    GameLogs['TDS/G'] = GameLogs['Career TD']/GameLogs['Games Played']
    GameLogs['INT/G'] = GameLogs['Career INT']/GameLogs['Games Played']
    GameLogs['ATT/G'] = GameLogs['Career ATT']/GameLogs['Games Played']
    return GameLogs

def GetRushCareerAves(GameLogs):
    """
    Calculates per-game career averages for rushing statistics.
    
    Args:
        GameLogs: DataFrame with rushing game logs
    
    Returns:
        DataFrame with added columns for Yards/G, TDS/G, CAR/G, FD/G
    """
    GameLogs['Yards/G'] = GameLogs['Career YDS']/GameLogs['Games Played']
    GameLogs['TDS/G'] = GameLogs['Career TD']/GameLogs['Games Played']
    GameLogs['CAR/G'] = GameLogs['Career CAR']/GameLogs['Games Played']
    GameLogs['FD/G'] = GameLogs['Career FD']/GameLogs['Games Played']
    return GameLogs

# ============================================================================
# INITIALIZE LAST 5 GAMES COLUMNS
# ============================================================================

def InitLast5Rec(GameLogs):
    """
    Initializes columns for tracking last 5 games receiving statistics.
    
    Args:
        GameLogs: DataFrame with receiving game logs
    
    Returns:
        DataFrame with new L5 (Last 5) columns initialized to 0
    """
    GameLogs['L5Yards/G'] = 0
    GameLogs['L5TDS/G'] = 0
    GameLogs['L5TGTS/G'] = 0
    GameLogs['L5REC/G'] = 0
    return GameLogs

def InitLast5Pass(GameLogs):
    """
    Initializes columns for tracking last 5 games passing statistics.
    
    Args:
        GameLogs: DataFrame with passing game logs
    
    Returns:
        DataFrame with new L5 (Last 5) columns initialized to 0
    """
    GameLogs['L5Yards/G'] = 0
    GameLogs['L5TDS/G'] = 0
    GameLogs['L5INT/G'] = 0
    GameLogs['L5ATT/G'] = 0
    GameLogs['L5CMP%/G'] = 0
    GameLogs['L5RTG/G'] = 0
    GameLogs['L5QBR/G'] = 0
    return GameLogs

def InitLast5Rush(GameLogs):
    """
    Initializes columns for tracking last 5 games rushing statistics.
    
    Args:
        GameLogs: DataFrame with rushing game logs
    
    Returns:
        DataFrame with new L5 (Last 5) columns initialized to 0
    """
    GameLogs['L5Yards/G'] = 0
    GameLogs['L5TDS/G'] = 0
    GameLogs['L5CAR/G'] = 0
    return GameLogs

# ============================================================================
# CALCULATE LAST 5 GAMES STATISTICS
# ============================================================================

def RecLast5(GameLogs):
    """
    Calculates rolling 5-game averages for receiving statistics for each player.
    For games 1-4, uses all available games. For game 5+, uses previous 5 games.
    
    Args:
        GameLogs: DataFrame with receiving game logs
    
    Returns:
        DataFrame with L5 statistics calculated for each game
    """
    NewLogs = pd.DataFrame()
    players = GameLogs['EspnID'].unique().tolist()
    
    for player in players:
        temp = GameLogs[GameLogs['EspnID'] == player]
        temp = temp.sort_values(['Year', 'Week'], ascending=[True,True])
        print(temp)
        temp.reset_index(drop=True, inplace=True)
        
        for x in range(0,len(temp)):
            if(x<5):  # For first 5 games, calculate average of all previous games
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
            else:  # After 5 games, use rolling 5-game average
                temp.loc[x,'L5Yards/G'] = sum(temp.loc[x-4:x,'Rec YDS'])/5
                temp.loc[x,'L5TDS/G'] = sum(temp.loc[x-4:x,'Rec TD'])/5
                temp.loc[x,'L5TGTS/G'] = sum(temp.loc[x-4:x,'TGTS'])/5
                temp.loc[x,'L5REC/G'] = sum(temp.loc[x-4:x,'REC'])/5
        
        NewLogs = pd.concat([NewLogs,temp], axis=0, ignore_index=True)
    return NewLogs

def PassLast5(GameLogs):
    """
    Calculates rolling 5-game averages for passing statistics for each player.
    
    Args:
        GameLogs: DataFrame with passing game logs
    
    Returns:
        DataFrame with L5 statistics calculated for each game
    """
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

def RushLast5(GameLogs):
    """
    Calculates rolling 5-game averages for rushing statistics for each player.
    
    Args:
        GameLogs: DataFrame with rushing game logs
    
    Returns:
        DataFrame with L5 statistics calculated for each game
    """
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

# ============================================================================
# INITIALIZE LAST GAME COLUMNS
# ============================================================================

def InitLastRec(GameLogs):
    """
    Initializes columns for tracking previous game receiving statistics.
    
    Args:
        GameLogs: DataFrame with receiving game logs
    
    Returns:
        DataFrame with new L (Last) columns initialized to 0
    """
    GameLogs['LYards/G'] = 0
    GameLogs['LTDS/G'] = 0
    GameLogs['LTGTS/G'] = 0
    GameLogs['LREC/G'] = 0
    return GameLogs

def InitLastPass(GameLogs):
    """
    Initializes columns for tracking previous game passing statistics.
    
    Args:
        GameLogs: DataFrame with passing game logs
    
    Returns:
        DataFrame with new L (Last) columns initialized to 0
    """
    GameLogs['LYards/G'] = 0
    GameLogs['LTDS/G'] = 0
    GameLogs['LINT/G'] = 0
    GameLogs['LATT/G'] = 0
    GameLogs['LCMP%/G'] = 0
    GameLogs['LRTG/G'] = 0
    GameLogs['LQBR/G'] = 0
    return GameLogs

def InitLastRush(GameLogs):
    """
    Initializes columns for tracking previous game rushing statistics.
    
    Args:
        GameLogs: DataFrame with rushing game logs
    
    Returns:
        DataFrame with new L (Last) columns initialized to 0
    """
    GameLogs['LYards/G'] = 0
    GameLogs['LTDS/G'] = 0
    GameLogs['LCAR/G'] = 0
    return GameLogs

# ============================================================================
# CALCULATE LAST GAME STATISTICS
# ============================================================================

def RecLast(GameLogs):
    """
    Populates last game statistics for each player's receiving data.
    Copies the previous game's stats into the current game's "Last" columns.
    
    Args:
        GameLogs: DataFrame with receiving game logs (must be sorted by player and week)
    
    Returns:
        DataFrame with last game statistics filled in
    """
    for x in range(0,len(GameLogs)):
        try:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']): 
                print("")
            
        except:
            print("No prior data for this player")
        
        else:
            if(GameLogs.loc[x, 'EspnID'] == GameLogs.loc[x-1, 'EspnID']):
                # Copy previous game stats to current game's "Last" columns
                GameLogs.loc[x, 'LYards'] = GameLogs.loc[x-1, 'Rec YDS']
                GameLogs.loc[x, 'LTDS'] = GameLogs.loc[x-1, 'Rec TD']
                GameLogs.loc[x, 'LTGTS'] = GameLogs.loc[x-1, 'TGTS']
                GameLogs.loc[x, 'LREC'] = GameLogs.loc[x-1, 'REC']
                
    return GameLogs

def PassLast(GameLogs):
    """
    Populates last game statistics for each player's passing data.
    Copies the previous game's stats into the current game's "Last" columns.
    
    Args:
        GameLogs: DataFrame with passing game logs (must be sorted by player and week)
    
    Returns:
        DataFrame with last game statistics filled in
    """
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
    
def RushLast(GameLogs):
    """
    Populates last game statistics for each player's rushing data.
    Copies the previous game's stats into the current game's "Last" columns.
    
    Args:
        GameLogs: DataFrame with rushing game logs (must be sorted by player and week)
    
    Returns:
        DataFrame with last game statistics filled in
    """
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

# ============================================================================
# BETTING LINES WEB SCRAPING
# ============================================================================

time.sleep(random.uniform(2, 5))

def LinesScraper(URL):
    """
    Scrapes betting lines data from OddsTrader website for NFL games.
    Uses Selenium to interact with dynamic page elements and extract prop bet data.
    
    Args:
        URL: OddsTrader URL for the week's games
    
    Returns:
        Tuple of (games, finalLinks, failed):
            - games: List of scraped game data strings
            - finalLinks: List of successfully scraped URLs
            - failed: List of URLs that failed to scrape
    """
    req = requests.get(URL)
    print(req)
    
    parser = bs(req.content, 'html.parser')  # Parse HTML content
    
    pull = parser.find('div', class_='leagueTablesContainer-RmVef')  # Find container with game links
    
    content = pull.find_all('a')
    
    # Extract and format game links
    linkList = []
    for stuff in content:
        temp = str(stuff)  # Convert to string for parsing
        link1, link2 = temp.split("href=\"")
        link, link1 = link2.split("\"></a>")     
        link, link1 = link.split("/?egid")      
        link1 = link1.replace("amp;", "")  # Clean up ampersand encoding
        link = link.replace("/matchup", "")
        print(link)
        link = "https://www.oddstrader.com" + link + '/player-props/?egid' + link1
        linkList.append(link)
        print(link)
    
    # Use Selenium to scrape dynamic content from each game page
    games = []
    failed = []
    finalLinks = []
    
    for link in linkList:
        driver = webdriver.Edge()
        try:
            driver.get(link)
            
            # Wait for "Show More" button to load
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'showMore-Q3CX0')))
       
        except: 
            print("Connection Failed")
            failed.append(link)
            
        else:
            # Click "Show More" button twice to load all player props
            button = driver.find_element(By.CLASS_NAME, 'showMore-Q3CX0')
            button.click()
            time.sleep(random.randrange(2,10))
            
            button = driver.find_element(By.CLASS_NAME, 'showMore-Q3CX0')
            button.click()
            time.sleep(random.randrange(2,10))
            
            # Extract content
            data = driver.find_elements(By.CLASS_NAME, 'content-PgEMq')
            games.append(data[0].text)
            
            time.sleep(random.randrange(2,10))
            finalLinks.append(link)
        
    finalLinks.extend(failed)
    return games, finalLinks, failed

def FailScraper(failedLinks, games):
    """
    Retry scraping for URLs that failed in the initial scrape attempt.
    
    Args:
        failedLinks: List of URLs that previously failed
        games: Existing list of successfully scraped game data to append to
    
    Returns:
        Tuple of (games, failed):
            - games: Updated list with newly scraped data added
            - failed: List of URLs that still failed
    """
    failed = []
    for link in failedLinks:
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

def ParseTeamsFromLink(data):
    """
    Extracts team names from OddsTrader URLs.
    
    Args:
        data: List of URLs containing team names in format "team1-vs-team2"
    
    Returns:
        DataFrame with columns "Team 1" and "Team 2"
    """
    teamList = []
    for team in data:
        temp1, temp2 = team.split("-vs-")
        tempx, temp1 = temp1.split("/event/")
        temp2, tempx = temp2.split("/player-props/")
        teamList.append([temp1, temp2])
    teamList = pd.DataFrame(teamList, columns=["Team 1", "Team 2"])
    return teamList

def AddPlayerID(data, teamNames, playerIDs):
    """
    Adds ESPN player IDs to scraped betting lines data by matching player names and teams.
    Handles both full names and abbreviated names (e.g., "J. Smith").
    
    Args:
        data: DataFrame with betting lines including Player and Team columns
        teamNames: DataFrame mapping long team names to abbreviations
        playerIDs: DataFrame with player names, teams, and ESPN IDs
    
    Returns:
        DataFrame with ESPN IDs added to betting lines data
    """
    # Separate data into full names and abbreviated names
    fullNameT1 = data[data['Player'].str.contains('.', regex = False) == False]
    fullNameT2 = fullNameT1
    fullNameT1 = fullNameT1.drop('Team 2', axis=1)
    fullNameT2 = fullNameT2.drop('Team 1', axis=1)
    
    # Join full names with team abbreviations
    fullNameT1 = pd.merge(fullNameT1, teamNames, left_on='Team 1', right_on='Long Name')
    fullNameT1 = fullNameT1.drop(['Team 1', 'Long Name'], axis=1)
    
    fullNameT2 = pd.merge(fullNameT2, teamNames, left_on='Team 2', right_on='Long Name')
    fullNameT2 = fullNameT2.drop(['Team 2', 'Long Name'], axis=1)
    
    # Handle abbreviated names
    abbrNameT1 = data[data['Player'].str.contains('.', regex = False)]
    abbrNameT2 = abbrNameT1
    
    abbrNameT1 = abbrNameT1.drop('Team 2', axis=1)
    abbrNameT2 = abbrNameT2.drop('Team 1', axis=1)
    
    abbrNameT1 = pd.merge(abbrNameT1, teamNames, left_on='Team 1', right_on='Long Name')
    abbrNameT1 = abbrNameT1.drop(['Team 1', 'Long Name'], axis=1)
    
    abbrNameT2 = pd.merge(abbrNameT2, teamNames, left_on='Team 2', right_on='Long Name')
    abbrNameT2 = abbrNameT2.drop(['Team 2', 'Long Name'], axis=1)

    # Join full names with player IDs
    fullNameT1 = pd.merge(fullNameT1, playerIDs, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    fullNameT2 = pd.merge(fullNameT2, playerIDs, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    
    # Create abbreviated version of player names for matching
    playerIDsAbbr = playerIDs.copy()
    playerIDsAbbr.reset_index(drop=True, inplace=True)

    for x in range(0, len(playerIDsAbbr)):
        name = playerIDsAbbr.loc[x,'Name'].split(' ')
        print(name)

        # Abbreviate the first name to first initial
        abbr = name[0]
        abbr = abbr[0] + '.'
        name[0] = abbr
        
        # Handle player names with suffixes (Jr., III, etc.)
        if(len(name) > 2):
            full = name[0] + ' ' + name[1] + ' ' + name[2]
        else:
            full = name[0] + ' ' + name[1]
        
        playerIDsAbbr.loc[x,'Name'] = full

    # Join abbreviated names with player IDs
    abbrNameT1 = pd.merge(abbrNameT1, playerIDsAbbr, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    abbrNameT2 = pd.merge(abbrNameT2, playerIDsAbbr, how='inner', left_on=['Player', 'Team'], right_on=['Name','Team'])
    
    # Combine all four tables
    finalTable = pd.concat([abbrNameT1, abbrNameT2, fullNameT1, fullNameT2] , ignore_index=True)
    finalTable = finalTable.drop('Name', axis=1)
    return finalTable

# ============================================================================
# PARSE BETTING LINES DATA
# ============================================================================

def ParseRecLinesData(data, teamList, teamNames, playerIDs, week, year):
    """
    Parses scraped receiving yards betting lines from raw text data.
    Extracts player names, positions, over/under lines, and payouts.
    
    Args:
        data: List of raw text strings from scraped game pages
        teamList: DataFrame with team matchups
        teamNames: DataFrame mapping team names to abbreviations
        playerIDs: DataFrame with player IDs
        week: NFL week number
        year: NFL season year
    
    Returns:
        Tuple of (trial, helper):
            - trial: Formatted DataFrame with ESPN IDs
            - helper: DataFrame without ESPN IDs for debugging
    """
    trial = []
    gameCount = 0
    
    for game in data:
        dataList = game.split("\n")  # Split by newlines to get individual data points

        for x in range(0, len(dataList)):
            # Find the receiving yards section
            if(dataList[x] == "RECEIVING YARDS OVER/UNDER" or dataList[x] == "RECEIVING YARDS"):
                x+=1
                teamCount = 0
                
                # Extract data until reaching the next section
                while(dataList[x] != "PASSING TOUCHDOWNS OVER/UNDER" and dataList[x] != "PASSING TOUCHDOWNS" and dataList[x] != "RECEPTIONS" and dataList[x] != "PLAYER TO SCORE FIRST TOUCHDOWN" and dataList[x] != "PLAYER LONGEST RECEPTION"):
                    temp = dataList[x]
                    
                    # Filter out unwanted data points (dashes, percentages, locked content, etc.)
                    if(temp == '-' or temp[0] == '-' or '%' in temp or temp == 'EV' or temp == 'EXPECTED VALUE' or temp == 'COVER PROB.' or temp == 'BEST LINE' or StringContains(temp, '/') == True or temp == 'UNLOCK' or temp == 'Turbo Exclusive Picks' or temp == 'BET RATING' or temp == 'These picks are reserved for Turbo users.'):
                        if(temp == 'Turbo Exclusive Picks'):
                            # Remove last two entries if hitting locked content
                            trial.pop()
                            trial.pop()
                            teamCount = 0
                            pass
                        else:
                            pass
                    else:
                        trial.append(temp)
                        teamCount += 1
                        # Add team names after collecting 6 data points per player
                        if(teamCount == 6):
                            trial.append(teamList.loc[gameCount, 'Team 1'])
                            teamCount += 1
                        if(teamCount == 7):
                            trial.append(teamList.loc[gameCount, 'Team 2'])
                            teamCount = 0
                    x+=1
                    
        gameCount += 1
    
    # Convert flat list to table with 8 columns per row
    trial = arrayToTable(trial, 8)
    trial = pd.DataFrame(data=trial, columns=["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Team 1", "Team 2"])
    helper = trial.copy()
    trial["Week"] = week 
    trial = AddPlayerID(trial, teamNames, playerIDs)  
    trial["Year"] = year           
    return trial, helper

def ParsePassLinesData(data, teamList, teamNames, playerIDs, week, year):
    """
    Parses scraped passing yards betting lines from raw text data.
    
    Args:
        data: List of raw text strings from scraped game pages
        teamList: DataFrame with team matchups
        teamNames: DataFrame mapping team names to abbreviations
        playerIDs: DataFrame with player IDs
        week: NFL week number
        year: NFL season year
    
    Returns:
        Tuple of (trial, helper):
            - trial: Formatted DataFrame with ESPN IDs
            - helper: DataFrame without ESPN IDs for debugging
    """
    trial = []
    gameCount = 0
    
    for game in data:
        dataList = game.split("\n")
        for x in range(0, len(dataList)):
            
            # Find the passing yards section
            if(dataList[x] == "PASSING YARDS OVER/UNDER" or dataList[x] == "PASSING YARDS"):
                x+=1
                teamCount = 0
                print(dataList[x])
                
                while(dataList[x] != "RUSHING YARDS OVER/UNDER" and dataList[x] != "RUSHING YARDS" and dataList[x] != "PASSING COMPLETIONS" and dataList[x] != "PASSING ATTEMPTS" and dataList[x] != "PASSING TOUCHDOWNS"):
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
                        # Skip specific player name that causes issues
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

def ParseRushLinesData(data, teamList, teamNames, playerIDs, week, year):
    """
    Parses scraped rushing yards betting lines from raw text data.
    
    Args:
        data: List of raw text strings from scraped game pages
        teamList: DataFrame with team matchups
        teamNames: DataFrame mapping team names to abbreviations
        playerIDs: DataFrame with player IDs
        week: NFL week number
        year: NFL season year
    
    Returns:
        Tuple of (trial, helper):
            - trial: Formatted DataFrame with ESPN IDs
            - helper: DataFrame without ESPN IDs for debugging
    """
    trial = []
    gameCount = 0
    
    for game in data:
        dataList = game.split("\n")
        for x in range(0, len(dataList)):
            
            # Find the rushing yards section
            if(dataList[x] == "RUSHING YARDS OVER/UNDER" or dataList[x] == "RUSHING YARDS"):
                x+=1
                teamCount = 0
                
                while dataList[x] != "RECEIVING YARDS OVER/UNDER" and dataList[x] != "RECEIVING YARDS" and dataList[x] != "PLAYER TO SCORE FIRST TOUCHDOWN":
                    temp = dataList[x]
                    print(temp)
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

# ============================================================================
# DEFENSIVE STATISTICS SCRAPING
# ============================================================================

def DefRushScraper(URL, Year, TeamNames):
    """
    Scrapes defensive rushing statistics from Pro Football Reference website.
    
    Args:
        URL: Pro Football Reference URL for defensive stats
        Year: NFL season year
        TeamNames: DataFrame mapping long team names to abbreviations
    
    Returns:
        DataFrame with defensive rushing stats by team
    """
    table = []
    driver = webdriver.Edge()
    try:
        driver.get(URL)
        stats = driver.find_elements(By.ID, 'rushing')
    except:
        print("Connection Failed")
        
    else:
        # Parse the rushing defense table
        stats = stats[0].text.split('\n')
        print(stats)
        for x in range(len(stats)):
            temp = stats[x].split(' ')
            # Handle team names with 2 words
            if(len(temp) == 10):
                temp[1] = temp[1] + ' ' + temp[2]
                del temp[2]
            # Handle team names with 3 words
            if(len(temp) == 11):
               temp[1] = temp[1] + ' ' + temp[2] + ' ' + temp[3]
               del temp[2:4]
            table.append(temp)
    
    table = pd.DataFrame(table)
    table.columns = table.iloc[0]
    table['Year'] = Year
    table = table.drop([0,33,34,35],axis=0)  # Remove header and footer rows
    table.reset_index(inplace=True)
    table = table.drop(['index', 'Rk', 'G'],axis=1)  # Remove unnecessary columns
    
    # Map long team names to abbreviations
    table = pd.merge(table, TeamNames, how='left', left_on='Tm', right_on='Long Name')
    table['Tm'] = table['Short Name']
    table = table.drop(['Long Name', 'Short Name'], axis=1)
    
    return table

def DefPassScraper(URL, Year, TeamNames):
    """
    Scrapes defensive passing statistics from Pro Football Reference website.
    Combines advanced defense metrics with standard passing defense stats.
    
    Args:
        URL: Pro Football Reference URL for defensive stats
        Year: NFL season year
        TeamNames: DataFrame mapping long team names to abbreviations
    
    Returns:
        DataFrame with defensive passing stats by team
    """
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
        # Parse advanced defense table
        advDef = advDef[0].text.split('\n')
        passDef = passDef[0].text.split('\n')
        
        for x in range(len(advDef)):
            temp = advDef[x].split(' ')
            # Handle multi-word team names
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
            
        # Parse passing defense table
        for x in range(len(passDef)):
            temp = passDef[x].split(' ')
            # Handle teams with no interceptions (blank spaces in table)
            if(len(temp) == 24 and temp[0] != 'Avg'):
                temp.insert(10, '0')
                temp.insert(12, '0')
            if(len(temp) == 25 and temp[0] != 'Rk'):
                temp.insert(11, '0')
                temp.insert(13, '0')
            # Handle multi-word team names
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
    
    # Map team names to abbreviations for both tables
    table1 = pd.merge(table1, TeamNames, how='left', left_on='Tm', right_on='Long Name')
    table1['Tm'] = table1['Short Name']
    table1 = table1.drop(['Long Name', 'Short Name'], axis=1)
    
    table2 = pd.merge(table2, TeamNames, how='left', left_on='Tm', right_on='Long Name')
    table2['Tm'] = table2['Short Name']
    table2 = table2.drop(['Long Name', 'Short Name'], axis=1)
    
    # Merge the two tables
    table = pd.merge(table1, table2, on='Tm')
    table['Year'] = Year
    table.reset_index(inplace=True)
    table = table.drop("index", axis=1)
    
    # Clean percentage symbols from data
    table['Bltz%'] = table['Bltz%'].str.replace('%', '')
    table['Hrry%'] = table['Hrry%'].str.replace('%', '')
    table['QBKD%'] = table['QBKD%'].str.replace('%', '')
    table['Prss%'] = table['Prss%'].str.replace('%', '')
    
    return table