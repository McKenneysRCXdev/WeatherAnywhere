import numpy as np
import requests as r
import datetime as d
import csv
import Calendar

#The intent of this code is to use WeatherUndergound as a tool to web-scrape historic weather data from their site
#and export the data to a CSV. Right now, the latitude and longintude need to be known, and the dates are picked before
#the function is called. We would like to eventually add a zip-code repository to allow for the latitude and longitude to
#be found more easily.

#Example URL
#'https://api.weather.com/v1/geocode/33.7788887/-84.52111053/observations/historical.json?apiKey=6532d6454b8aa370768e63d6ba5a832e&startDate=20190206&endDate=20190206&units=e')

def buildNewObservationArray(longitude, latitude, startDate, endDate):
    #This function builds an array for the day in question. If time is within 1 hour of start time or end time,
    #it is included in the array that is exported via CSV. Note, the end time needs to be at least 1 minute more than the
    #start time.
    if startDate == endDate:
        print("End time needs to be at least 1 minute more than start time")
        return
    csvFileName = "WeatherUndergroundData.csv"
    csvFile = open(csvFileName, 'wb')
    writer = csv.writer(csvFile)
    JSONdata = getObservationArray(longitude,latitude,startDate,endDate)
    pointsOfInterest = ['valid_time_gmt', 'obs_name', 'temp', 'rh', 'dewPt', 'feels_like', 'pressure', 'wspd', 'wx_phrase', 'vis', 'wdir_cardinal', 'precip_hrly', 'precip_total' ]
    weatherTable = ['Time', 'Station', 'Temperature', 'Relative Humidity', 'Dew Point', 'Feels Like', 'Pressure', 'Wind Speed', 'Condition', 'Visibility', 'Wind Direction', 'Precipitation rate', 'Precipitation Accumulation']
    writer.writerow(weatherTable)
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
            dontAddToBuildRow = False
    csvFile.close()
    print(weatherTable)
    return weatherTable

def getObservationArray(longitude, latitude, startingDate, endingDate):
    #Called in buildNewObservationArray, this function exports a JSON array obtained from Weather Underground.
    #The export contains raw data that is compiled from multipe "gets" from the URL.
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
    #Used in createNewObservationArray, this converts weather underground's time to an actual time.
    #Note: weather underground's time clock starts 1/1/1970 at 0:00
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


# def pickDates():
#     #I found a code that creates a pop up where the user can type in the date and when hitting enter, the date is shown
#     #in the console. This might be useful in trying to standardize the date inputs, but perhaps not.
#     execfile('Calendar.py')


#Run the code
#datetime is (yyyy,month,day,hr,min)
beginDate = d.datetime(2019,2,8,11,00)
finishDate = d.datetime(2019,2,8,11,01)
buildNewObservationArray('33.7788887','-84.52111053',beginDate,finishDate)
