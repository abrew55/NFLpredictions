# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 23:14:12 2026

@author: Austin
"""

import NFLqueries
import NFLmodelling
import NFLscraper
import pandas as pd

#Player IDs if I need to pull them
PlayerList = GetPlayerInfo()
SendEspnIDs(PlayerList)


def ProcessGameLogs(week, year):
    #Preparing IDs
    IDs = LoadEspnIDs()
    recIDs = IDs[(IDs['Position'] == 'WR') | (IDs['Position'] == 'TE')]
    passIDs = IDs[(IDs['Position'] == 'QB')]
    rushIDs = IDs[(IDs['Position'] == 'RB')]
    
    
    #Scraping data for Rec, Rush, and Pass Yards
    RecGameLogs = GetWeeklyRecData(recIDs)
    RecGameLogs = RecGameLogs.iloc[:,0:30]
    PassGameLogs = GetWeeklyPassData(passIDs)
    RushGameLogs = GetWeeklyRushData(rushIDs)
    
    
    #Taking Care of necessary data cleaning
    RecGameLogs = CleanScapedData(RecGameLogs, "Rec Yds")
    RushGameLogs = CleanScapedData(RushGameLogs, "Rush Yds")
    PassGameLogs = CleanScapedData(PassGameLogs, "Pass Yds")
    
    
    #Calculating career average data
    RecGameLogs = GetRecCareerAves(RecGameLogs)
    PassGameLogs = GetPassCareerAves(PassGameLogs)
    RushGameLogs = GetRushCareerAves(RushGameLogs)
    
    
    #Initializing the columns for my last 5 game statistics
    RecGameLogs = InitLast5Rec(RecGameLogs)
    PassGameLogs = InitLast5Pass(PassGameLogs)
    RushGameLogs = InitLast5Rush(RushGameLogs)
    
    #Initializing the columns that include my last game statistics
    RecGameLogs = InitLastRec(RecGameLogs)
    PassGameLogs = InitLastPass(PassGameLogs)
    RushGameLogs = InitLastRush(RushGameLogs)
    
    
    #Setting the year, which is the last column in the dataset.
    RecGameLogs['Year'] = year 
    
    PassGameLogs['Year'] = year
    
    RushGameLogs['Year'] = year 
    
    #Parsing data down to the most recent week
    RecGameLogs = RecGameLogs[RecGameLogs["Week"] == week]
    RushGameLogs = RushGameLogs[RushGameLogs["Week"] == week]
    PassGameLogs = PassGameLogs[PassGameLogs["Week"] == week]
    
    #Reseting index before I send to DB
    RecGameLogs.reset_index(drop=True, inplace=True)
    RushGameLogs.reset_index(drop=True, inplace=True)
    PassGameLogs.reset_index(drop=True, inplace=True)
    
    #Can use my SendGameLogs function here to send data to the DB
    SendRecGameLogs(RecGameLogs)
    SendRushGameLogs(RushGameLogs)
    SendPassGameLogs(PassGameLogs)
    
    #Loading the game logs back in to calculate the rest of the values that I need
    RecGameLogs = LoadRecGameLogs()
    RushGameLogs = LoadRushGameLogs()
    PassGameLogs = LoadPassGameLogs()
    
    
    #Calculating the Last 5 game stats, and merging to get the player IDs I need
    espnID = LoadEspnIDs()
    RecPlayerIDs = espnID[(espnID["Position"] == "WR") | (espnID["Position"] == "TE")]
    RecPlayerIDs = RecPlayerIDs.drop(["Position"], axis=1)
    RecGameLogs = RecLast5(RecGameLogs)  
    
    
    
    #Calculating the Last 5 game stats, and merging to get the player IDs I need
    PassPlayerIDs = espnID[espnID["Position"] == "QB"]
    PassPlayerIDs = PassPlayerIDs.drop(["Position"], axis=1)
    PassGameLogs = PassLast5(PassGameLogs)  
    
    
    
    #Calculating the Last 5 game stats, and merging to get the player IDs I need
    RushPlayerIDs = espnID[espnID["Position"] == "RB"]
    RushPlayerIDs = RushPlayerIDs.drop(["Position"], axis=1) 
    RushGameLogs = RushLast5(RushGameLogs) 
    
    
    
    #Calculating my last game statistics
    RecGameLogs = RecLast(RecGameLogs)
    PassGameLogs = PassLast(PassGameLogs)
    RushGameLogs = RushLast(RushGameLogs)
    
    #Parsing data down to the most recent week
    RecGameLogs = RecGameLogs[(RecGameLogs["Week"] == week) & (RecGameLogs["Year"] == year)]
    RushGameLogs = RushGameLogs[(RushGameLogs["Week"] == week) & (RushGameLogs["Year"] == year)]
    PassGameLogs = PassGameLogs[(PassGameLogs["Week"] == week) & (PassGameLogs["Year"] == year)]
    
    
    #Reseting index before I send to DB
    RecGameLogs.reset_index(drop=True, inplace=True)
    RushGameLogs.reset_index(drop=True, inplace=True)
    PassGameLogs.reset_index(drop=True, inplace=True)
    
    
    #Can use my SendGameLogs function here to send data to the DB
    FinalSendRecGameLogs(RecGameLogs, week, year)
    FinalSendRushGameLogs(RushGameLogs, week, year)
    FinalSendPassGameLogs(PassGameLogs, week, year)
    
    
    
    
    
def GrabDefensiveStats(week, year):
    #Pulling the defensive rush stats for the season
    TeamNames = LoadTeamNames()
    DefRush = DefRushScraper('https://www.pro-football-reference.com/years/2025/opp.htm', year, TeamNames)
    
    
    #Pulling the defensive passing stats for the seaon
    DefPass = DefPassScraper('https://www.pro-football-reference.com/years/2025/opp.htm', year, TeamNames)
    
    
    #Sending the defensive stats to the DB
    SendDefRushing(DefRush, year, week)
    SendDefPassing(DefPass, year, week)