# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 23:21:17 2026

@author: Austin
"""

import NFLqueries
import NFLmodelling
import NFLscraper
import pandas as pd


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