# -*- coding: utf-8 -*-
"""
Created on Wed Jul  2 22:42:54 2025

@author: Austin
"""

import NFLqueries
import NFLmodelling
import NFLscraperTest
import pandas as pd

##### SCRAPING #####

#Player IDs if I need to pull them
PlayerList = GetPlayerInfo()
SendEspnIDs(PlayerList)

ProcessGameLogs(13, 2025)
GrabDefensiveStats(13, 2025)

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


### Def Stats scraping ###
def GrabDefensiveStats(week, year):
    #Pulling the defensive rush stats for the season
    TeamNames = LoadTeamNames()
    DefRush = DefRushScraper('https://www.pro-football-reference.com/years/2025/opp.htm', year, TeamNames)
    
    
    #Pulling the defensive passing stats for the seaon
    DefPass = DefPassScraper('https://www.pro-football-reference.com/years/2025/opp.htm', year, TeamNames)
    
    
    #Sending the defensive stats to the DB
    SendDefRushing(DefRush, year, week)
    SendDefPassing(DefPass, year, week)




##### MODELLING #####
def Modelling(week, year):
    #Pulling in the game logs
    RecGameLogs = LoadRecGameLogs()
    RushGameLogs = LoadRushGameLogs()
    PassGameLogs = LoadPassGameLogs()
    
    ### Joining defensive stats ###
    
    #Loading in the defensive passing statistics
    DefPassStats = LoadDefPassing()
    DefRushStats = LoadDefRushing()
    
    
    #Performing a left-outer join to combine the game log data with the def passing stats data. NEED TO UPGRADE THIS MERGE.
    NFLdataRec = pd.merge(RecGameLogs, DefPassStats, left_on=['Opp','Week','Year'], right_on=['Opp', 'Week', 'Year'], how='left')
    NFLdataPass = pd.merge(PassGameLogs, DefPassStats, left_on=['Opp','Week','Year'], right_on=['Opp', 'Week', 'Year'], how='left')
    NFLdataRush = pd.merge(RushGameLogs, DefRushStats, left_on=['Opp','Week','Year'], right_on=['Opp', 'Week', 'Year'], how='left')
    
    
    yTrainRec,xTrainRec,yTestRec,xTestRec,TrainingDataRec,TestingDataRec = modelPrep(NFLdataRec, week, year, "Rec")
    yTrainRush,xTrainRush,yTestRush,xTestRush,TrainingDataRush,TestingDataRush = modelPrep(NFLdataRush, week, year, "Rush")
    yTrainPass,xTrainPass,yTestPass,xTestPass,TrainingDataPass,TestingDataPass = modelPrep(NFLdataPass, week, year, "Pass")
    
    schedule = LoadSchedule(year)
       
       
    xTestRec = predPrep(xTestRec, DefPassStats, schedule, espnID, week, year, "Rec")
    xTestRush = predPrep(xTestRush, DefRushStats, schedule, espnID, week, year, "Rush")
    xTestPass = predPrep(xTestPass, DefPassStats, schedule, espnID, week, year, "Pass")
            
    resultsRec = BuildModel(yTrainRec, xTrainRec, yTestRec, xTestRec, TrainingDataRec, TestingDataRec, "Rec", "Ridge", week, "Ridge_1.0")
    resultsRush = BuildModel(yTrainRush, xTrainRush, yTestRush, xTestRush, TrainingDataRush, TestingDataRush, "Rush", "Ridge", week, "Ridge_1.0")
    resultsPass = BuildModel(yTrainPass, xTrainPass, yTestPass, xTestPass, TrainingDataPass, TestingDataPass, "Pass", "Ridge", week, "Ridge_1.0")
    
    
    #Sending forecasts to the DB
    SendRecYdsForecast(resultsRec, year)
    SendRushYdsForecast(resultsRush, year)
    SendPassYdsForecast(resultsPass, year)
    
    #Loading Betting Lines back in
    RecBettingData = LoadRecBettingLines()
    RushBettingData = LoadRushBettingLines()
    PassBettingData = LoadPassBettingLines()
    
    #Calculating prediction data. Use the upcoming week.
    predRec = Predictions(resultsRec, RecBettingData, espnID, "Rec", week, year, "Ridge_1.0")
    predRush = Predictions(resultsRush, RushBettingData, espnID, "Rush", week, year, "Ridge_1.0")
    predPass = Predictions(resultsPass, PassBettingData, espnID, "Pass", week, year, "Ridge_1.0")
    
    #Sending prediction data to the DB
    SendRecYdsPredictions(predRec)
    SendRushYdsPredictions(predRush)
    SendPassYdsPredictions(predPass)
    
    
    #Loading predictions back in
    predRec = LoadRecYdsPredictions()
    predRush = LoadRushYdsPredictions()
    predPass = LoadPassYdsPredictions()
    
    #Selecting my best bets for the week.
    Best = BestBets(predRec, predRush, predPass, "Ridge_1.0", "Ridge_1.0", "Ridge_1.0", 0.05, 0.25, 20, week, year)
    
    #Sending best bets to the database
    SendBestBets(Best)

##### REVIEW #####

### AFTER GAMES ARE COMPLETE ###

def ReviewResults(week, year):
    #Pull my predictions back out of the database
    resultsRec = LoadRecYdsPredictions()
    resultsRush = LoadRushYdsPredictions()
    resultsPass = LoadPassYdsPredictions()
    
    #Narrow the predicitons down to the most recent week.
    resultsRec = resultsRec[(resultsRec['Week'] == week) & (resultsRec['Year'] == year) & (resultsRec['Model'] == 'Ridge_1.0')]
    resultsRush = resultsRush[(resultsRush['Week'] == week) & (resultsRush['Year'] == year) & (resultsRush['Model'] == 'Ridge_1.0')]
    resultsPass = resultsPass[(resultsPass['Week'] == week) & (resultsPass['Year'] == year) & (resultsPass['Model'] == 'Ridge_1.0')]
    
    #Pull fresh game logs
    RecGameLogs = LoadRecGameLogs()
    RushGameLogs = LoadRushGameLogs()
    PassGameLogs = LoadPassGameLogs()
    
    #Prep the columns for my model evaluation function
    predRecPrep = resultsRec[["Player", "Predicted Yards"]]
    predRushPrep = resultsRush[["Player", "Predicted Yards"]]
    predPassPrep = resultsPass[["Player", "Predicted Yards"]]
    
    #Load in betting lines for review
    RecBettingLines = LoadRecBettingLines()
    RushBettingLines = LoadRushBettingLines()
    PassBettingLines = LoadPassBettingLines()
    
    #Evaluating the results for each stat
    finalResultsRec = modEvalRec(predRecPrep, RecGameLogs, RecBettingLines, week, year)
    finalResultsRush = modEvalRush(predRushPrep, RushGameLogs, RushBettingLines, week, year)
    finalResultsPass = modEvalPass(predPassPrep, PassGameLogs, PassBettingLines, week, year)
    
    #Calculate the overall results for the week
    weeklyRecRes = WeeklyResults(finalResultsRec, week, year,"Ridge_1.0")
    weeklyRushRes = WeeklyResults(finalResultsRush, week, year,"Ridge_1.0")
    weeklyPassRes = WeeklyResults(finalResultsPass, week, year,"Ridge_1.0")
    
    #Send overall results to the DB
    SendWeeklyRes(weeklyRecRes, "Rec")
    SendWeeklyRes(weeklyRushRes, "Rush")
    SendWeeklyRes(weeklyPassRes, "Pass")
    
    #Determine the results of the best bets of the week and send back to the database
    Best = LoadBestBets()
    BestRes = BestResults(week, year, Best, RecGameLogs, RushGameLogs, PassGameLogs)
    SendBestBetsResults(BestRes)

  

def CalculateCareerResults(betAmount, week, year):
    #Load in full list of predictions for career results
    resultsRec = LoadRecYdsPredictions()
    resultsRush = LoadRushYdsPredictions()
    resultsPass = LoadPassYdsPredictions()
    
    
    #Compute the results for all players
    RecCareerRes = CareerResults(resultsRec, RecGameLogs, "Rec", "Over", "Ridge_1.0")
    RecCareerRes = CareerResults(resultsRec, RecGameLogs, "Rec", "Under", "Ridge_1.0")
    RushCareerRes = CareerResults(resultsRush, RushGameLogs, "Rush", "Over", "Ridge_1.0")
    RushCareerRes = CareerResults(resultsRush, RushGameLogs, "Rush", "Under", "Ridge_1.0")
    PassCareerRes = CareerResults(resultsPass, PassGameLogs, "Pass", "Over", "Ridge_1.0")
    PassCareerRes = CareerResults(resultsPass, PassGameLogs, "Pass", "Under", "Ridge_1.0")
    
    #Send to the DB
    SendCareerRecPreds(RecCareerRes, "Over", "Ridge_1.0")
    SendCareerRushPreds(RushCareerRes, "Over", "Ridge_1.0")
    SendCareerPassPreds(PassCareerRes, "Over", "Ridge_1.0")
            
    
    
    #Calculating my wins and losses for the week
    RecPayout = CalcPayout(RecCareerRes, betAmount, week, year)
    RushPayout = CalcPayout(RushCareerRes, betAmount, week, year)   
    PassPayout = CalcPayout(PassCareerRes, 10, 6, 2025)      



