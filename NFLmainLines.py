# -*- coding: utf-8 -*-
"""
Created on Wed Jul  2 22:42:54 2025

@author: Austin
"""

import NFLqueries
import NFLmodelling
import NFLscraperTest
import pandas as pd


### Lines Processing ###

def GrabBettingLines(attempt, link, week, year):
    #Making my initial pass at scraping this week's lines
    games, links, failedLinks = LinesScraper('https://www.oddstrader.com/nfl/')
    
    
    #Making a second pass at scraping this week's games
    games, failedLinks = FailScraper(failedLinks, games)
    
    #Pulling the team names which are imbedded in the links
    teamList = ParseTeamsFromLink(links)     

    team2 = teamList.copy()
    team2.iloc[0,:] = teamList.iloc[14,:]
    for x in range(1,len(teamList)):
        team2.iloc[x,:] = teamList.iloc[x-1,:]
    teamList = team2
    #This file is needed to connect the abbreviated names with their long form
    teamNames = pd.read_csv('D:/Data Science Stuff/Betting Project 3/LongNameAndAbbr.csv', header=0)
    
    
    #I will need player IDs with their team
    espnID = LoadEspnIDs()
    RecPlayerIDs = espnID[(espnID["Position"] == "WR") | (espnID["Position"] == "TE")]
    RecPlayerIDs = RecPlayerIDs.drop(["Position"], axis=1)
    PassPlayerIDs = espnID[espnID["Position"] == "QB"]
    PassPlayerIDs = PassPlayerIDs.drop(["Position"], axis=1)
    RushPlayerIDs = espnID[espnID["Position"] == "RB"]
    RushPlayerIDs = RushPlayerIDs.drop(["Position"], axis=1)
    
    teamsList = {'Team 1':['buffalo-bills', 'indianapolis-colts', 'atlanta-falcons', 'las-vegas-raiders', 'cleveland-browns', 'cincinnati-bengals', 'los-angeles-rams', 'new-england-patriots', 'new-york-jets', 'houston-texans', 'denver-broncos', 'new-orleans-saints', 'kansas-city-chiefs', 'chicago-bears', 'arizona-cardinals', 'baltimore-ravens'], 'Team 2':['miami-dolphins', 'tennessee-titans', 'carolina-panthers', 'washington-commanders', 'green-bay-packers', 'minnesota-vikings', 'philadelphia-eagles', 'pittsburgh-steelers', 'tampa-bay-buccaneers', 'jacksonville-jaguars', 'los-angeles-chargers', 'seattle-seahawks', 'new-york-giants', 'dallas-cowboys', 'san-francisco-49ers', 'detroit-lions']}
    teamsList = pd.DataFrame(teamsList)
    #Pulling the data I need from the raw html text
    RecGamesDF, test1 = ParseRecLinesData(games, teamList, teamNames, RecPlayerIDs, week, year) 
    PassGamesDF, test2 = ParsePassLinesData(games, teamList, teamNames, PassPlayerIDs, week, year) 
    RushGamesDF, test3 = ParseRushLinesData(games, teamList, teamNames, RushPlayerIDs, week, year) 
    
    
    #Sending the data to the database
    SendRecBettingLines(RecGamesDF)
    SendPassBettingLines(PassGamesDF)
    SendRushBettingLines(RushGamesDF)  




