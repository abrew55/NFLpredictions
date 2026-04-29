# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 21:41:53 2025

@author: Austin
"""

import pymysql 
import pandas as pd

#This function will pull all existing Game Log data out of my SQL database. It requires pymysql and pandas libraries.

def LoadSchedule(year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    if (year == 2024):
        cur.execute("select * from NFLdata.schedule2024") 
    if (year == 2025):
        cur.execute("select * from NFLdata.schedule2025")
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Week", "Home Team", "Away Team"]
    
    conn.close()
    
    return output


def SendEspnIDs(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.espnid VALUES (%s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()
    
def LoadEspnIDs():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    

    cur.execute("select * from NFLdata.espnid")
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Name", "Team", "EspnID", "Position"]
    
    conn.close()
    
    return output
    
def LoadEspnIDsWithTeam():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    

    cur.execute("select * from NFLdata.espnid_team")
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Name", "Team", "EspnID", "Position"]
    
    conn.close()
    
    return output
    
def UpdateEspnIDsWtihTeam():
    reclogs = LoadRecGameLogs()
    rushlogs = LoadRushGameLogs()
    passlogs = LoadPassGameLogs()
    
    reclogs = reclogs.loc[:, ["Name", "Team", "EspnID"]]
    rushlogs = rushlogs.loc[:, ["Name", "Team", "EspnID"]]
    passlogs = passlogs.loc[:, ["Name", "Team", "EspnID"]]
    
    IDteam = pd.concat([reclogs, rushlogs, passlogs], ignore_index=True)
    IDteam = IDteam.drop_duplicates()
    
    ID = LoadEspnIDs()

    IDteam = pd.merge(IDteam, ID, how="inner", left_on="EspnID", right_on="ID")
    IDteam = IDteam.drop(columns = ["ID", "Name_y"])
    
    
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(IDteam)):
        SQL = "INSERT INTO NFLdata.espnid_team VALUES (%s, %s, %s, %s)"
        cur.execute(SQL, tuple(IDteam.loc[row,:])) 
        conn.commit()
    
    #Delete any duplicate rows in the table
    SQL = "WITH CTE AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY name, team, espnid, position ORDER BY espnid) as row_num FROM espnid_team) DELETE FROM CTE WHERE row_num > 1;"
    cur.execute(SQL)
    conn.commit
    
    # To close the connection 
    conn.close()
    
    
def LoadRecGameLogs():  
    #Loads a list of column headers. This is better than typing them out.
    Headers = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RecGameLogsHeaders.csv')           
    Headers = Headers.columns
    
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.recgamelogs") 
    output = pd.DataFrame(cur.fetchall())
    print(output)

    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = Headers
      
    # To close the connection 
    conn.close() 

    return output

#This function will send the data from my Game Logs to the database 1 by 1. The passed dataset should only contain the most recent week's data.
def SendRecGameLogs(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO recgamelogs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()
    
def FinalSendRecGameLogs(data, week, year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    
    SQL = "DELETE FROM NFLdata.recgamelogs WHERE Year = %s AND Week = %s"
    cur.execute(SQL, tuple([year, week]))
    
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO recgamelogs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()

def LoadPassGameLogs():  
    #Loads a list of column headers. This is better than typing them out.
    Headers = pd.read_csv('D:/Data Science Stuff/Betting Project 3/PassGameLogsHeaders.csv')           
    Headers = Headers.columns
    
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.passgamelogs") 
    output = pd.DataFrame(cur.fetchall())

    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = Headers
      
    # To close the connection 
    conn.close() 

    return output



#This function will send the data from my Game Logs to the database 1 by 1. The passed dataset should only contain the most recent week's data.
def SendPassGameLogs(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO passgamelogs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()
    
#This function will send the data from my Game Logs to the database 1 by 1. The passed dataset should only contain the most recent week's data.
def FinalSendPassGameLogs(data, week, year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor() 
    
    SQL = "DELETE FROM NFLdata.passgamelogs WHERE Year = %s AND Week = %s"
    cur.execute(SQL, tuple([year, week]))
    
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO passgamelogs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()
    


def LoadRushGameLogs():  
    #Loads a list of column headers. This is better than typing them out.
    Headers = pd.read_csv('D:/Data Science Stuff/Betting Project 3/RushGameLogsHeaders.csv')           
    Headers = Headers.columns
    
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.rushgamelogs") 
    output = pd.DataFrame(cur.fetchall())

    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = Headers
      
    # To close the connection 
    conn.close() 

    return output

#This function will send the data from my Game Logs to the database 1 by 1. The passed dataset should only contain the most recent week's data.
def SendRushGameLogs(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO rushgamelogs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()
    
#This function will send the data from my Game Logs to the database 1 by 1. The passed dataset should only contain the most recent week's data.
def FinalSendRushGameLogs(data, week, year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    
    SQL = "DELETE FROM NFLdata.rushgamelogs WHERE Year = %s AND Week = %s"
    cur.execute(SQL, tuple([year, week]))
    
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO rushgamelogs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()
    

def SendRecBettingLines(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO betting_recyds VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()    
    
    
def LoadRecBettingLines():  
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.betting_recyds") 
    output = pd.DataFrame(cur.fetchall())

    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Year"]
      
    # To close the connection 
    conn.close() 

    return output    

def SendPassBettingLines(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO betting_passyds VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()    
    
    
def LoadPassBettingLines():  
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.betting_passyds") 
    output = pd.DataFrame(cur.fetchall())

    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Year"]
      
    # To close the connection 
    conn.close() 

    return output 

def SendRushBettingLines(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO betting_rushyds VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()    
    
    
def LoadRushBettingLines():  
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.betting_rushyds") 
    output = pd.DataFrame(cur.fetchall())

    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Player", "Position", "Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Year"]
      
    # To close the connection 
    conn.close() 

    return output 


def LoadDefPassing():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.defensepassingstats") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Opp", "DADOT", "Blitz%", "Hrry%", "QBKD%", "Prss%", "Cmp%", "TD%", "Int%", "Y/A", "AY/A", "Y/C", "Y/G", "Rate", "Sk%", "NY/A", "ANY/A", "EXP", "Year", "Week"]
      
    # To close the connection 
    conn.close() 

    return output    
  

def SendDefPassing(data, year, week):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    data["Week"] = week
    
    #Create the cursor object
    cur = conn.cursor()  
    
    #Deleting the old data for the specified year.
    #SQL = "DELETE FROM NFLdata.defensepassingstats WHERE Year = %s"
    #cur.execute(SQL, tuple([year, week])
    
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.defensepassingstats VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()  
    
    

def LoadDefRushing():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.defenserushingstats") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Opp", "ATT", "YDS", "TD", "Y/A", "Y/G", "EXP", "Year", "Week"]
      
    # To close the connection 
    conn.close() 

    return output   


    
def SendDefRushing(data, year, week):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    data["Week"] = week
     
    #Create the cursor object
    cur = conn.cursor()  
    #Deleting the old data for the specified year.
    #SQL = "DELETE FROM NFLdata.defenserushingstats WHERE Year = %s"
    #cur.execute(SQL, year)

    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.defenserushingstats VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()    
 
def LoadTeamNames():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.teamnames") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Long Name", "Short Name"]
    
    conn.close()
    
    return output
  
  
### Forecast Queries ###  
  
def SendRecYdsForecast(data, year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    #Adding additional column to determine the year
    data["Year"] = year
    
    #Insert the table data row by row
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.recydsforecasts VALUES (%s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
        
     #To close the connection 
    conn.close()
    
    
def SendRushYdsForecast(data, year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    #Adding additional column to determine the year
    data["Year"] = year
    
    #Insert the table data row by row
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.rushydsforecasts VALUES (%s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
        
    # To close the connection 
    conn.close()
    
def SendPassYdsForecast(data, year):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    #Adding additional column to determine the year
    data["Year"] = year
    
    #Insert the table data row by row
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.passydsforecasts VALUES (%s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
    #To close the connection 
    conn.close()  
    
    
def LoadRecYdsForecast():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.recydsforecasts") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Player", "Predicted Yards", "Week", "Model"]
    
    conn.close()
    
    return output


def LoadRushYdsForecast():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.rushydsforecasts") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Player", "Predicted Yards", "Week", "Model"]
    
    conn.close()
    
    return output



def LoadPassYdsForecast():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.passydsforecasts") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Player", "Predicted Yards", "Week", "Model"]
    
    conn.close()
    
    return output    
    
### Prediction Queries ### 

def SendRecYdsPredictions(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    #Insert the table data row by row
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.recydspredictions VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
        
     #To close the connection 
    conn.close()
    
    
def SendRushYdsPredictions(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    #Insert the table data row by row
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.rushydspredictions VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
        
    # To close the connection 
    conn.close()
    
def SendPassYdsPredictions(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    #Insert the table data row by row
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.passydspredictions VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
    #To close the connection 
    conn.close()  
    
    
def LoadRecYdsPredictions():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.recydspredictions") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model"]
    
    conn.close()
    
    return output


def LoadRushYdsPredictions():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.rushydspredictions") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model"]
    
    conn.close()
    
    return output



def LoadPassYdsPredictions():
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    #This query simply loads in all of the data from the team names table.
    cur.execute("select * from NFLdata.passydspredictions") 
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model"]
    
    conn.close()
    
    return output    


### Weekly Result Queries ###
    
def SendWeeklyRes(data, stat):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    if(stat == "Rec"):
        #Insert the row to the dataframe
            SQL = "INSERT INTO NFLdata.weeklyres_rec VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(SQL, data) 
            conn.commit()
        
    if(stat == "Rush"):
        #Insert the row to the dataframe
            SQL = "INSERT INTO NFLdata.weeklyres_rush VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(SQL, data) 
            conn.commit()
            
    if(stat == "Pass"):
        #Insert the row to the dataframe
            SQL = "INSERT INTO NFLdata.weeklyres_pass VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(SQL, data) 
            conn.commit()
    
    #To close the connection 
    conn.close()  
    
    
def LoadWeeklyRes(stat):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        )
    
    cur = conn.cursor() 
    
    if(stat == "Rec"):
        cur.execute("select * from NFLdata.weeklyres_rec")
    if(stat == "Rush"):
        cur.execute("select * from NFLdata.weeklyres_rush")
    if(stat == "Pass"):
        cur.execute("select * from NFLdata.weeklyres_pass")
        
    output = pd.DataFrame(cur.fetchall())
    
    output.columns = ["Win%", "Model Difference", "Sportsbook Difference", "Week", "Model", "Year"]
    
    conn.close()
    
    return output  


### Career Betting Queries ###

def SendCareerRecPreds(data, method, model):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    
    #Deleting the old data for the specified method.
    if(method == "Over"):
        SQL = "DELETE FROM NFLdata.career_recyds_preds WHERE Method='Over' AND Model=(%s)"
        
    if(method == "Under"):
        SQL = "DELETE FROM NFLdata.career_recyds_preds WHERE Method='Under' AND Model=(%s)"
    cur.execute(SQL, model)
    
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.career_recyds_preds VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()  


def LoadCareerRecPreds():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.career_recyds_preds") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model", "Result", "Method", "Opp", "Rec YDS", "Pred Diff", "Absolute Pred Diff", "Sportsbook Diff", "Absolute Sportsbook Diff"]
      
    # To close the connection 
    conn.close() 

    return output 

    
def SendCareerRushPreds(data, method, model):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    
    #Deleting the old data for the specified method.
    if(method == "Over"):
        SQL = "DELETE FROM NFLdata.career_rushyds_preds WHERE Method='Over' AND Model=(%s)"
        
    if(method == "Under"):
        SQL = "DELETE FROM NFLdata.career_rushyds_preds WHERE Method='Under' AND Model=(%s)"
    cur.execute(SQL, model)
    
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.career_rushyds_preds VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()      


def LoadCareerRushPreds():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.career_rushyds_preds") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model", "Result", "Method", "Opp", "Rush YDS", "Pred Diff", "Absolute Pred Diff", "Sportsbook Diff", "Absolute Sportsbook Diff"]
      
    # To close the connection 
    conn.close() 

    return output 

    
def SendCareerPassPreds(data, method, model):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
     
    #Create the cursor object
    cur = conn.cursor()  
    
    #Deleting the old data for the specified method.
    if(method == "Over"):
        SQL = "DELETE FROM NFLdata.career_passyds_preds WHERE Method='Over' AND Model=(%s)"
        
    if(method == "Under"):
        SQL = "DELETE FROM NFLdata.career_passyds_preds WHERE Method='Under' AND Model=(%s)"
    cur.execute(SQL, model)
    
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.career_passyds_preds VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
    
     # To close the connection 
    conn.close()  
    
    
    
def LoadCareerPassPreds():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
      
    # Select query 
    cur.execute("select * from NFLdata.career_passyds_preds") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model", "Result", "Method", "Opp", "Pass YDS", "Pred Diff", "Absolute Pred Diff", "Sportsbook Diff", "Absolute Sportsbook Diff"]
      
    # To close the connection 
    conn.close() 

    return output 


### Best Bets ###

def SendBestBets(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.bestbets VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
     
    #Create the cursor object
    cur = conn.cursor()  
    
    
def LoadBestBets():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    # Select query 
    cur.execute("select * from NFLdata.bestbets") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model", "Stat"]
      
    # To close the connection 
    conn.close() 

    return output 

def SendBestBetsResults(data):
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    cur = conn.cursor()  
    # Select query 
    for row in range(0,len(data)):
        SQL = "INSERT INTO NFLdata.bestbets_results VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.execute(SQL, tuple(data.loc[row,:])) 
        conn.commit()
     
    #Create the cursor object
    cur = conn.cursor()  
    
    
def LoadBestBetsResults():
    #Create the connection to the SQL server
    conn = pymysql.connect( 
        host='localhost', 
        user='root',  
        password = "Alpaca44!", 
        db='NFLdata', 
        ) 
    
    #Create the cursor object
    cur = conn.cursor() 
    
    # Select query 
    cur.execute("select * from NFLdata.bestbets_results") 
    output = pd.DataFrame(cur.fetchall())
    
    #Assign the output dataframe the proper headers (it was 1,2,3,4,etc.)
    output.columns = ["Over", "Over Payout", "Under", "Under Payout", "Week", "Team", "ID", "Player", "Predicted Yards", "Expected Under Payout", "Expected Over Payout", "Year", "Model", "Stat", "Result", "Actual Yards"]
      
    # To close the connection 
    conn.close() 

    return output 