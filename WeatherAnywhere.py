import numpy as np
import requests as r
import datetime as d
import csv
import re
import Calendar

#The intent of this code is to use WeatherUndergound as a tool to web-scrape historic weather data from their site
#and export the data to a CSV. Right now, all you need is a zipcode and the dates you want before
#the function is called.
#Special Notes:
#   Start/ Stop times need to be at least 1 minute apart.
#   If data at a zipcode is non-existent for a given month, it will grab data from Atlanta/ Fulton Station (default)
#   If no data exists within an hour before start time or an hour after end time, the data will be pulled from default station
#       It is possible to see the closest time stamp at a given site. If that is prefered, uncomment the related code

#Example URL
#'https://api.weather.com/v1/geocode/33.7788887/-84.52111053/observations/historical.json?apiKey=6532d6454b8aa370768e63d6ba5a832e&startDate=20190206&endDate=20190206&units=e')

def exportWeatherGivenTimeStamps(incidentFile):
    incidentData = readCSV(incidentFile, 0)
    newIncidentDataW = incidentFile[0:-4] + "_weatherAdded" + incidentFile[-4:]
    csvWriteFile = open(newIncidentDataW, 'wb')
    writer = csv.writer(csvWriteFile)
    initalHeaders = incidentData[0]
    headers = np.append(initalHeaders,['Time', 'Station', 'Temperature', 'Relative Humidity', 'Dew Point', 'Feels Like', 'Pressure', 'Wind Speed', 'Condition', 'Visibility', 'Wind Direction', 'Precipitation rate', 'Precipitation Accumulation'])
    writer.writerow(headers)
    for row in incidentData[1:]:
        if row[2] == '':
            latitude = 33.7788887
            longitude = -84.52111053
        else:
            latitude, longitude = getDataUsingZipcode(row[2])
        dateStampArr = re.split('/',row[0])
        timeStampArr = re.split(':',row[1])
        year = int(dateStampArr[2])
        month = int(dateStampArr[0])
        day = int(dateStampArr[1])
        hour = int(timeStampArr[0])
        minute = int(timeStampArr[1])
        startDate = d.datetime(year,month,day,hour,minute)
        endDate = d.datetime(year,month,day,hour,minute + 1)
        weatherTable = buildNewObservationArray(latitude,longitude,startDate,endDate)

        dateTimeArr = []
        weatherTableNoHeader = weatherTable[1:]
        for weatherRow in weatherTableNoHeader:
            dateTimeW = re.split(' ',weatherRow[0])
            dateResult = re.split('-',dateTimeW[0])
            timeResult = re.split(':',dateTimeW[1])
            yearW = int(dateResult[0])
            monthW = int(dateResult[1])
            dayW = int(dateResult[2])
            hourW = int(timeResult[0])
            minuteW = int(timeResult[1])
            weatherDate = d.datetime(yearW,monthW,dayW,hourW,minuteW)
            timeDiff = abs(weatherDate - startDate)
            dateTimeArr.append(timeDiff)

        closestDate = np.argmin(dateTimeArr)
        newRow = np.append(row,weatherTableNoHeader[closestDate])
        writer.writerow(newRow)

    csvWriteFile.close()
    return

def getDataUsingZipcode(zipcode):
    zipCodeData = readCSV("ZipData.csv",1)
    foundZip = False
    for zip in zipCodeData:
        if zip[0] == float(zipcode):
            foundZip = True
            return zip[1], zip[2]
    if foundZip == False:
        return 33.7788887, -84.52111053


def buildNewObservationArray(latitude, longitude, startDate, endDate):
    #This function builds an array for the day in question. If time is within 1 hour of start time or end time,
    #it is included in the array that is exported via CSV. Note, the end time needs to be at least 1 minute more than the
    #start time.
    if startDate == endDate:
        print("End time needs to be at least 1 minute more than start time")
        return
    if type(longitude) == float or type(latitude) == float:
        latitude = str(latitude)
        longitude = str(longitude)
    csvFileName = "WeatherUndergroundData.csv"
    csvFile = open(csvFileName, 'wb')
    writer = csv.writer(csvFile)
    JSONdata = getObservationArray(latitude,longitude,startDate,endDate)
    pointsOfInterest = ['valid_time_gmt', 'obs_name', 'temp', 'rh', 'dewPt', 'feels_like', 'pressure', 'wspd', 'wx_phrase', 'vis', 'wdir_cardinal', 'precip_hrly', 'precip_total' ]
    weatherTable = np.array([['Time', 'Station', 'Temperature', 'Relative Humidity', 'Dew Point', 'Feels Like', 'Pressure', 'Wind Speed', 'Condition', 'Visibility', 'Wind Direction', 'Precipitation rate', 'Precipitation Accumulation']])
    backupWeatherTable = weatherTable
    writer.writerow(weatherTable)
    dontAddToBuildRow = False
    minBeforeStart = []
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
                        minBeforeStart = np.append(minBeforeStart,timeBeforeStart.seconds)
                    if type(value) is unicode:
                        value = str(value)
                    buildRow[0, index] = value
                except:
                    pass
            if dontAddToBuildRow != True:
                writer.writerow(buildRow[0,:])
                weatherTable = np.vstack([weatherTable,buildRow])
            dontAddToBuildRow = False
            backupWeatherTable = np.vstack([backupWeatherTable,buildRow])
    if len(weatherTable) == 1:
        #this will find a similar time but at the default station
        weatherTable = buildNewObservationArray(33.7788887, -84.52111053,startDate,endDate)

        # #This will pick the closest time at the current weather station (Note that it is outside an hour of the requested timestamp)
        # min = np.argmin(minBeforeStart)
        # weatherTable = np.vstack([weatherTable,backupWeatherTable[min]])
    csvFile.close()
    print(weatherTable)
    return weatherTable

def getObservationArray(latitude, longitude, startingDate, endingDate):
    #Called in buildNewObservationArray, this function exports a JSON array obtained from Weather Underground.
    #The export contains raw data that is compiled from multipe "gets" from the URL.
    observationArray = []
    url = 'https://api.weather.com/v1/geocode/' + latitude + '/' + longitude + '/observations/historical.json?'
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
        if checkResponse == 400: #400 is the error if there is no data at that station for that time period. The default station is referenced to gain data for that time stamp.
            observationArray = getObservationArray(33.7788887, -84.52111053,startTimeStampStr, endTimeStampStr)
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

def readCSV(csvFilename, numHeaderLines = 0):
    #Produces data array of the CSV file which is used in functions: "testCSVdata" and "trainingFromCSVdata"
    csvfile = open(csvFilename,"r")
    csvLines = csv.reader(csvfile)
    dataArray = []
    headerLinesEncountered = 0
    for currRow in csvLines:
        if headerLinesEncountered < numHeaderLines:
            # Is a header line, so skip
            headerLinesEncountered+=1
        else:
            # Is actual data, so convert to numbers if possible
            cleanedRowArray = []
            for currCell in currRow:
                try:
                    cleanedRowArray.append(float(currCell.replace(",", "")))
                except ValueError:
                    cleanedRowArray.append(currCell)
            dataArray.append(cleanedRowArray)
    csvfile.close()
    return dataArray


# def pickDates():
#     #A code was found that creates a pop up where the user can type in the date and when hitting enter, the date is shown
#     #in the console. This might be useful in trying to standardize the date inputs, but perhaps not.
#     execfile('Calendar.py')


# #Run the code
# #datetime is (yyyy,month,day,hr,min)
# Latitude, Longitude = getDataUsingZipcode(30009)
# beginDate = d.datetime(2018,7,12,8,40)
# finishDate = d.datetime(2018,7,12,8,41)
# buildNewObservationArray(Latitude,Longitude,beginDate,finishDate)


#The following function was build anticipating the input file would have
#   Dates in column A (separated by '/') 1/1/1970
#   Time in column B (separated by ':')  1:01:00
#   Zipcodes in column C
exportWeatherGivenTimeStamps('TimeStampData.csv')