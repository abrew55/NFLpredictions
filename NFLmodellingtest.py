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
import seaborn as sns
import matplotlib.pyplot as plt



#This function will prep the data for the model. It combines the players career stats with the team they will be facing.
def predPrep(data, defenseData, schedule, week, method):
    schedule = schedule[schedule["Week"] == week]
    schedule.reset_index(drop=True, inplace=True)
   
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
            if(data.loc[x,"Team"] == schedule.loc[y,"Home Team"]):
                data.loc[x,"Opp"] = schedule.loc[y,"Away Team"]
            if(data.loc[x,"Team"] == schedule.loc[y,"Away Team"]):
                data.loc[x,"Opp"] = schedule.loc[y,"Home Team"] 
    

        
    data = pd.merge(data, defenseData, how='left', on=['Opp','Week'])
    data = data.drop(["Team", "Opp", "Year_y"], axis=1)
    data.rename(columns={"Year_x": "Year"}, inplace=True)
    
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

def modEvalRec(modResults, NFLdata, week, year):
    
    modResults = modResults[(modResults["Week"] == week) & (modResults["Year"] == year)]
    modResults = modResults.drop(["Week", "Year"], axis=1)
    #modResults = modResults[1:].reset_index(drop=True)
    #print(modResults)
    
    actResults = NFLdata[NFLdata["Week"] == week]
    actResults = actResults.loc[:,["Name", "EspnID", "Rec YDS"]]

    finalResults = pd.merge(modResults, actResults, left_on="ID", right_on="EspnID")
    
    print(len(finalResults))
  
    bettingLines = LoadRecBettingLines()

    bettingLines["ID"] = pd.to_numeric(bettingLines["ID"])
    bettingLines = bettingLines[(bettingLines["Week"] == week) & (bettingLines["Year"] == year)]
    
    #print(bettingLines)
    #print(finalResults)
    
    finalResults = pd.merge(finalResults, bettingLines, left_on="EspnID", right_on="ID", how="inner")
    finalResults = finalResults.drop(["Name", "Player_y", "Position", "EspnID"], axis=1)
    

    finalResults["Predicted Yards"] = pd.to_numeric(finalResults["Predicted Yards"])

    finalResults = lineToNumeric(finalResults)
    finalResults["Over"] = pd.to_numeric(finalResults["Over"])
    finalResults["Under"] = pd.to_numeric(finalResults["Under"])

    resultsTable = []
    for x in range(0, len(finalResults)):
        temp = []
        temp.append(finalResults.loc[x, "Player_x"])
        temp.append(finalResults.loc[x, "Rec YDS"])
        temp.append(finalResults.loc[x, "Predicted Yards"])
        temp.append(finalResults.loc[x, "Over"])
        
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
                
        
    resultsTable = pd.DataFrame(resultsTable, columns=["Player", "Rec YDS", "Predicted Yards", "Over", "Confidence", "Result", "Model Difference", "SportsBook Difference"])

    resultsTable = resultsTable.drop_duplicates()

    resultsTable["Result"].value_counts()
    
    resultsTable["Week"] = week
    resultsTable["Year"] = year
    
    return resultsTable


def modEvalRush(modResults, NFLdata, week, year):
    
    modResults = modResults[(modResults["Week"] == week) & (modResults["Year"] == year)]
    modResults = modResults.drop(["Week", "Year"], axis=1)
    #modResults.columns = modResults.iloc[0]
    #modResults = modResults[1:].reset_index(drop=True)
    #print(modResults)
    
    actResults = NFLdata[NFLdata["Week"] == week]
    actResults = actResults.loc[:,["Name", "EspnID", "Rush YDS"]]

    finalResults = pd.merge(modResults, actResults, left_on="ID", right_on="EspnID")
  
    bettingLines = LoadRushBettingLines()

    bettingLines["ID"] = pd.to_numeric(bettingLines["ID"])
    bettingLines = bettingLines[(bettingLines["Week"] == week) & (bettingLines["Year"] == year)]

    finalResults = pd.merge(finalResults, bettingLines, left_on="EspnID", right_on="ID")
    finalResults = finalResults.drop(["Name", "Player_y", "Position", "EspnID"], axis=1)

    finalResults["Predicted Yards"] = pd.to_numeric(finalResults["Predicted Yards"])

    finalResults = lineToNumeric(finalResults)
    finalResults["Over"] = pd.to_numeric(finalResults["Over"])
    finalResults["Under"] = pd.to_numeric(finalResults["Under"])
    

    resultsTable = []
    for x in range(0, len(finalResults)):
        temp = []
        temp.append(finalResults.loc[x, "Player_x"])
        temp.append(finalResults.loc[x, "Rush YDS"])
        temp.append(finalResults.loc[x, "Predicted Yards"])
        temp.append(finalResults.loc[x, "Over"])
        
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
                
        
    resultsTable = pd.DataFrame(resultsTable, columns=["Player", "Rush YDS", "Predicted Yards", "Over", "Confidence", "Result", "Model Difference", "SportsBook Difference"])

    resultsTable = resultsTable.drop_duplicates()

    resultsTable["Result"].value_counts()
    
    resultsTable["Week"] = week
    resultsTable["Year"] = year
    
    return resultsTable

def modEvalPass(modResults, NFLdata, week, year):
    
    modResults = modResults[(modResults["Week"] == week) & (modResults["Year"] == year)]
    modResults = modResults.drop(["Week", "Year"], axis=1)
    #modResults.columns = modResults.iloc[0]
    #modResults = modResults[1:].reset_index(drop=True)
    #print(modResults)
    
    actResults = NFLdata[NFLdata["Week"] == week]
    actResults = actResults.loc[:,["Name", "EspnID", "Pass YDS"]]
    

    finalResults = pd.merge(modResults, actResults, left_on="ID", right_on="EspnID")
  
    bettingLines = LoadPassBettingLines()

    bettingLines["ID"] = pd.to_numeric(bettingLines["ID"])
    bettingLines = bettingLines[(bettingLines["Week"] == week) & (bettingLines["Year"] == year)]

    finalResults = pd.merge(finalResults, bettingLines, left_on="EspnID", right_on="ID")
    finalResults = finalResults.drop(["Name", "Player_y", "Position", "EspnID"], axis=1)

    finalResults["Predicted Yards"] = pd.to_numeric(finalResults["Predicted Yards"])

    finalResults = lineToNumeric(finalResults)
    finalResults["Over"] = pd.to_numeric(finalResults["Over"])
    finalResults["Under"] = pd.to_numeric(finalResults["Under"])

    resultsTable = []
    for x in range(0, len(finalResults)):
        temp = []
        temp.append(finalResults.loc[x, "Player_x"])
        temp.append(finalResults.loc[x, "Pass YDS"])
        temp.append(finalResults.loc[x, "Predicted Yards"])
        temp.append(finalResults.loc[x, "Over"])
        
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
                
        
    resultsTable = pd.DataFrame(resultsTable, columns=["Player", "Pass YDS", "Predicted Yards", "Over", "Confidence", "Result", "Model Difference", "SportsBook Difference"])

    resultsTable = resultsTable.drop_duplicates()

    resultsTable["Result"].value_counts()
    
    resultsTable["Week"] = week
    resultsTable["Year"] = year
    
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

#RecGameLogs = LoadRecGameLogs()
#RushGameLogs = LoadRushGameLogs()
#PassGameLogs = LoadPassGameLogs()

### Joining defensive stats ###

#Loading in the defensive passing statistics
#DefPassStats = LoadDefPassing()
#DefRushStats = LoadDefRushing()

#Filtering the data to just the year that I want
#DefPassStats24 = DefPassStats[DefPassStats['Year'] == 2024]
#DefRushStats24 = DefRushStats[DefRushStats['Year'] == 2024]

#DefStats24['EXP'] = DefStats24['EXP'].apply(pd.to_numeric)

#Performing a left-outer join to combine the game log data with the def passing stats data. NEED RUSH DEF STATS.
#NFLdataRec = pd.merge(RecGameLogs, DefPassStats24, on='Opp', how='left')
#NFLdataPass = pd.merge(PassGameLogs, DefPassStats24, on='Opp', how='left')
#NFLdataRush = pd.merge(RushGameLogs, DefRushStats24, on='Opp', how='left')

"""
#Plots and pearson correlations
NFLdataSumm = NFLdataRec
NFLdataSumm["Rec YDS"] = NFLdataRec["Rec YDS"].astype(str)
NFLdataRec["Rec YDS"] = NFLdataRec["Rec YDS"].apply(pd.to_numeric)
uniqueYDS = NFLdataSumm["Rec YDS"].unique()
uniqueYDS.sort()                                    #The describe() function sorts the string of yard values alphabetically. This will be used to get around that.
NFLdataHeaders = NFLdataSumm.keys()
for x in range(5,55):
    fig = plt.figure(figsize=(12, 12))  
    ax = fig.add_subplot()  
    ax.scatter(NFLdataRec.loc[:,"Rec YDS"], NFLdataRec.iloc[:,x])    #Plotting the scatter plot points.    
    summ = NFLdataSumm.groupby('Rec YDS')[NFLdataHeaders[x]].describe() 
    summ['Rec YDS'] = uniqueYDS
    summ['Rec YDS'] = summ['Rec YDS'].apply(pd.to_numeric)
    ax.scatter(summ.loc[:,'Rec YDS'], summ.loc[:,'mean'])
    plt.legend(loc='upper right')
    title = "Rec YDS vs " + NFLdataHeaders[x]
    plt.title(title)
    plt.show()

for x in range(5,55):    
    #Pearson's
    corr, _ = pearsonr(NFLdataRec.loc[:,"Rec YDS"], NFLdataRec.iloc[:,x])
    print('Pearsons correlation for', NFLdataHeaders[x],': %.3f' % corr,)

"""

def modelPrepTesting(data, weekStart, weekEnd, method):
    #If modelling receiving data
    if(method == "Rec"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for the current week.
        TrainingData = data[(data["Week"] != weekEnd)]
        for x in range(0,weekEnd-weekStart+1):
            TrainingData = TrainingData[(TrainingData["Week"] != weekStart+x+1)]
        TestingData = data[(data["Week"] <= weekStart)]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Rec YDS", "Rec TD", "Name", "EspnID", "REC", "TGTS", "Yds per Rec", "Rec LNG", "CAR", "Rush YDS", "Rush AVG", "Rush LNG", "Rush TD", "FUM", "LST"]
        
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
        xDrop = ["Name", "EspnID", "Car", "Rush YDS", "Rush AVG", "Rush TD", "Rush LNG", "Rec", "TGTS", "Rec YDS", "Rec AVG", "Rec TD", "Rec LNG", "Fum", "LST"]
        
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
        xDrop = ["Name", "EspnID", "CMP", "ATT", "Pass YDS", "CMP%", "YDS per CMP", "TDS", "INT", "Pass LNG", "Sacks", "RTG", "QBR", "Car", "Rush YDS", "YDS per Rush", "Rush TDS", "Rush LNG"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Pass YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        xTrain = xTrain.drop(["Team", "Opp"], axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Pass YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
    return yTrain,xTrain,yTest,xTest,TrainingData,TestingData

#This function will prepare data for the model each week. Need to test.
def modelPrep(data, week, year, method):
    #If modelling receiving data
    if(method == "Rec"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for each player's most recent game.
        TrainingData = data[(data["Week"] != week) & (data["Year"] != year)]
        TestingData = data[data["Year"] == year]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Rec YDS", "Rec TD", "Name", "Team", "Opp", "EspnID", "Year_x", "REC", "TGTS", "Yds per Rec", "Rec LNG", "CAR", "Rush YDS", "Rush AVG", "Rush LNG", "Rush TD", "FUM", "LST", "Year_y"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Rec YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Rec YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
    #If modelling rushing data
    if(method == "Rush"):
        
        #Training data will consist of all data up to this point. Testing data will only contain data for each player's most recent game.
        TrainingData = data[(data["Week"] != week) & (data["Year"] != year)]
        TestingData = data[data["Year"] == year]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Name", "Team", "Opp", "EspnID", "Car", "Rush YDS", "Rush AVG", "Rush TD", "Rush LNG", "Rec", "TGTS", "Rec YDS", "Rec AVG", "Rec TD", "Rec LNG", "Fum", "LST", "Year_x", "Year_y"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Rush YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Rush YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
       
    #If modelling passing data
    if(method == "Pass"):
        #Training data will consist of all data up to this point. Testing data will only contain data for each player's most recent game.
        TrainingData = data[(data["Week"] != week) & (data["Year"] != year)]
        TestingData = data[data["Year"] == year]
        TestingData = TestingData.loc[TestingData.groupby('EspnID')['Week'].idxmax()]
        
        #Removing irrelevant variables
        xDrop = ["Name", "Team", "Opp", "EspnID", "CMP", "ATT", "Pass YDS", "CMP%", "YDS per CMP", "TDS", "INT", "Pass LNG", "Sacks", "RTG", "QBR", "Car", "Rush YDS", "YDS per Rush", "Rush TDS", "Rush LNG", "Year_x", "Year_y"]
        
        #Creating the training sets for x and y
        yTrain = TrainingData["Pass YDS"]
        xTrain = TrainingData.drop(xDrop, axis=1)
        
        #Creating the testing sets for x and y
        yTest = TestingData["Pass YDS"]
        xTest = TestingData.drop(xDrop, axis=1)
        
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
        
    if(modelType == "Linear"):
        
        model = LinearRegression()
        model.fit(xTrain,yTrain)
        
        y_pred = model.predict(xTest)
        
    if(modelType == "StepLinear"):
        
        #Fitting a stepwise linear regressor
        reg = LinearRegression()
        stepModel = RFE(reg) #n_features_to_select=5
        stepModel = stepModel.fit(xTrain,yTrain)
        #test = x.columns[stepModel.support_]

        #Building the model with the features according to the stepwise process
        #xTest = xTest.drop(["Opp", "Team"], axis=1)
        y_pred = stepModel.predict(xTest)
    
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
    results = pd.merge(results, playerIDs, left_on="EspnID", right_on="EspnID", how="inner")
    results = results.drop(["Name", "Position","Week","Model"], axis=1)
    if(method == "Rec"):
        #Calling betting data and filtering to this upcoming week
        bettingData = bettingData[(bettingData["Week"] == week) & (bettingData["Year"] == year)]
        
        #Merging betting lines with predictions
        data = pd.merge(bettingData, results, left_on="ID", right_on="EspnID", how="inner")
        print(data)
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


#######
"""
#Fitting a stepwise linear regressor
reg = LinearRegression()
stepModel = RFE(reg) #n_features_to_select=5
stepModel = stepModel.fit(x,y)
print(x.columns[stepModel.support_])
#test = x.columns[stepModel.support_]

#Building the model with the features according to the stepwise process
Xcols = ['Career LST', 'Yards/G', 'TDS/G', 'TGTS/G', 'L5REC/G', 'Hrry%', 'QBKD%', 'Prss%', 'Cmp%', 'TD%', 'Int%', 'Y/A', 'AY/A', 'Y/C', 'Rate', 'Sk%', 'NY/A', 'ANY/A']
X = NFLtrainingData[Xcols]
model = LinearRegression()
model = model.fit(X,y)

"""
#######
"""
scaler = StandardScaler()
x = scaler.fit_transform(x)
xTest = scaler.transform(xTest)

ridge_cv = RidgeCV(alphas=[0.1, 1.0, 10.0])  
ridge_cv.fit(x, y)

y_pred = ridge_cv.predict(xTest)
print("Model score (R^2):", r2_score(yTest, y_pred))

results = NFLtestingData["Name"].reset_index()
results = results.drop("index", axis=1)
results["Predicted Yards"] = y_pred
results.columns = ["Player", "Predicted Yards"]



# Create a pairplot
RecGamePlot = RecGameLogs.drop(["Name", "Team", "Opp", "EspnID", "REC", "TGTS", "Yds per Rec", "Rec TD", "Rec LNG", "CAR", "Rush YDS", "Rush AVG", "Rush LNG", "Rush TD", "FUM", "LST", "Year"], axis=1)
sns.pairplot(RecGameLogs)

# Show the plot
plt.show()

"""

#######
espnID = LoadEspnIDs()

#Pulling in the game logs
RecGameLogs = LoadRecGameLogs()
RushGameLogs = LoadRushGameLogs()
PassGameLogs = LoadPassGameLogs()

RecGameLogs = RecGameLogs[RecGameLogs["Year"] != 2024]
RushGameLogs = RushGameLogs[RushGameLogs["Year"] != 2024]
PassGameLogs = PassGameLogs[PassGameLogs["Year"] != 2024]

### Joining defensive stats ###

#Loading in the defensive passing statistics
DefPassStats = LoadDefPassing()
DefRushStats = LoadDefRushing()
DefPassStats = DefPassStats[DefPassStats["Year"] == 2025]
DefRushStats = DefRushStats[DefRushStats["Year"] == 2025]


#Performing a left-outer join to combine the game log data with the def passing stats data. NEED TO UPGRADE THIS MERGE.
NFLdataRec = pd.merge(RecGameLogs, DefPassStats, left_on=['Opp','Week','Year'], right_on=['Opp', 'Week', 'Year'], how='left')
NFLdataPass = pd.merge(PassGameLogs, DefPassStats, left_on=['Opp','Week','Year'], right_on=['Opp', 'Week', 'Year'], how='left')
NFLdataRush = pd.merge(RushGameLogs, DefRushStats, left_on=['Opp','Week','Year'], right_on=['Opp', 'Week', 'Year'], how='left')



#These functions are used for back testing my model. Don't use for week to week processing. Use last week. 
yTrainRec,xTrainRec,yTestRec,xTestRec,TrainingDataRec,TestingDataRec = modelPrepTesting(NFLdataRec, 9, 17, "Rec")
yTrainRush,xTrainRush,yTestRush,xTestRush,TrainingDataRush,TestingDataRush = modelPrepTesting(NFLdataRush, 9, 17, "Rush")
yTrainPass,xTrainPass,yTestPass,xTestPass,TrainingDataPass,TestingDataPass = modelPrepTesting(NFLdataPass, 9, 17, "Pass")

schedule = LoadSchedule(2025)
   
xTestRec = predPrep(xTestRec, DefPassStats, schedule, 10, "Rec")
xTestRush = predPrep(xTestRush, DefRushStats, schedule, 10, "Rush")
xTestPass = predPrep(xTestPass, DefPassStats, schedule, 10, "Pass")
        
resultsRec = BuildModel(yTrainRec, xTrainRec, yTestRec, xTestRec, TrainingDataRec, TestingDataRec, "Rec", "StepLinear", 10, "Step_2.0")
resultsRush = BuildModel(yTrainRush, xTrainRush, yTestRush, xTestRush, TrainingDataRush, TestingDataRush, "Rush", "StepLinear", 10, "Step_2.0")
resultsPass = BuildModel(yTrainPass, xTrainPass, yTestPass, xTestPass, TrainingDataPass, TestingDataPass, "Pass", "StepLinear", 10, "Step_2.0")


#Sending forecasts to the DB
SendRecYdsForecast(resultsRec,2025)
SendRushYdsForecast(resultsRush,2025)
SendPassYdsForecast(resultsPass,2025)

#Loading Betting Lines back in
RecBettingData = LoadRecBettingLines()
RushBettingData = LoadRushBettingLines()
PassBettingData = LoadPassBettingLines()

predRec = Predictions(resultsRec, RecBettingData, espnID, "Rec", 10, 2025, "Step_2.0")
predRush = Predictions(resultsRush, RushBettingData, espnID, "Rush", 10, 2025, "Step_2.0")
predPass = Predictions(resultsPass, PassBettingData, espnID, "Pass", 10, 2025, "Step_2.0")

#Sending prediction data to the DB
SendRecYdsPredictions(predRec)
SendRushYdsPredictions(predRush)
SendPassYdsPredictions(predPass)

### Select best bets ###

def BestBets(RecPreds, RushPreds, PassPreds, RecModel, RushModel, PassModel, exp, bets, week, year):
    #Filtering down by expected payout value, week, year, and model. Pass yard predictions under 200 yards are unreliable, so I'm trimming those out. 
    BestRec = RecPreds[(RecPreds["Expected Over Payout"] > exp) & (RecPreds["Week"] == week) & (RecPreds["Year"] == year) & (RecPreds["Model"] == RecModel)]
    BestRec["Stat"] = "Rec"
    BestRush = RushPreds[(RushPreds["Expected Over Payout"] > exp) & (RushPreds["Week"] == week) & (RushPreds["Year"] == year) & (RushPreds["Model"] == RushModel)]
    BestRush["Stat"] = "Rush"
    BestPass = PassPreds[(PassPreds["Predicted Yards"] > 200) & (PassPreds["Expected Over Payout"] > exp) & (PassPreds["Week"] == week) & (PassPreds["Year"] == year) & (PassPreds["Model"] == PassModel)]
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


predRec = LoadRecYdsPredictions()
predRush = LoadRushYdsPredictions()
predPass = LoadPassYdsPredictions()

Best = BestBets(predRec, predRush, predPass, "RF_1.0", "Ridge_1.0", "Ridge_1.0", 0.5, 20, 11, 2024)

#SendBestBets(Best)

###### AFTER GAMES ARE COMPLETE #####

#Pull my predictions back out of the database
#resultsRec = LoadRecYdsPredictions()
#resultsRush = LoadRushYdsPredictions()
#resultsPass = LoadPassYdsPredictions()

#Narrow the predicitons down to the most recent week.
#resultsRec = resultsRec[(resultsRec['Week'] == 17) & (resultsRec['Year'] == 2024) & (resultsRec['Model'] == 'Ridge_1.0')]
#resultsRush = resultsRush[(resultsRush['Week'] == 17) & (resultsRush['Year'] == 2024) & (resultsRush['Model'] == 'Ridge_1.0')]
#resultsPass = resultsPass[(resultsPass['Week'] == 17) & (resultsPass['Year'] == 2024) & (resultsPass['Model'] == 'Ridge_1.0')]

#Pull fresh game logs
#RecGameLogs = LoadRecGameLogs()
#RushGameLogs = LoadRushGameLogs()
#PassGameLogs = LoadPassGameLogs()

predRec = LoadRecYdsPredictions()
predRush = LoadRushYdsPredictions()
predPass = LoadPassYdsPredictions()

predRec = predRec[predRec["Model"] == "Step_2.0"]
predRush = predRush[predRush["Model"] == "Step_2.0"]
predPass = predPass[predPass["Model"] == "Step_2.0"]

predRecPrep = predRec[["Player", "Predicted Yards", "ID", "Week", "Year"]]
predRushPrep = predRush[["Player", "Predicted Yards", "ID", "Week", "Year"]]
predPassPrep = predPass[["Player", "Predicted Yards", "ID", "Week", "Year"]]
        
finalResultsRec = modEvalRec(predRecPrep, NFLdataRec, 10, 2025)
#finalResultsRecBest = modEvalRec(bestRecPrep, NFLdataRec, 11)

finalResultsRush = modEvalRush(predRushPrep, NFLdataRush, 10, 2025)
#finalResultsRushBest = modEvalRush(bestRushPrep, NFLdataRush, 11)

finalResultsPass = modEvalPass(predPassPrep, NFLdataPass, 10, 2025)
#finalResultsPassBest = modEvalPass(bestPassPrep, NFLdataPass, 11)


weeklyRecRes = WeeklyResults(finalResultsRec, 10, 2025, "Step_2.0")
weeklyRushRes = WeeklyResults(finalResultsRush, 10, 2025, "Step_2.0")
weeklyPassRes = WeeklyResults(finalResultsPass, 10, 2025, "Step_2.0")

SendWeeklyRes(weeklyRecRes, "Rec")
SendWeeklyRes(weeklyRushRes, "Rush")
SendWeeklyRes(weeklyPassRes, "Pass")

#weeklyResBest = WeeklyResults(finalResultsRecBest, 11)

#Need weekly high conf
    
### Analyzing results ###

def BestResults(week, year):
    #Load in the predictions
    BestBets = LoadBestBets()
    
    BestBets = BestBets[(BestBets["Week"] == week) & (BestBets["Year"] == year)]
    #Load in the stats
    RecGameLogs = LoadRecGameLogs()
    RecGameLogs["Stat"] = "Rec"
    
    RushGameLogs = LoadRushGameLogs()
    RushGameLogs["Stat"] = "Rush"
    
    PassGameLogs = LoadPassGameLogs()
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

BestRes = BestResults(1, 2025)
#SendBestBetsResults(BestRes)

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
    
    
#Load in full list of predictions for career results
resultsRec = LoadRecYdsPredictions()
resultsRush = LoadRushYdsPredictions()
resultsPass = LoadPassYdsPredictions()

#Pull fresh game logs
RecGameLogs = LoadRecGameLogs()
RushGameLogs = LoadRushGameLogs()
PassGameLogs = LoadPassGameLogs()
    
#Compute the results for all players
RecCareerRes = CareerResults(resultsRec, RecGameLogs, "Rec", "Over", "Ridge_2.0")
#RecCareerRes = CareerResults(resultsRec, RecGameLogs, "Rec", "Under", "Ridge_2.0")
RushCareerRes = CareerResults(resultsRush, RushGameLogs, "Rush", "Over", "Ridge_2.0")
#RushCareerRes = CareerResults(resultsRush, RushGameLogs, "Rush", "Under", "Ridge_1.0")
PassCareerRes = CareerResults(resultsPass, PassGameLogs, "Pass", "Over", "Ridge_2.0")
#PassCareerRes = CareerResults(resultsPass, PassGameLogs, "Pass", "Under", "Ridge_1.0")

#Send to the DB
SendCareerRecPreds(RecCareerRes, "Over", "Ridge_2.0")
SendCareerRushPreds(RushCareerRes, "Over", "Ridge_2.0")
SendCareerPassPreds(PassCareerRes, "Over", "Ridge_2.0")

CarRecPreds = LoadCareerRecPreds()
CarRushPreds = LoadCareerRushPreds()
CarPassPreds = LoadCareerPassPreds()

#Plots
CarRecPreds = CarRecPreds[CarRecPreds["Method"] == "Over"]
CarRushPreds = CarRushPreds[CarRushPreds["Method"] == "Over"]
CarPassPreds = CarPassPreds[CarPassPreds["Method"] == "Over"]

#Trimming down to RF 1.0
CarRecPreds = CarRecPreds[CarRecPreds["Model"] == "RF_1.0"]
CarRushPreds = CarRushPreds[CarRushPreds["Model"] == "RF_1.0"]
CarPassPreds = CarPassPreds[CarPassPreds["Model"] == "RF_1.0"]

#Trimming down to Ridge 1.0
CarRecPreds = CarRecPreds[CarRecPreds["Model"] == "Ridge_1.0"]
CarRushPreds = CarRushPreds[CarRushPreds["Model"] == "Ridge_1.0"]
CarPassPreds = CarPassPreds[CarPassPreds["Model"] == "Ridge_1.0"]

def PlotCareer(data):
    fig = plt.figure(figsize=(12, 12))  
    ax = fig.add_subplot()  
    color = {'Success':'blue', 'Failure':'red'}
    ax.scatter(data.loc[:,"Week"], data.loc[:,"Predicted Yards"], c=data["Result"].map(color))    #Plotting the scatter plot points.    
    plt.legend(loc='upper right')
    title = "Results mapped against Predicted Yards per Week"
    plt.title(title)
    plt.show()
        

PlotCareer(CarRecPreds)
PlotCareer(CarRushPreds)
PlotCareer(CarPassPreds)
###
CarRecPreds = CarRecPreds[(CarRecPreds["Model"] == "Ridge_2.0")]
CarRushPreds = CarRushPreds[(CarRushPreds["Model"] == "Ridge_2.0")]
CarPassPreds = CarPassPreds[(CarPassPreds["Model"] == "Ridge_2.0")]

CarRecPreds = CarRecPreds[(CarRecPreds["Year"] == 2025)]
CarRushPreds = CarRushPreds[(CarRushPreds["Year"] == 2025)]
CarPassPreds = CarPassPreds[(CarPassPreds["Year"] == 2025)]

CarRecPreds["Sportsbook Diff"] = CarRecPreds["Over"] - CarRecPreds["Rec YDS"]
CarRecPreds["Absolute Sportsbook Diff"] = abs(CarRecPreds["Over"] - CarRecPreds["Rec YDS"])

CarRushPreds["Sportsbook Diff"] = CarRushPreds["Over"] - CarRushPreds["Rush YDS"]
CarRushPreds["Absolute Sportsbook Diff"] = abs(CarRushPreds["Over"] - CarRushPreds["Rush YDS"])

CarPassPreds["Sportsbook Diff"] = CarPassPreds["Over"] - CarPassPreds["Pass YDS"]
CarPassPreds["Absolute Sportsbook Diff"] = abs(CarPassPreds["Over"] - CarPassPreds["Pass YDS"])

CarRecPreds = CarRecPreds[(CarRecPreds["Expected Over Payout"] > .05)]
CarRecPreds = CarRecPreds[(CarRecPreds["Expected Over Payout"] > .1)]
CarRecPreds = CarRecPreds[(CarRecPreds["Expected Over Payout"] > .25)]
CarRecPreds = CarRecPreds[(CarRecPreds["Expected Over Payout"] > .50)]

CarRushPreds = CarRushPreds[(CarRushPreds["Expected Over Payout"] > .05)]
CarRushPreds = CarRushPreds[(CarRushPreds["Expected Over Payout"] > .1)]
CarRushPreds = CarRushPreds[(CarRushPreds["Expected Over Payout"] > .25)]
CarRushPreds = CarRushPreds[(CarRushPreds["Expected Over Payout"] > .50)]


CarPassPreds = CarPassPreds[(CarPassPreds["Predicted Yards"] > 200)]
CarPassPreds = CarPassPreds[(CarPassPreds["Expected Over Payout"] > .05)]
CarPassPreds = CarPassPreds[(CarPassPreds["Expected Over Payout"] > .1)]
CarPassPreds = CarPassPreds[(CarPassPreds["Expected Over Payout"] > .25)]
CarPassPreds = CarPassPreds[(CarPassPreds["Expected Over Payout"] > .50)]




print(CarRecPreds.groupby("Result").count())
print("Absolute Prediction Difference: ", CarRecPreds["Absolute Pred Diff"].mean())
print("Absolute Sportsbook Difference: ", CarRecPreds["Absolute Sportsbook Diff"].mean())


print(CarRushPreds.groupby("Result").count())
print("Absolute Prediction Difference: ", CarRushPreds["Absolute Pred Diff"].mean())
print("Absolute Sportsbook Difference: ", CarRushPreds["Absolute Sportsbook Diff"].mean())

print(CarPassPreds.groupby("Result").count())
print("Absolute Prediction Difference: ", CarPassPreds["Absolute Pred Diff"].mean())
print("Absolute Sportsbook Difference: ", CarPassPreds["Absolute Sportsbook Diff"].mean())


#### Analyzing Season Data ####
recData = LoadCareerRecPreds()
rushData = LoadCareerRushPreds()
passData = LoadCareerPassPreds()


#Filtering out 2024
recData = recData[recData["Year"] == 2025]
rushData = rushData[rushData["Year"] == 2025]
passData = passData[passData["Year"] == 2025]

#
recData["Result"].value_counts()
rushData["Result"].value_counts()
passData["Result"].value_counts()


#Sorting the data by expected payout
recData_sorted = recData.sort_values(by='Expected Over Payout', ascending=True)
rushData_sorted = rushData.sort_values(by='Expected Over Payout', ascending=True)
passData_sorted = passData.sort_values(by='Expected Over Payout', ascending=True)

### Rec Yards Analysis ###

#Cutting out predictions of more than 100 and less than 10 yards.
recMid = recData[(recData["Predicted Yards"] > 10) & (recData["Predicted Yards"] < 100)]
recMid["Result"].value_counts()

#Cutting out predictions of more than 80 and less than 20 yards.
recMid = recData[(recData["Predicted Yards"] > 20) & (recData["Predicted Yards"] < 80)]
recMid["Result"].value_counts()


#### RANDOM FOREST 1.0 #####
###Rec
#Total Over = 53.16%
#Expected Greater than 0.05 = 53.36%
#Expected Greater than 0.1 = 52.95%
#Expected Greater than 0.25 = 56.93%
#Expected Greater than 0.5 = 56.58%



###Rush
#Total Over = 52.75%
#Expected Greater than 0.05 = 52.27%
#Expected Greater than 0.1 = 52.75%
#Expected Greater than 0.25 = 52.13%
#Expected Greater than 0.5 = 54.35%

###Pass
#Total Over = 40.76%
#Greater than 200 yards = 43.4%
    #Expected Greater than 0.05 = 43.66%
    #Expected Greater than 0.1 = 44.53%
    #Expected Greater than 0.25 = 48.88%
    #Expected Greater than 0.5 = 52.94%



### RIDGE 1.0 ####
###Rec
#Total Over = 51.05%
#Expected Greater than 0.05 = 52.73%
#Expected Greater than 0.1 = 53.33%
#Expected Greater than 0.25 = 52.60%
#Expected Greater than 0.5 = 60.87%



###Rush
#Total Over = 53.07%
#Expected Greater than 0.05 = 53.97%
#Expected Greater than 0.1 = 56.37%
#Expected Greater than 0.25 = 58.49%
#Expected Greater than 0.5 = 51.43%

###Pass
#Total Over = 51.09%
#Greater than 200 yards = 54.97%
    #Expected Greater than 0.05 = 54.29%
    #Expected Greater than 0.1 = 53.54%
    #Expected Greater than 0.25 = 56.04%
    #Expected Greater than 0.5 = 50.00%


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
        
RecPayout = CalcPayout(CarRecPreds, 10, 12, 2024)
RushPayout = CalcPayout(CarRushPreds, 10)   
PassPayout = CalcPayout(CarPassPreds, 10)           



"""
#Week 10
#R^2=0.4216
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=55, F=47
#RIDGE: -1.1943 model, -9.1961 sportbook
#RF: S=35, F=20
#RF: 1.0474 model, -13.3 sportbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=19, F=11
#RIDGE: 4.0364 model, -16.6 sportsbook
#RF: S=19:, F=7
#RF: 11.6415 model, -17.4615 sportsbook

#Week 11
#R^2=0.4783
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=65, F=43
#RIDGE: -4.5543 model, -12.8241 sportbook
#RF: S=38, F=20
#RF: -5.1131 model, -20.1897 sportbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=16, F=10
#RIDGE: 5.04757 model, -15.9231 sportsbook
#RF: S=19, F=9
#RF: 5.6118 model, -21.6071 sportbook


#Week 12
#R^2=0.4593
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=52, F=47
#RIDGE: -4.7997 model, -14.1464 sportbook
#RF: S=36, F=18
#RF: -1.6969 model, -14.1464 sportbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=20, F=17
#RIDGE: 11.2362 model, -10.1486 sportsbook
#RF: S=16, F=8
#RF: 12.0496 model, -18.1667 sportsbook



#Week 13
#R^2=0.4476
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=67, F=56
#RIDGE: -4.5862 model, -13.5569 sportbook
#RF: S=48, F=20
#RF: 2.3128 model, -17.8971 sportsbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=20, F=25
#RIDGE: 9.3062 model, -10.411 sportsbook
#This is a case where my high confidence picks were horrible. I have to go down to 5 to break positive.
#RF: S=30, F=10
#RF: 11.4225 model, 19.025 sportsbook



#Week 14
#R^2=0.5544
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=59, F=48
#RIDGE: -4.0295 model, -14.4813 sportbook
#RF: S=41, F=24
#RF: 5.3717 model, -16.2077 sportbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=24, F=16
#RIDGE: 7.2340 model, -14.85 sportsbook
#RF: S=27, F=9
#RF: 13.3019 model, -20.5 sportsbook



#Week 15
#R^2=0.4260
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=63, F=72
#RIDGE: 3.9470 model, -0.1296 sportbook
#RF: S=39, F=35
#RF: 12.2508 model, 0.66216 sportsbook


highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=10, F=13
#RIDGE: 12.4269 model, -1.4130 sportsbook
#I was actually 4-3 with a 20 conf. That could be worth testing across the board.
#RF: S=14, F=10
#RF: 23.2525 model, -7.500 model


#Week 16
#R^2=0.5667
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=47, F=46
#RIDGE: 2.194 model, -2.2097 sportbook
#RF: S=45, F=33
#RF: -0.404 model, -4.064 sportsbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=7, F=7
#RIDGE: 3.4423 model, -12.4286 sportsbook
#Could mess around with this number to get better results
#RF: S=10, F=4
#RF: 8.6779 model, -12.3571 sportsbook



#Week 17
finalResults = finalResults.drop_duplicates()
print(finalResults["Result"].value_counts())
print(finalResults.loc[:,"Model Difference"].mean())
print(finalResults.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=75, F=63
#RIDGE: -5.0159 model, -7.9275 sportbook
#RF: S=45, F=30
#RF: -2.526 model, -10.2067 sportsbook

highConf = finalResults[finalResults["Confidence"] > 15]
print(highConf["Result"].value_counts())
print(highConf.loc[:,"Model Difference"].mean())
print(highConf.loc[:,"SportsBook Difference"].mean())

#RIDGE: S=11, F=6
#RIDGE: -7.7984 model, -22.5 sportsbook
#RF: S=16, F=3
#RF: -2.8926 model, -24.3947 sportsbook


### RIDGE: 53.4% accurate overall,  54.7% high conf ###
### RF: 62.05% accurate overall, 71.56% high conf ###
"""




















