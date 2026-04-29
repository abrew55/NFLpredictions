# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 23:16:49 2026

@author: Austin
"""

import NFLqueries
import NFLmodelling
import NFLscraper
import pandas as pd


##### MODELLING #####
def Modelling(week, year, modType, modName):
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
            
    resultsRec = BuildModel(yTrainRec, xTrainRec, yTestRec, xTestRec, TrainingDataRec, TestingDataRec, "Rec", modType, week, modName)
    resultsRush = BuildModel(yTrainRush, xTrainRush, yTestRush, xTestRush, TrainingDataRush, TestingDataRush, "Rush", modType, week, modName)
    resultsPass = BuildModel(yTrainPass, xTrainPass, yTestPass, xTestPass, TrainingDataPass, TestingDataPass, "Pass", modType, week, modName)
    
    
    #Sending forecasts to the DB
    SendRecYdsForecast(resultsRec, year)
    SendRushYdsForecast(resultsRush, year)
    SendPassYdsForecast(resultsPass, year)
    
    #Loading Betting Lines back in
    RecBettingData = LoadRecBettingLines()
    RushBettingData = LoadRushBettingLines()
    PassBettingData = LoadPassBettingLines()
    
    #Calculating prediction data. Use the upcoming week.
    predRec = Predictions(resultsRec, RecBettingData, espnID, "Rec", week, year, modName)
    predRush = Predictions(resultsRush, RushBettingData, espnID, "Rush", week, year, modName)
    predPass = Predictions(resultsPass, PassBettingData, espnID, "Pass", week, year, modName)
    
    #Sending prediction data to the DB
    SendRecYdsPredictions(predRec)
    SendRushYdsPredictions(predRush)
    SendPassYdsPredictions(predPass)
    
    
    #Loading predictions back in
    predRec = LoadRecYdsPredictions()
    predRush = LoadRushYdsPredictions()
    predPass = LoadPassYdsPredictions()
    
    #Selecting my best bets for the week.
    Best = BestBets(predRec, predRush, predPass, modName, modName, modName, 0.05, 0.25, 20, week, year)
    
    #Sending best bets to the database
    SendBestBets(Best)
    
    
    
Modelling(1, 2026, "Ridge", "Ridge_1.0")