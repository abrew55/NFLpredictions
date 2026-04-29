# -*- coding: utf-8 -*-
"""
Created on Sun Jan 12 11:19:41 2025

@author: Austin
"""
import numpy as np
from numpy import arange
import pandas as pd
import statsmodels.api as sm
from sklearn.feature_selection import RFE
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import random
import NFLqueries
import pymysql 



#This function will prep the data for the model. It combines the players career stats with the team they will be facing.
def predPrep(data, defenseData, schedule, EspnIDs, week, year, method):
    defenseData = defenseData[(defenseData["Week"] == week-1) & (defenseData["Year"] == year)]
    
    schedule = schedule[schedule["Week"] == week]
    schedule.reset_index(drop=True, inplace=True)
    
    data = pd.merge(data, EspnIDs, how="left", on="EspnID")
    data = data.drop(["Name", "Team_x", "EspnID", "Position"], axis=1)
       
    #data = data[data["Week"] == data["Week"].max()]      
    #data = data.loc[data.groupby('EspnID')['Week'].idxmax()] #Pulling data from player's most recent week
   
    #Need to remove old defense data before adding new.
    if(method == "Rec" or method == "Pass"):
        data = data.drop(["DADOT", "Blitz%", "Hrry%", "QBKD%", "Prss%", "Cmp%", "TD%", "Int%", "Y/A", "AY/A", "Y/C", "Y/G", "Rate", "Sk%", "NY/A", "ANY/A", "EXP"], axis=1)
    if(method == "Rush"):
        data = data.drop(["ATT", "YDS", "TD", "Y/A", "Y/G", "EXP"], axis=1)
    
    data.reset_index(drop=True, inplace=True)
    
    #The following will switch the team's oppenent from last week's to this upcoming week's
    for x in range(0,len(data)):
        for y in range(0,len(schedule)):
            if(data.loc[x,"Team_y"] == schedule.loc[y,"Home Team"]):
                data.loc[x,"Opp"] = schedule.loc[y,"Away Team"]
            if(data.loc[x,"Team_y"] == schedule.loc[y,"Away Team"]):
                data.loc[x,"Opp"] = schedule.loc[y,"Home Team"] 
    


    data = pd.merge(data, defenseData, how='left', on='Opp')
    data = data.drop(["Team_y", "Opp", "Year_y", "Week_y"], axis=1)
    data = data.rename(columns={'Week_x': 'Week', 'Year_x': 'Year'})
    
    return data

#This function will make predictions for every player within the dataset
def modPred(model, cols, data):
    full = cols.copy()
    full.append('Name')
    data = data.loc[:,full]
    results = [['Player', 'Predicted Yards']]
    for x in range(0, len(data)):
        temp = []
        temp.append(data.loc[x,'Name'])
        X_predict = pd.DataFrame(columns = cols)
        X_predict.loc[-1] = data.loc[x,cols]
        print(X_predict)
        y_predict = model.predict(X_predict)
        temp.append(y_predict[0])
        results.append(temp)
        
    return results

def modEvalRec(modResults, NFLdata, bettingLines, week, year):
    
    #modResults = pd.DataFrame(modResults, columns=["Player", "Predicted Yards"])
    #modResults.columns = modResults.iloc[0]
    #modResults = modResults[1:].reset_index(drop=True)
    #print(modResults)
    
    actResults = NFLdata[(NFLdata["Week"] == week) & (NFLdata["Year"] == year)]
    actResults = actResults.loc[:,["Name", "EspnID", "Rec YDS"]]

    playerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RecPlayerIDwithTeam.csv')

    actResults = pd.merge(actResults, playerIDs, on="Name")
    actResults = actResults.drop("EspnID", axis=1)

    finalResults = pd.merge(modResults, actResults, left_on="Player", right_on="Name")

    bettingLines["ID"] = pd.to_numeric(bettingLines["ID"])
    bettingLines = bettingLines[(bettingLines["Week"] == week) & (bettingLines["Year"] == year)]

    finalResults = pd.merge(finalResults, bettingLines, on="ID")
    finalResults = finalResults.drop(["Name", "Player_y", "Position", "Team_y"], axis=1)

    finalResults["Predicted Yards"] = pd.to_numeric(finalResults["Predicted Yards"])

    finalResults = lineToNumeric(finalResults)
    finalResults["Over"] = pd.to_numeric(finalResults["Over"])
    finalResults["Under"] = pd.to_numeric(finalResults["Under"])

    resultsTable = []
    for x in range(0, len(finalResults)):
        temp = []
        temp.append(finalResults.loc[x, "Player_x"])
        if(finalResults.loc[x, "Predicted Yards"] > finalResults.loc[x, "Over"]):
            
            temp.append(finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Over"])
            if(finalResults.loc[x, "Rec YDS"] > finalResults.loc[x, "Over"]):
                temp.append("Success")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rec YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rec YDS"]))
                
            if(finalResults.loc[x, "Rec YDS"] < finalResults.loc[x, "Over"]):
                temp.append("Failure")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rec YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rec YDS"]))
                
                
        if(finalResults.loc[x, "Predicted Yards"] < finalResults.loc[x, "Over"]):
            
            temp.append(finalResults.loc[x, "Over"] - finalResults.loc[x, "Predicted Yards"])
            if(finalResults.loc[x, "Rec YDS"] > finalResults.loc[x, "Over"]):
                temp.append("Failure")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rec YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rec YDS"]))
                
            if(finalResults.loc[x, "Rec YDS"] < finalResults.loc[x, "Over"]):
                temp.append("Success")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rec YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rec YDS"]))
                
        resultsTable.append(temp)
                
        
    resultsTable = pd.DataFrame(resultsTable, columns=["Player", "Confidence", "Result", "Model Difference", "SportsBook Difference"])

    resultsTable = resultsTable.drop_duplicates()

    resultsTable["Result"].value_counts()
    
    return resultsTable


def modEvalRush(modResults, NFLdata, bettingLines, week, year):
    
    modResults = pd.DataFrame(modResults, columns=["Player", "Predicted Yards"])
    #modResults.columns = modResults.iloc[0]
    #modResults = modResults[1:].reset_index(drop=True)
    #print(modResults)
    
    actResults = NFLdata[(NFLdata["Week"] == week) & (NFLdata["Year"] == year)]
    actResults = actResults.loc[:,["Name", "EspnID", "Rush YDS"]]

    playerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RushPlayerIDwithTeam.csv')

    actResults = pd.merge(actResults, playerIDs, on="Name")
    actResults = actResults.drop("EspnID", axis=1)

    finalResults = pd.merge(modResults, actResults, left_on="Player", right_on="Name")
  

    bettingLines["ID"] = pd.to_numeric(bettingLines["ID"])
    bettingLines = bettingLines[(bettingLines["Week"] == week) & (bettingLines["Year"] == year)]

    finalResults = pd.merge(finalResults, bettingLines, on="ID")
    finalResults = finalResults.drop(["Name", "Player_y", "Position", "Team_y"], axis=1)

    finalResults["Predicted Yards"] = pd.to_numeric(finalResults["Predicted Yards"])

    finalResults = lineToNumeric(finalResults)
    finalResults["Over"] = pd.to_numeric(finalResults["Over"])
    finalResults["Under"] = pd.to_numeric(finalResults["Under"])
    

    resultsTable = []
    for x in range(0, len(finalResults)):
        temp = []
        temp.append(finalResults.loc[x, "Player_x"])
        if(finalResults.loc[x, "Predicted Yards"] > finalResults.loc[x, "Over"]):
            
            temp.append(finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Over"])
            if(finalResults.loc[x, "Rush YDS"] > finalResults.loc[x, "Over"]):
                temp.append("Success")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rush YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rush YDS"]))
                
            if(finalResults.loc[x, "Rush YDS"] < finalResults.loc[x, "Over"]):
                temp.append("Failure")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rush YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rush YDS"]))
                
                
        if(finalResults.loc[x, "Predicted Yards"] < finalResults.loc[x, "Over"]):
            
            temp.append(finalResults.loc[x, "Over"] - finalResults.loc[x, "Predicted Yards"])
            if(finalResults.loc[x, "Rush YDS"] > finalResults.loc[x, "Over"]):
                temp.append("Failure")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rush YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rush YDS"]))
                
            if(finalResults.loc[x, "Rush YDS"] < finalResults.loc[x, "Over"]):
                temp.append("Success")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Rush YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Rush YDS"]))
                
        resultsTable.append(temp)
                
        
    resultsTable = pd.DataFrame(resultsTable, columns=["Player", "Confidence", "Result", "Model Difference", "SportsBook Difference"])

    resultsTable = resultsTable.drop_duplicates()

    resultsTable["Result"].value_counts()
    
    return resultsTable

def modEvalPass(modResults, NFLdata, bettingLines, week, year):
    
    modResults = pd.DataFrame(modResults, columns=["Player", "Predicted Yards"])
    #modResults.columns = modResults.iloc[0]
    #modResults = modResults[1:].reset_index(drop=True)
    #print(modResults)
    
    actResults = NFLdata[(NFLdata["Week"] == week) & (NFLdata["Year"] == year)]
    actResults = actResults.loc[:,["Name", "EspnID", "Pass YDS"]]

    playerIDs = pd.read_csv('D:/Data Science Stuff/Betting Project 3/PassPlayerIDwithTeam.csv')

    actResults = pd.merge(actResults, playerIDs, on="Name")
    actResults = actResults.drop("EspnID", axis=1)

    finalResults = pd.merge(modResults, actResults, left_on="Player", right_on="Name")

    bettingLines["ID"] = pd.to_numeric(bettingLines["ID"])
    bettingLines = bettingLines[(bettingLines["Week"] == week) & (bettingLines["Year"] == year)]

    finalResults = pd.merge(finalResults, bettingLines, on="ID")
    finalResults = finalResults.drop(["Name", "Player_y", "Position", "Team_y"], axis=1)

    finalResults["Predicted Yards"] = pd.to_numeric(finalResults["Predicted Yards"])

    finalResults = lineToNumeric(finalResults)
    finalResults["Over"] = pd.to_numeric(finalResults["Over"])
    finalResults["Under"] = pd.to_numeric(finalResults["Under"])

    resultsTable = []
    for x in range(0, len(finalResults)):
        temp = []
        temp.append(finalResults.loc[x, "Player_x"])
        if(finalResults.loc[x, "Predicted Yards"] > finalResults.loc[x, "Over"]):
            
            temp.append(finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Over"])
            if(finalResults.loc[x, "Pass YDS"] > finalResults.loc[x, "Over"]):
                temp.append("Success")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Pass YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Pass YDS"]))
                
            if(finalResults.loc[x, "Pass YDS"] < finalResults.loc[x, "Over"]):
                temp.append("Failure")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Pass YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Pass YDS"]))
                
                
        if(finalResults.loc[x, "Predicted Yards"] < finalResults.loc[x, "Over"]):
            
            temp.append(finalResults.loc[x, "Over"] - finalResults.loc[x, "Predicted Yards"])
            if(finalResults.loc[x, "Pass YDS"] > finalResults.loc[x, "Over"]):
                temp.append("Failure")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Pass YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Pass YDS"]))
                
            if(finalResults.loc[x, "Pass YDS"] < finalResults.loc[x, "Over"]):
                temp.append("Success")
                temp.append((finalResults.loc[x, "Predicted Yards"] - finalResults.loc[x, "Pass YDS"]))
                temp.append((finalResults.loc[x, "Over"] - finalResults.loc[x, "Pass YDS"]))
                
        resultsTable.append(temp)
                
        
    resultsTable = pd.DataFrame(resultsTable, columns=["Player", "Confidence", "Result", "Model Difference", "SportsBook Difference"])

    resultsTable = resultsTable.drop_duplicates()

    resultsTable["Result"].value_counts()
    
    return resultsTable


def lineToNumeric(lineData):
    for x in range(0, len(lineData)):
        tempOver = str(lineData.loc[x, "Over"])
        tempUnder = str(lineData.loc[x, "Under"])
        
        numOver = ""
        numUnder = ""
        
        for y in range(0, len(tempOver)):
            if(tempOver[y].isnumeric()):
                if(tempOver[y] == "½"):
                    numOver = numOver + ".5"
                else:
                    numOver = numOver + tempOver[y]
                
        for y in range(0, len(tempUnder)):
            if(tempUnder[y].isnumeric()):
                if(tempUnder[y] == "½"):
                    numUnder = numUnder + ".5"
                else:
                    numUnder = numUnder + tempUnder[y]
                
                
        
        lineData.loc[x, "Over"] = numOver
        lineData.loc[x, "Under"] = numUnder
    
    return lineData



def modelPrepTesting(data, weekStart, weekEnd, method):
    data = data[data['Week'] != 1]
    #If modelling receiving data
    if(method == "Rec"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for the current week.
        TrainingData = data[(data["Week"] != weekEnd)]
        for x in range(0,weekEnd-weekStart+1):
            TrainingData = TrainingData[(TrainingData["Week"] != weekStart+x+1)]
        TestingData = data[(data["Week"] <= weekStart)]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Rec YDS", "Rec TD", "Name", "EspnID", "Year_x", "REC", "TGTS", "Yds per Rec", "Rec LNG", "CAR", "Rush YDS", "Rush AVG", "Rush LNG", "Rush TD", "FUM", "LST", "Year_y"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Rec YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Rec YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
    #If modelling rushing data
    if(method == "Rush"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for the current week.
        TrainingData = data[(data["Week"] != weekEnd)]
        for x in range(0,weekEnd-weekStart+1):
            TrainingData = TrainingData[(TrainingData["Week"] != weekStart+x+1)]
        TestingData = data[(data["Week"] <= weekStart)]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Name", "EspnID", "Car", "Rush YDS", "Rush AVG", "Rush TD", "Rush LNG", "Rec", "TGTS", "Rec YDS", "Rec AVG", "Rec TD", "Rec LNG", "Fum", "LST", "Year_x", "Year_y"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Rush YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Rush YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
       
    #If modelling passing data
    if(method == "Pass"):
        #Training data will consist of all data up to this point. Testing data will only contain data for the current week.
        TrainingData = data[(data["Week"] != weekEnd)]
        for x in range(0,weekEnd-weekStart+1):
            TrainingData = TrainingData[(TrainingData["Week"] != weekStart+x+1)]
        TestingData = data[(data["Week"] <= weekStart)]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Name", "EspnID", "CMP", "ATT", "Pass YDS", "CMP%", "YDS per CMP", "TDS", "INT", "Pass LNG", "Sacks", "RTG", "QBR", "Car", "Rush YDS", "YDS per Rush", "Rush TDS", "Rush LNG", "Year_x", "Year_y"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Pass YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Pass YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
    return yTrain,xTrain,yTest,xTest,TrainingData,TestingData

def CreateTestSortCol(data):
    data['temp'] = 0
    for x in range(0, len(data)):
        temp = data.loc[x, 'Week']
        if(temp < 10):
            temp = str(temp)
            temp = '0' + temp
        else:
            temp = str(temp)
        
        data.loc[x, 'temp'] = str(data.loc[x, 'Year']) + temp
        
    data['temp'] = data['temp'].astype(int)
    
    return data
        
#This function will prepare data for the model each week. Need to test.
def modelPrep(data, week, year, method):
    #If modelling receiving data
    if(method == "Rec"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for each player's most recent game.
        #TrainingData = data[(data["Week"] != week) & (data["Year"] != year)]
        TrainingData = data.copy()
        TestingData = data.copy()
        TestingData = CreateTestSortCol(TestingData)
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['temp'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Rec YDS", "Rec TD", "Name", "REC", "TGTS", "Yds per Rec", "Rec LNG", "CAR", "Rush YDS", "Rush AVG", "Rush LNG", "Rush TD", "FUM", "LST"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Rec YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp", "EspnID"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Rec YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        xTest = xTest.drop('temp', axis=1)
        
    #If modelling rushing data
    if(method == "Rush"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for each player's most recent game.
        #TrainingData = data[(data["Week"] != week) & (data["Year"] != year)]
        TrainingData = data.copy()
        TestingData = data.copy()
        TestingData = CreateTestSortCol(TestingData)
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['temp'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Name", "Car", "Rush YDS", "Rush AVG", "Rush TD", "Rush LNG", "Rec", "TGTS", "Rec YDS", "Rec AVG", "Rec TD", "Rec LNG", "Fum", "LST"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Rush YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp", "EspnID"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Rush YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        xTest = xTest.drop('temp', axis=1)
        
       
    #If modelling passing data
    if(method == "Pass"):
        #Training data will consist of all data up to this point. Testing data will only contain data for each player's most recent game.
        #TrainingData = data[(data["Week"] != week) & (data["Year"] != year)]
        TrainingData = data.copy()
        TestingData = data.copy()
        TestingData = CreateTestSortCol(TestingData)
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['temp'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Name", "CMP", "ATT", "Pass YDS", "CMP%", "YDS per CMP", "TDS", "INT", "Pass LNG", "Sacks", "RTG", "QBR", "Car", "Rush YDS", "YDS per Rush", "Rush TDS", "Rush LNG"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Pass YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp", "EspnID"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Pass YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        xTest = xTest.drop('temp', axis=1)
        
    return yTrain,xTrain,yTest,xTest,TrainingData,TestingData

def BuildModel(yTrain, xTrain, yTest, xTest, TrainingData, TestingData, method, modelType, week, name) :
    #results = TestingData["Name"]
    if(modelType == "RF"):
        model = RandomForestRegressor(n_estimators=100, random_state=0, oob_score=True)
        model.fit(xTrain,yTrain)

        print(model.oob_score_)

        y_pred = model.predict(xTest)
    
    if(modelType == "Ridge"):

        scaler = StandardScaler()
        xTrain = scaler.fit_transform(xTrain)
        xTest = scaler.transform(xTest)

        ridge_cv = RidgeCV(alphas=arange(0.1, 10, 0.1), scoring='neg_mean_absolute_error')  
        ridge_cv.fit(xTrain, yTrain)
        
        print(ridge_cv.alpha_)

        y_pred = ridge_cv.predict(xTest)
        print("Model score (R^2):", r2_score(yTest, y_pred))
    
    results = TestingData["Name"].reset_index()
    results = results.drop("index", axis=1)
    results["Predicted Yards"] = y_pred
    results.columns = ["Player", "Predicted Yards"]
    #Adding two more helpful columns (current week and type of model)
    results["Week"] = week
    results["Model"] = name
    
    #Inserting a final column for EspnID
    resultsTemp = TestingData["EspnID"].reset_index()
    resultsTemp = resultsTemp.drop("index", axis=1)
    results["EspnID"] = resultsTemp["EspnID"]
    
    return results


#modResults = modPred(model, Xcols, testData)
def ProcessBettingLines(data):
    for x in range(0,len(data)):
        #Necessary filtering for the Overs
        tempOver = data.loc[x,'Over']
        tempOver = tempOver[1:-1]
        data.loc[x,'Over'] = tempOver
        
        #Necessary filtering for the Unders
        tempUnder = data.loc[x,'Under']
        tempUnder = tempUnder[1:-1]
        data.loc[x,'Under'] = tempUnder
        
        #Necessary filtering for the Over Payouts
        tempOverPayout = data.loc[x,'Over Payout']
        tempOverPayout = tempOverPayout[1:-1]
        data.loc[x,'Over Payout'] = tempOverPayout
        
        #Necessary filtering for the Under Payouts
        tempUnderPayout = data.loc[x,'Under Payout']
        tempUnderPayout = tempUnderPayout[1:-1]
        data.loc[x,'Under Payout'] = tempUnderPayout
        
    data['Over'] = pd.to_numeric(data['Over'])
    data['Under'] = pd.to_numeric(data['Under'])
    data['Over Payout'] = pd.to_numeric(data['Over Payout'])
    data['Under Payout'] = pd.to_numeric(data['Under Payout'])

    for x in range(0,len(data)):
        #If plus odds
        if(data.loc[x,'Over Payout'] > 0):
            data.loc[x,'Over Payout'] = (data.loc[x,'Over Payout']+100)/100
        
        #If minus odds
        if(data.loc[x,'Over Payout'] < 0):
             data.loc[x,'Over Payout'] = (100/abs(data.loc[x,'Over Payout']))+1
       
        #If plus odds
        if(data.loc[x,'Under Payout'] > 0):
            data.loc[x,'Under Payout'] = (data.loc[x,'Under Payout']+100)/100
             
        #If minus odds   
        if(data.loc[x,'Under Payout'] < 0):
            data.loc[x,'Under Payout'] = (100/abs(data.loc[x,'Under Payout']))+1
        
    
    return data
        

#Uses payouts to find the best overall bets for the coming week. Week variable is upcoming week, not most recent week.
def Predictions(results, bettingData, playerIDs, method, week, year, model):
    results = results.drop("Year", axis=1)
    results = pd.merge(results, playerIDs, left_on="EspnID", right_on="EspnID", how="inner")
    results = results.drop(["Name", "Position","Week","Model"], axis=1)
    if(method == "Rec"):
        #Calling betting data and filtering to this upcoming week
        bettingData = bettingData[(bettingData["Week"] == week) & (bettingData["Year"] == year)]
        
        #Merging betting lines with predictions
        data = pd.merge(bettingData, results, left_on="ID", right_on="EspnID", how="inner")
        data = data.drop(["Player_x", "Year_x", "Year_y"], axis=1)
        
        #Running the dataset through a function that will prepare it for use
        data = ProcessBettingLines(data)
        
    if(method == "Rush"):
        #Calling betting data and filtering to this upcoming week
        bettingData = bettingData[(bettingData["Week"] == week) & (bettingData["Year"] == year)]
        
        #Merging betting lines with predictions
        data = pd.merge(bettingData, results, left_on="ID", right_on="EspnID", how="inner")
        data = data.drop(["Player_x", "Year_x", "Year_y"], axis=1)
        
        #Running the dataset through a function that will prepare it for use
        data = ProcessBettingLines(data)
        
    if(method == "Pass"):
        #Calling betting data and filtering to this upcoming week
        bettingData = bettingData[(bettingData["Week"] == week) & (bettingData["Year"] == year)]
        
        #Merging betting lines with predictions
        data = pd.merge(bettingData, results, left_on="ID", right_on="EspnID", how="inner")
        data = data.drop(["Player_x", "Year_x", "Year_y"], axis=1) 
        
        #Running the dataset through a function that will prepare it for use
        data = ProcessBettingLines(data)
        
    data["Expected Under Payout"] = (abs(data["Predicted Yards"] - data["Under"])/100)*data["Under Payout"]
    data["Expected Over Payout"] = (abs(data["Predicted Yards"] - data["Over"])/100)*data["Over Payout"]
    data["Year"] = year
    data["Model"] = model
    data = data.drop(["Team_y", "Position", "EspnID"], axis=1)
    data = data.dropna()
    return data


def WeeklyResults(finalResults, week, year, model):
    failure, success = 0, 0
    finalResults.reset_index(drop=True, inplace=True)
    for x in range(0,len(finalResults)):
        if(finalResults.loc[x,"Result"] == "Success"):
            success += 1
        else:
            failure += 1
    print(finalResults["Result"].value_counts())
    winPerc = success/(success+failure)
    modelAve = finalResults.loc[:,"Model Difference"].abs().mean()
    sbAve = finalResults.loc[:,"SportsBook Difference"].abs().mean()
    final = [winPerc,modelAve,sbAve,week, model, year]
    return final       
    
def get_stats():
    results = sm.OLS(y, x).fit()
    print(results.summary())


### Select best bets ###

def BestBets(RecPreds, RushPreds, PassPreds, RecModel, RushModel, PassModel, ExpLow, ExpHigh, bets, week, year):
    #Filtering down by expected payout value, week, year, and model. Pass yard predictions under 200 yards are unreliable, so I'm trimming those out. 
    BestRec = RecPreds[(RecPreds["Expected Over Payout"] > ExpLow) & (RecPreds["Expected Over Payout"] < ExpHigh) & (RecPreds["Week"] == week) & (RecPreds["Year"] == year) & (RecPreds["Model"] == RecModel)]
    BestRec["Stat"] = "Rec"
    BestRush = RushPreds[(RushPreds["Expected Over Payout"] > ExpLow) & (RushPreds["Expected Over Payout"] < ExpHigh) & (RushPreds["Week"] == week) & (RushPreds["Year"] == year) & (RushPreds["Model"] == RushModel)]
    BestRush["Stat"] = "Rush"
    BestPass = PassPreds[(PassPreds["Predicted Yards"] > 200) & (PassPreds["Expected Over Payout"] > ExpLow) & (PassPreds["Expected Over Payout"] < ExpHigh) & (PassPreds["Week"] == week) & (PassPreds["Year"] == year) & (PassPreds["Model"] == PassModel)]
    BestPass["Stat"] = "Pass"
    
    #Stacking the 3 filtered datasets as they have the same columns
    BestBets = pd.concat([BestRec, BestRush, BestPass], ignore_index=True)
    
    
    #Generating a random value vector according to the number of desired bets. It's very possible I want more bets than can be provided, so the try except statement addresses that. 
    try:
        randomVector = random.sample(range(0,len(BestBets)), bets)
    
    except:
        print("Length of desired vector exceeds population size")
    
    #Taking a random sample of the best bets. 
    BestBets = BestBets.loc[randomVector, :]
    
    BestBets = BestBets.reset_index(drop=True)
    
    return BestBets

###### AFTER GAMES ARE COMPLETE #####


def BestResults(week, year, BestBets, RecGameLogs, RushGameLogs, PassGameLogs):
    #Load in the predictions
    
    BestBets = BestBets[(BestBets["Week"] == week) & (BestBets["Year"] == year)]
    #Load in the stats
    RecGameLogs["Stat"] = "Rec"
    
    RushGameLogs["Stat"] = "Rush"
    
    PassGameLogs["Stat"] = "Pass"
    
    #Prepare the final results column
    BestBets["Result"] = 0
    
    #Split the rows according to stat type.
    BBRec = BestBets[BestBets["Stat"] == "Rec"]
    BBRush = BestBets[BestBets["Stat"] == "Rush"]
    BBPass = BestBets[BestBets["Stat"] == "Pass"]

    #Merging the split best bets with the game logs
    BBRec = pd.merge(BBRec, RecGameLogs, how="left", left_on=["Week", "ID", "Year", "Stat"], right_on=["Week", "EspnID", "Year", "Stat"])
    BBRec = BBRec.dropna()
    
    BBRush = pd.merge(BBRush, RushGameLogs, how="left", left_on=["Week", "ID", "Year", "Stat"], right_on=["Week", "EspnID", "Year", "Stat"])
    BBRush = BBRush.dropna()
    
    BBPass = pd.merge(BBPass, PassGameLogs, how="left", left_on=["Week", "ID", "Year", "Stat"], right_on=["Week", "EspnID", "Year", "Stat"])
    BBPass = BBPass.dropna()
    
    #Cleaning up the merged data.
    BBRec = BBRec.iloc[:, 0:22]
    BBRec = BBRec.drop(BBRec.columns[[15,16,17,18,19,20]], axis=1)
    BBRec = BBRec.rename({"Rec YDS": "Actual Yards"}, axis=1)
    
    BBRush = BBRush.iloc[:, 0:21]
    BBRush = BBRush.drop(BBRush.columns[[15,16,17,18,19]], axis=1)
    BBRush = BBRush.rename({"Rush YDS": "Actual Yards"}, axis=1)
    
    BBPass = BBPass.iloc[:, 0:22]
    BBPass = BBPass.drop(BBPass.columns[[15,16,17,18,19,20]], axis=1)
    BBPass = BBPass.rename({"Pass YDS": "Actual Yards"}, axis=1)

    BestBets = pd.concat([BBRec, BBRush, BBPass], ignore_index=True)    
    
    
    for x in range(0,len(BestBets)):
        if(BestBets.loc[x,"Stat"] == "Rec"):
            if(BestBets.loc[x,"Predicted Yards"] > BestBets.loc[x,"Over"]):
                #If the actual yards are greater than the over, then the bet is a success.
                if(BestBets.loc[x,"Actual Yards"] >= BestBets.loc[x,"Over"]):
                    BestBets.loc[x,"Result"] = "Success"
                else:
                    BestBets.loc[x,"Result"] = "Failure"
                
            #If our prediction is less than the over line. This means we would bet below the over. 
            if(BestBets.loc[x,"Predicted Yards"] < BestBets.loc[x,"Over"]):
                #If the actual yards are greater than the over, then the bet is a success.
                if(BestBets.loc[x,"Actual Yards"] <= BestBets.loc[x,"Over"]):
                    BestBets.loc[x,"Result"] = "Success"
                else:
                    BestBets.loc[x,"Result"] = "Failure"      
                    
                    
        if(BestBets.loc[x,"Stat"] == "Rush"):    
            #If our prediction is greater than the over line. This means we would bet above the over. 
            if(BestBets.loc[x,"Predicted Yards"] > BestBets.loc[x,"Over"]):
                #If the actual yards are greater than the over, then the bet is a success.
                if(BestBets.loc[x,"Actual Yards"] >= BestBets.loc[x,"Over"]):
                    BestBets.loc[x,"Result"] = "Success"
                else:
                    BestBets.loc[x,"Result"] = "Failure"
                    
            #If our prediction is less than the over line. This means we would bet below the over. 
            if(BestBets.loc[x,"Predicted Yards"] < BestBets.loc[x,"Over"]):
                #If the actual yards are greater than the over, then the bet is a success.
                if(BestBets.loc[x,"Actual Yards"] <= BestBets.loc[x,"Over"]):
                    BestBets.loc[x,"Result"] = "Success"
                else:
                    BestBets.loc[x,"Result"] = "Failure"
                    
                    
        if(BestBets.loc[x,"Stat"] == "Pass"):
            #If our prediction is greater than the over line. This means we would bet above the over. 
            if(BestBets.loc[x,"Predicted Yards"] > BestBets.loc[x,"Over"]):
                #If the actual yards are greater than the over, then the bet is a success.
                if(BestBets.loc[x,"Actual Yards"] >= BestBets.loc[x,"Over"]):
                    BestBets.loc[x,"Result"] = "Success"
                else:
                    BestBets.loc[x,"Result"] = "Failure"
            
            #If our prediction is less than the over line. This means we would bet below the over. 
            if(BestBets.loc[x,"Predicted Yards"] < BestBets.loc[x,"Over"]):
                #If the actual yards are greater than the over, then the bet is a success.
                if(BestBets.loc[x,"Actual Yards"] <= BestBets.loc[x,"Over"]):
                    BestBets.loc[x,"Result"] = "Success"
                else:
                    BestBets.loc[x,"Result"] = "Failure"
    
    return BestBets


def CareerResults(Preds, GameLogs, stat, method, model):
    
    if(stat == "Rec"):
        Preds["Result"] = 0
        Preds["Method"] = 0
        Preds = Preds[Preds["Model"] == model]
        Preds = pd.merge(Preds, GameLogs, left_on=["Week", "ID", "Year"], right_on=["Week", "EspnID", "Year"])
        
        
        #Parsing through each line to check the results of that individual bet.
        for x in range(0,len(Preds)):
            #We want to compare to overs
            if(method == "Over"):
                Preds["Method"] = "Over"
                #If our prediction is greater than the over line. This means we would bet above the over. 
                if(Preds.loc[x,"Predicted Yards"] > Preds.loc[x,"Over"]):
                    #If the actual yards are greater than the over, then the bet is a success.
                    if(Preds.loc[x,"Rec YDS"] >= Preds.loc[x,"Over"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                
                #If our prediction is less than the over line. This means we would bet below the over. 
                if(Preds.loc[x,"Predicted Yards"] < Preds.loc[x,"Over"]):
                    #If the actual yards are greater than the over, then the bet is a success.
                    if(Preds.loc[x,"Rec YDS"] <= Preds.loc[x,"Over"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
            
            #We want to compare to unders
            if(method == "Under"):
                Preds["Method"] = "Under"
                #If our prediction is greater than the under line. This means we would bet above the under. 
                if(Preds.loc[x,"Predicted Yards"] > Preds.loc[x,"Under"]):
                    #If the actual yards are greater than the under, then the bet is a success.
                    if(Preds.loc[x,"Rec YDS"] >= Preds.loc[x,"Under"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                
                #If our prediction is less than the under line. This means we would bet below the under. 
                if(Preds.loc[x,"Predicted Yards"] < Preds.loc[x,"Under"]):
                    #If the actual yards are greater than the under, then the bet is a success.
                    if(Preds.loc[x,"Rec YDS"] <= Preds.loc[x,"Under"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                        
        #I need to delete 5 columns before Rec Yds, and then I can drop everything else.
        Preds = Preds.drop(["Name", "Team_y", "EspnID", "REC", "TGTS"], axis=1)
        Preds = Preds.loc[:, :'Rec YDS']
        
        #Creating some columns which are helpful tools for analysis
        Preds["Pred Diff"] = (Preds["Rec YDS"] - Preds["Predicted Yards"])
        Preds["Absolute Pred Diff"] = abs(Preds["Rec YDS"] - Preds["Predicted Yards"])
        
        Preds["Sportsbook Diff"] = Preds["Over"] - Preds["Rec YDS"]
        Preds["Absolute Sportsbook Diff"] = abs(Preds["Over"] - Preds["Rec YDS"])


        return Preds
                        
                        
    if(stat == "Rush"):
        
        Preds["Result"] = 0
        Preds["Method"] = 0
        Preds = Preds[Preds["Model"] == model]
        Preds = pd.merge(Preds, GameLogs, left_on=["Week", "ID", "Year"], right_on=["Week", "EspnID", "Year"])
        
        
        #Parsing through each line to check the results of that individual bet.
        for x in range(0,len(Preds)):
            #We want to compare to overs
            if(method == "Over"):
                Preds["Method"] = "Over"
                #If our prediction is greater than the over line. This means we would bet above the over. 
                if(Preds.loc[x,"Predicted Yards"] > Preds.loc[x,"Over"]):
                    #If the actual yards are greater than the over, then the bet is a success.
                    if(Preds.loc[x,"Rush YDS"] >= Preds.loc[x,"Over"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                
                #If our prediction is less than the over line. This means we would bet below the over. 
                if(Preds.loc[x,"Predicted Yards"] < Preds.loc[x,"Over"]):
                    #If the actual yards are greater than the over, then the bet is a success.
                    if(Preds.loc[x,"Rush YDS"] <= Preds.loc[x,"Over"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
            
            #We want to compare to unders
            if(method == "Under"):
                Preds["Method"] = "Under"
                #If our prediction is greater than the under line. This means we would bet above the under. 
                if(Preds.loc[x,"Predicted Yards"] > Preds.loc[x,"Under"]):
                    #If the actual yards are greater than the under, then the bet is a success.
                    if(Preds.loc[x,"Rush YDS"] >= Preds.loc[x,"Under"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                
                #If our prediction is less than the under line. This means we would bet below the under. 
                if(Preds.loc[x,"Predicted Yards"] < Preds.loc[x,"Under"]):
                    #If the actual yards are greater than the under, then the bet is a success.
                    if(Preds.loc[x,"Rush YDS"] <= Preds.loc[x,"Under"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                        
        #I need to delete 5 columns before Rush Yds, and then I can drop everything else.
        Preds = Preds.drop(["Name", "Team_y", "EspnID", "Car"], axis=1)
        Preds = Preds.loc[:, :'Rush YDS']
        
        #Creating some columns which are helpful tools for analysis
        Preds["Pred Diff"] = (Preds["Rush YDS"] - Preds["Predicted Yards"])
        Preds["Absolute Pred Diff"] = abs(Preds["Rush YDS"] - Preds["Predicted Yards"])
        
        Preds["Sportsbook Diff"] = Preds["Over"] - Preds["Rush YDS"]
        Preds["Absolute Sportsbook Diff"] = abs(Preds["Over"] - Preds["Rush YDS"])
        
        return Preds
                        
    if(stat == "Pass"):

        Preds["Result"] = 0
        Preds["Method"] = 0
        Preds = Preds[Preds["Model"] == model]
        Preds = pd.merge(Preds, GameLogs, left_on=["Week", "ID", "Year"], right_on=["Week", "EspnID", "Year"])
        
        
        #Parsing through each line to check the results of that individual bet.
        for x in range(0,len(Preds)):
            #We want to compare to overs
            if(method == "Over"):
                Preds["Method"] = "Over"
                #If our prediction is greater than the over line. This means we would bet above the over. 
                if(Preds.loc[x,"Predicted Yards"] > Preds.loc[x,"Over"]):
                    #If the actual yards are greater than the over, then the bet is a success.
                    if(Preds.loc[x,"Pass YDS"] >= Preds.loc[x,"Over"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                
                #If our prediction is less than the over line. This means we would bet below the over. 
                if(Preds.loc[x,"Predicted Yards"] < Preds.loc[x,"Over"]):
                    #If the actual yards are greater than the over, then the bet is a success.
                    if(Preds.loc[x,"Pass YDS"] <= Preds.loc[x,"Over"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
            
            #We want to compare to unders
            if(method == "Under"):
                Preds["Method"] = "Under"
                #If our prediction is greater than the under line. This means we would bet above the under. 
                if(Preds.loc[x,"Predicted Yards"] > Preds.loc[x,"Under"]):
                    #If the actual yards are greater than the under, then the bet is a success.
                    if(Preds.loc[x,"Pass YDS"] >= Preds.loc[x,"Under"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                
                #If our prediction is less than the under line. This means we would bet below the under. 
                if(Preds.loc[x,"Predicted Yards"] < Preds.loc[x,"Under"]):
                    #If the actual yards are greater than the under, then the bet is a success.
                    if(Preds.loc[x,"Pass YDS"] <= Preds.loc[x,"Under"]):
                        Preds.loc[x,"Result"] = "Success"
                    else:
                        Preds.loc[x,"Result"] = "Failure"
                        
        #I need to delete 5 columns before Rec Yds, and then I can drop everything else.
        Preds = Preds.drop(["Name", "Team_y", "EspnID", "CMP", "ATT"], axis=1)
        Preds = Preds.loc[:, :'Pass YDS'] 


        #Creating some columns which are helpful tools for analysis
        Preds["Pred Diff"] = (Preds["Pass YDS"] - Preds["Predicted Yards"])
        Preds["Absolute Pred Diff"] = abs(Preds["Pass YDS"] - Preds["Predicted Yards"])
        
        Preds["Sportsbook Diff"] = Preds["Over"] - Preds["Pass YDS"]
        Preds["Absolute Sportsbook Diff"] = abs(Preds["Over"] - Preds["Pass YDS"])
              
        return Preds
    

def PlotCareer(data):
    fig = plt.figure(figsize=(12, 12))  
    ax = fig.add_subplot()  
    color = {'Success':'blue', 'Failure':'red'}
    ax.scatter(data.loc[:,"Week"], data.loc[:,"Predicted Yards"], c=data["Result"].map(color))    #Plotting the scatter plot points.    
    plt.legend(loc='upper right')
    title = "Results mapped against Predicted Yards per Week"
    plt.title(title)
    plt.show()
        



def CalcPayout(data, amount, week=None, year=None):
    payout = 0
    total = 0
    if( week != None and year != None ):
        data = data[(data["Week"]==week) & (data["Year"]==year)]
    data = data.reset_index()
    for x in range(0, len(data)):
        #Keeping track of how much I put in
        total += amount
        
        #Updating my running payout total
        payout += amount
        
        if(data.loc[x, "Result"] == "Success"):
            payout -= (amount*2)
            payout += (data.loc[x, "Over Payout"]) * amount
        else:
            payout -= (amount*2)
        
    percReturn = payout/total
    return [total,payout,percReturn]




















