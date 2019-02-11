from types import NoneType
import numpy as np
import urllib
import requests as r
import datetime as d
import csv
import Calendar

#Get weather data from Weather Underground from a specified location and on a certain date.
#'https://api.weather.com/v1/geocode/33.7788887/-84.52111053/observations/historical.json?apiKey=6532d6454b8aa370768e63d6ba5a832e&startDate=20190206&endDate=20190206&units=e')
#def convertZipcodeToCoord(Zipcode): #later - convert zip code to lat, long coordinates

def buildNewObservationArray(longitude, latitude, startDate, endDate):
    #Build an array for the day in question.. If a time matches
    csvFileName = "WeatherUndergroundData.csv"
    csvFile = open(csvFileName, 'wb')
    writer = csv.writer(csvFile)
    JSONdata = getObservationArray(longitude,latitude,startDate,endDate)
    pointsOfInterest = ['valid_time_gmt', 'obs_name', 'temp', 'rh', 'dewPt', 'feels_like', 'pressure', 'wspd', 'wx_phrase', 'vis', 'wdir_cardinal', 'precip_hrly', 'precip_total' ]
    weatherTable = ['Time', 'Station', 'Temperature', 'Relative Humidity', 'Dew Point', 'Feels Like', 'Pressure', 'Wind Speed', 'Condition', 'Visibility', 'Wind Direction', 'Precipitation rate', 'Precipitation Accumulation']
    writer.writerow(weatherTable)
    specificTimeTable = weatherTable
    foundTime = False
    dontAddToBuildRow = False
    for stamp in JSONdata:
        buildRow = np.zeros([1,len(pointsOfInterest)],dtype = object)
        for group in stamp:
            for title in group:
                try:
                    index = pointsOfInterest.index(title)
                    value = group[title]
                    if title == 'valid_time_gmt':
                        value = timeConversion(value)
                        valueDT = d.datetime(int(value[:4]), int(value[5:7]), int(value[8:10]), int(value[11:13]), int(value[14:16]))
                        timeBeforeStart = startDate - valueDT
                        timeAfterFinish = valueDT - endDate
                        if (timeBeforeStart.seconds > 3600 and timeBeforeStart.days >= 0):
                            dontAddToBuildRow = True
                        if (timeAfterFinish.seconds > 3600 and timeAfterFinish.days >= 0):
                            dontAddToBuildRow = True
                    if type(value) is unicode:
                        value = str(value)
                    buildRow[0, index] = value
                except:
                    pass
            if dontAddToBuildRow != True:
                writer.writerow(buildRow[0,:])
                weatherTable = np.vstack([weatherTable,buildRow])
            if foundTime == True:
                specificTimeTable = np.vstack([specificTimeTable,buildRow])
            foundTime = False
            dontAddToBuildRow = False
    csvFile.close()
    print(specificTimeTable)
    print('------------------')
    print(weatherTable)
    return weatherTable

def getObservationArray(longitude, latitude, startingDate, endingDate):
    #inputs for startingDate and endingDate need to be consistent with datetime library
    observationArray = []
    url = 'https://api.weather.com/v1/geocode/' + longitude + '/' + latitude + '/observations/historical.json?'
    timeDifference = endingDate - startingDate

    while timeDifference.seconds != 0.:
        if timeDifference.days > 30.:
            EndDate = startingDate + d.timedelta(30.)
        else:
            EndDate = endingDate
        endTimeStampStr = str(EndDate)
        endingDateStr = endTimeStampStr[:4] + endTimeStampStr[5:7] + endTimeStampStr[8:10]
        startTimeStampStr = str(startingDate)
        startingDateStr = startTimeStampStr[:4] + startTimeStampStr[5:7] + startTimeStampStr[8:10]
        params = dict(
            apiKey = '6532d6454b8aa370768e63d6ba5a832e',
            startDate= startingDateStr,
            endDate = endingDateStr,
            units = 'e'
        )
        rawData = r.get(url, params)
        checkResponse = rawData.status_code
        if checkResponse != 200:
            print("There may be an error with the URL")
            return
        JSONdata = rawData.json()
        startingDate = EndDate
        timeDifference = endingDate - startingDate
        observationArray.append(JSONdata['observations'])
    return observationArray


def timeConversion(WUtime_gmt):
    #converts weather underground's time to an actual time. Note: weather underground's time clock starts 1/1/1970 at 0:00
    secPerMin = 60.
    minPerHour = 60.
    hrsPerDay = 24.
    daysPerYear = 365.
    conversionFactor = secPerMin*minPerHour*hrsPerDay*daysPerYear
    adjustGMTtoEST = 5./24
    yrs = WUtime_gmt / conversionFactor
    timeSinceStart = yrs*daysPerYear - adjustGMTtoEST
    currentTime = d.datetime(1970,1,1) + d.timedelta(days = timeSinceStart)
    return str(currentTime)


def pickDates():   #for standardizing calendar input
    execfile('Calendar.py')
# StartDate = None
# while StartDate is None:
#     StartDate = Calendar.startDate()
# print(StartDate)

#pickDates()
#execfile('Calendar.py')




#run code
beginDate = d.datetime(2019,2,8,11,00)
finishDate = d.datetime(2019,2,8,11,59)
buildNewObservationArray('33.7788887','-84.52111053',beginDate,finishDate)
