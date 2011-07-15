
# Imports
import datetime
import urllib
import readTable
import numpy as np
import numpy.random as random

# Global variables
ISO_8601_DATETIME = '%Y-%m-%d'


"""    
File: adherence_predict.py

    Written by: William J. Bosl
    Children's Hospital Boston Informatics Program
    300 Longwood Avenue
    Boston, MA 02115

    Description: This function takes a list of prescription fulfillment
    dates and checks for gaps larger than a specified threshold.

"""
class adherence_predict():
    
    def __init__(self, filename):
        # Get the data table from the given regression file
        try:
            reader = readTable.readTable(filename)
        except:
            print "Can't open file ", filename
            return
        self.data = reader.read()
    
    def predict(self, med_name, age, mpr, iday):
        
        # Initialize to null. This is the default case if none of the given
        # input parameters match the valid model parameters.
        threshold = 0.8     # Defined threshold for determining good or poor adherence
        adherence_warning = False   # By default, no warning is reported
        sday = str(iday)
        allowable_days = ['60', '90', '120']
        model_class = ["statins", "antih", "hypogly"]
        
        # Get the drug class from the drug name
        #drug_class = med_name
        r = random.randint(0,3)
        drug_class = model_class[r]
                
        if not (drug_class in model_class):
            print "med not allowable for adherence calculation"
            return adherence_warning
        elif not (sday in allowable_days):
            print "day not allowable for adherence calculation"
            return adherence_warning
                
        # Set up the regression coefficients. Age must be 60, 90 or 120 days
        # at this time.
        coeff = self.data[drug_class][sday]
        a = float(coeff[0])
        b = float(coeff[1])
        c = float(coeff[2])
        #accuracy = float(coeff[3])  # Not sure if we should do anything with this information now
                
        # Compute the logit function
        mpr = 0.4
        g = a + b*mpr + c*age
        exp_g = np.exp(-g)
        p = 1/(1.0 + exp_g)
                
        print "med: ", med_name.split()[0], "    p(%d,%f) = %f, " %(age,mpr, p)
        #print "med: ", med_name.split()[0], "mpr=%f, p=%f, pMPR=%f" %(mpr, p, pMPR)
        
        if p > 0.5:
            adherence_warning = True            
        
        return adherence_warning
    