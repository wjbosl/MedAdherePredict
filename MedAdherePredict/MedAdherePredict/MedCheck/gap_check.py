
# Imports
import datetime
import adherence_predict as adhere
from django.conf import settings
import numpy as np

# Global variables
ISO_8601_DATETIME = '%Y-%m-%d'


"""    
File: gap_check.py

    Written by: William J. Bosl
    Children's Hospital Boston Informatics Program
    300 Longwood Avenue
    Boston, MA 02115

    Description: This class has a function that takes a list of prescription fulfillment
    dates and checks for gaps larger than a specified threshold.

"""
def gap_check(patient_refill_data, drug, birthday):
    
    # Local variables
    model_prediction_days = [60,90,120]
    threshold = 30     # default threshold in days
    gap_flag = []
    max_gap = {}
    refill_data = {}
    mpr_tseries = {}
    refill_day = {}
    gaps = {}
    predictedMPR = {}
    actualMPR = {}
    logistic_data_file = settings.MEDIA_ROOT + "genLinearModel.txt"
    adherence = adhere.adherence_predict(logistic_data_file)
        
    # Go through the list of refill data for each drug and determine which have gaps
    for data in patient_refill_data: 
        #med = data[0]
        name = data[1]
        if drug=='all' or drug==name:
            quant = int(data[2])
            when = data[3]
            d = datetime.datetime.strptime(str(when), ISO_8601_DATETIME) 
            actualMPR[name] = [0.7,0.8,0.9,1.0] 
            age_on_first_fill = {}
                    
            # Organize all refill dates by drug name 
            max_gap[name] = 0.0
            if not refill_data.has_key(name):
                refill_data[name] = {}
                mpr_tseries[name] = []
                gaps[name] = []
                refill_day[name] = []
            refill_data[name][d] = quant
    sorted(refill_data.keys())
                    
    # Check for gaps and predict adherence
    for name in refill_data.keys():
        dates = refill_data[name].keys()
        npills = refill_data[name].values()
        pMPR_yesno = False
        
        # Sort dates and npills list together / simultaneously
        dates, npills = zip(*sorted(zip(dates, npills)))
                        
        # If the total pills for all refills is less than 1 year, make an adherence
        # prediction based on the regression model.
        make_prediction = False
        if np.sum(npills) < 365:
            make_prediction = True
        
        # Determine the patient's age on the date of first fill for this med
        date0 = dates[0]
        first = date0       # This will change; it's the fill date or the day on which the 
        last = date0        # next batch of pills will start to be used.
        bd = datetime.datetime.strptime(str(birthday), ISO_8601_DATETIME)
        age_on_first_fill[name] = date0 - bd
                        
        pMPR = 1.0
        age = age_on_first_fill[name].days/365          # Age in years on first fill date

        nDates = len(dates)
        nDays = (dates[nDates-1] - date0).days + npills[nDates-1]
                
        mpr = 1.0
        day = 0     # Initial fill
        pills_available = npills[0]
        total_pills_taken = 0
        days_since_initial_fill = 0
        next_refill_index = 1
        next_refill_day = 0
        if nDates > 1:
            next_refill_day = (dates[1] - date0).days
        mpr_tseries[name].append( [0, mpr] )
        predictedMPR[name] = [ [day,mpr], [day, mpr] ] 
        refill_day[name].append([0,1.0])
        for day in range(1, nDays): 
                                        
            # Is it time for a refill? Check to see if prescription was filled
            if day == next_refill_day and next_refill_day < nDays:
                refill_day[name].append([day,mpr])
                pills_available += npills[next_refill_index]
                next_refill_index += 1
                if nDates > next_refill_index:                    
                    next_refill_day = (dates[next_refill_index] - date0).days       
            
            # Does the patient still have pills left? If so, increment
            if pills_available > 0:
                pills_available -= 1
                total_pills_taken += 1
            # Time marches on whether or not patient has pills
            days_since_initial_fill += 1
                
            # Compute the current mpr
            mpr = 1.0*total_pills_taken / days_since_initial_fill
            
            # If this is the last refill, check to see if we need 
            # to make an adherence prediction
            if (day in model_prediction_days) and make_prediction:
                # Record the mpr at 60, 90 and 120 days, in case we need to make a prediction  
                pMPR_yesno = adherence.predict(name, age, mpr, day) 
                            
            # If the number of available pills is less than zero, we have a gap
            if pills_available == 0 and day < nDays-1:
                mpr_tseries[name].append( "null" )
                gaps[name].append( [day, mpr] )
            else:
                mpr_tseries[name].append( [day, mpr] )
                
        if make_prediction:
            predictedMPR[name][0][0] = mpr_tseries[name][-1]
            predictedMPR[name][1][0] = mpr_tseries[name][-1]
            #predictedMPR[name][1][1] = mpr_tseries[name][-1][1]
                       
        for i in range(1,len(dates)):
            #q = refill_data[name][dates[i-1]]
            
            # Get the number of pills at the last refill
            q = npills[i-1]                        
            last = dates[i]                       
 
            gap = (dates[i] - dates[i-1]).days - q
            if gap > max_gap[name]:
                max_gap[name] = gap
                
        # flag=0: 30-day gaps; flag=1: predicted 1-year MPR<0.8;
        # flag=2: Actual 1-year MPR<0.8; flag=3: Predicted 1-year MPR>0.8;
        # flag=4: Actual 1-year MPR>0.8 
        if nDays < 60:
            flag = 5
        elif max_gap[name] > threshold:   # 30-day gaps
            flag = 0
        elif nDays>364 and mpr<0.8:     # actual mpr < 0.8
            flag = 1
        elif nDays<365 and mpr<0.8:     # predicted mpr < 0.8
            flag = 2
        elif nDays>364 and mpr>=0.8:     # actual mpr < 0.8
            flag = 3
        elif nDays<365 and mpr>=0.8:     # predicted mpr < 0.8
            flag = 4

        urlname = name.replace (" ", "%20")
        gap_flag.append([name, urlname, flag, first, last])
                       
    return gap_flag, gaps, mpr_tseries, refill_day, predictedMPR, actualMPR
    