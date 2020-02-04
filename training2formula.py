#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 19:18:59 2019

@author: thiyagu
"""
from os import path
import pandas as pd
import matplotlib.pyplot as plt

"""
The all_time function computes all the time points at which data is available.
The input N is a list of the names .csv files. Here these csv files are assumed to be in the current folder 
from which the function is being called. Further the time scale is assumed to be common and named ('hour', 'day' etc) 
in the same way in all the csv files. In the particular data sets I am using here the time scale is 'hour'. Perhaps this 
should be changed to a neutral name like 'time'.

The output is a a list T of time points and dic, a dictionary that contains the csv files converted to dataframes , the name 
of the associated observable. mildly processed (drop the index column) to prepare them for further processing.
"""

def all_times(N):
    dic = {}
    T = []
    for i in range(len(N)):
        df = pd.read_csv(N[i]+'.csv')
        c = [0]
        # The first column containing the indices -if present- is dropped.
        df.drop(df.columns[c],axis=1, inplace=True)
        C = df.columns.tolist()
        obs = C[-1]
        T.extend(df['hour'].tolist())
        # in the example data set the time scale is reported as 'hour'
        T = list(set(T))
        dic[N[i]] = (df, obs)
        # the dictionary dic returns the mildly transformed individual csv files to make it more convenient 
        # for further processing.
    T.sort()
    return(T, dic)

"""
Next we assemble the data into a single dataframe. In this dataframe there will be one column 'time' containing all the 
time points for which data is available. In addition there will be one column corresponding to the observable mentioned 
in each of the individula data files. In the current example for instance, the B4.csv file's observable is 'Tc4_B'. 
Then for each time point t in the list T. In the column corresponding to the observable, say, 'Tc4_B', we insert the kth entry to be 
'd' if 'd' has been obseved to be the value of this observable at time T[k]. If there is no data at this time point for the observable, the entry 
is fixed to be '_1.0' which will be treated as "no data" later.
"""
def data(N, dic, T):
    # df_data is the unified training dat file we want to assemble.
    df_data = pd.DataFrame()
    df_data['time'] = T
    for n in N:
        obs = dic[n][1]
        # compute the data values for each time point in T for the observable in the daa file n (say, 'Tc4_B') in N.
        data_n = []
        df_n = dic[n][0]
        day_n = df_n['hour'].tolist()
        for i in range(len(T)):
            t_i = T[i]            
            if t_i in day_n:
                j = day_n.index(t_i)
                data_n.append(df_n.loc[j][1])
            else:
                data_n.append(-1.0)
        df_data[obs] = data_n
    return(df_data)

"""
We next convert the training data to a set of BLTL (Bounded Linear Time Logic) formulas.
Since we are converting just time course data we just need future formulas of the form F^{t} (x \in I).
This formula says that the value of the variable x was observed to fall in the interval I at time t.

Here I is an interval around the reported value v. It will be of the form [v-\delta, v+\delta] where \delata is a 
user supplied tolerance value. It is usually specified as a percentage of the reported data value. Thus with tolerance chosen 
as 5%, I will be set to [v*19/20, v*21/20].

We begin with a specification of such intervals, It will be easy to expnad this specification should the need arise.

"""
def tolerance(df_data, w):
    # extract the set of observables
    Obs = df_data.columns.tolist()[1:]
    #define the tolerance for each observable using the parameter w. In general this could be a dictionary.
    tol = {}
    for x in Obs:
        tol[x] = w
    return tol
    
    

"""
In the future I want to be able to add other kinds of properties for model checking and parameter estimation.

Hence I want to represent the current training data in a more elaborate fashion. 

First we unpack the training data to generate the observables and their relevant time points. This may seem silly because this is the information 
contained in the individual data files. But I don't want to make any assumptions about how the training data was prepared other than the 
convetions assumed in df_data 

"""


def trainingdata2formulas(df_data, tol):
    Obs = df_data.columns.tolist()[1:]
    # We convert all the data points into formulas. For convenience we also encode this 
    # information as a dictionary in which each observable has a set of formulas assigned to it.
    formulas = []
    formulas_Obs = {x:[] for x in Obs}
    for i in range(len(df_data)):
        d = df_data.loc[i]
        for x in Obs:
            if d[x] >= 0:
                formulas.append(('F_eq', d[0], x, d[x], tol[x]))
                # The above entry denotes at exactly d[0 time units in the future the observable x will have a value 
                # that lies in the interval [d[x]-tol[x], d[x]+tol[x]]
                formulas_Obs[x].append(('F_eq', d[0], d[x], tol[x]))
                # the same information is coded above but this time for each observable.
    return formulas, formulas_Obs
    



if __name__ == '__main__':
    N_files = ['pk', 'B4', 'B8', 'Bleuk', 'BM4', 'BM8', 'BMleuk',  'IFNg', 'IL2', 'IL6', 'IL10']
    time , dic = all_times(N_files)
    time = [float(t) for t in time]
    df_data = data(N_files, dic, time) 
    w = 5/100
    tol = tolerance(df_data, w)    
    formulas, formulas_Obs = trainingdata2formulas(df_data, tol)
    
    
    
    
    
    
    





