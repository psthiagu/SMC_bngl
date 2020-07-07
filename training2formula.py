#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 19:18:59 2019

@author: thiyagu
"""
from os import path
import pandas as pd
import matplotlib.pyplot as plt
import argparse, glob, os, sys, pickle


class Train2Form:
    def __init__(self, handler=None, fpath=None, w=0.05, cmdline=False, outfile="t2f_out.pickle"):
        '''
        Either handler or fpath and w are required arguments
        Handler will override other options. fpath default is "data" 
        w default is 0.05
        '''
        if cmdline: 
            self._parse_args()
            self.fpath = self.args.file_path
            self.w = self.args.tolerance
            self.outfile = self.args.outfile
        elif not (handler is None):
            self.configHandler = handler
            data_options = self.configHandler._config_dict.get("data_options")
            self.fpath = data_options.get("data_path", "data")
            self.w = data_options.get("w", 0.05)
        else:
            self.fpath = fpath
            self.w = w
            self.outfile = outfile

    def _parse_args(self):
        '''
        Parses the arguments for our command line program
        '''
        parser = argparse.ArgumentParser(description='Gets the training data?')
        parser.add_argument('-fp', '--fpath', dest='file_path', type=str, default=os.getcwd(),
                            help='Sets the file path to get the data files from')
        parser.add_argument('-w', '--tol', dest='tolerance', type=float, default=0.05,
                            help='Sets the tolerance')
        parser.add_argument('-o', '--output', dest='outfile', type=str, default='t2f_out.pickle',
                            help='Output file path')
       
        self.parser = parser
        self.args = self.parser.parse_args()
    
    def get_files(self, fmt=".csv"):
        '''
        Finds all the csv files in the given file path and returns the full 
        paths to each data file
        ''' 
        assert (self.fpath is not None) or self.fpath != "", \
                "No file path given which is required: {}".format(self.fpath)
        return glob.glob(self.fpath + "/*{}".format(fmt)) 
        
    def all_times(self, N):
        """Computes all the time points at which data is available and converts the data files to dataframes.
        
        
        The input N is a list of the names .csv files. Further the time scale is assumed to be common and named ('day') here though 'hour' 
        will be more appropriate. In fact 'time' will be a more appropriate neutral name.
        
        Parameters
        ----------
        N : list 
        
        A list of file names
        
        Returns
        -------
        T : list
        
        A sorted (ascending) list of time points at which experimental observations are available.
        
        dic : dictionary
        
        Gives for each file name an ordered pair; a dataframe representation of the data in the file and the 
        observable associated with the data.
        
        Raises
        ------
        
        I think it will be a good idea to ensure that all the dataframes have a common name for time.
        Also it might be worth checking that the names of the observables assembled from the data files match the names of 
        the observables in the bngl file (and hence in the list parameters in the sbml file). I ran into this problem much later and had to go back 
        to the data files to fix it.
        
        """
        dic = {}
        T = []
        for ifile, fpath in enumerate(N):
            fname = os.path.basename(fpath).replace(".csv", "")
            df = pd.read_csv(fpath)
            c = [0]
            # The first column containing the indices -if present- is dropped.
            # df.drop(df.columns[c],axis=1, inplace=True)
            C = df.columns.tolist()
            obs = C[-1]
            T.extend(df['day'].tolist())
            # in the example data set the time scale is reported as 'hour'
            T = list(set(T))
            dic[fname] = (df, obs)
            # the dictionary dic returns the mildly transformed individual csv files to make it more convenient 
            # for further processing.
        T.sort()
        return(T, dic)

    def data(self, N, dic, T):
        """Next we assemble the data into a single dataframe. 
        
        In this dataframe there will be one column 'time' containing all the 
        time points for which data is available. In addition there will be 
        one column corresponding to the observable mentioned 
        in each of the individula data files. If for a 'time' value no data is available for an observable 
        then we insert the default value '-1' for this 'time' value. As a result for each 'time' point each 
        observable will have a data value.
        
        Parameters
        ----------
        
        N: list
        
        As above.
        
        dic: dictionary
        
        As above
        
        T: list
        
        As above
        
        Returns
        -------
        
        df_data : dataframe
        
        The datfrme that contains all the data with a common time frame.
        
        """
        # df_data is the unified training dat file we want to assemble.
        df_data = pd.DataFrame()
        df_data['time'] = T
        for ifile, fpath in enumerate(N):
            fname = os.path.basename(fpath).replace(".csv", "")
            obs = dic[fname][1]
            # compute the data values for each time point in T for the observable in the daa file n (say, 'Tc4_B') in N.
            data_n = []
            df_n = dic[fname][0]
            day_n = df_n['day'].tolist()
            for i in range(len(T)):
                t_i = T[i]            
                if t_i in day_n:
                    j = day_n.index(t_i)
                    data_n.append(df_n.loc[j][1])
                else:
                    data_n.append(-1.0)
            df_data[obs] = data_n
        return(df_data)

    def tolerance(self, df_data, w):
        """The tolerance values to model noisy data.
        Each data point, when being compared to the value reported by a simulation, should be done with some tolerance.
        If the data point's value is v and its tolerance is \delta then we check if the reported value falls in
        the interval [v-\delta, v+\delta].
        
        To start with, we are assuming the tolerance for all the observables and all their data values are the same.
        Here we also assume that it is specified as a (small) percentage. Thus if w = 5% then the interval associated with v 
        is [v*19/20, v*21/20]
        
        Parameters
        ----------
        
        df_data : dataframe
        
        The assembled data; see above
        
        w : float
        
        The tolerance. Interpreted as a percentage. 
        
        Returns
        -------
        tol : dictionary
        
        Specifies for each observable its tolerance as a percentage.

        
        """
        # extract the set of observables
        Obs = df_data.columns.tolist()[1:]
        #define the tolerance for each observable using the parameter w. In general this could be a dictionary.
        tol = {}
        for x in Obs:
            tol[x] = w
        return tol

    def trainingdata2formulas(self, df_data, tol):
        """Converts the assembled data into BLTL formulas.
        
        If the observable x has the value v at time point t then this will be converted to the future 
        formula F^t(x \in [v-\delta, v+\delta]).
        
        Parameters
        ----------
        
        df_data : dataframe
        
        As above.
        
        tol: dictionary
        
        As above.
        
        Returns
        -------
        formulas : list
        
        A list of tuples of the form (F_eq, t, x, v, w). Such a tuple asserts that at exactly time t in 
        the future (hence F_eq) the reported value of x falls in the interval [v - \delta, v + \delta] where
        \delta = v * (w/100)
        
        formulas_Obs : dictionary
        
        The same information as in 'formulas' but organized as a dictionary. We are not sure which will be more 
        convenient to  work with and hence just  hedging our bets. Can easily eliminate one of them.
        
        """
        Obs = df_data.columns.tolist()[1:]
        formulas = []
        formulas_Obs = {x:[] for x in Obs}
        for i in range(len(df_data)):
            d = df_data.loc[i]
            for x in Obs:
                if d[x] >= 0:
                    formulas.append(('F_eq', d[0], x, d[x], tol[x]))
                    formulas_Obs[x].append(('F_eq', d[0], d[x], tol[x]))
        return formulas, formulas_Obs

    def save_res(self, to_save):
        """nothing much to say here.
        
        """
        with open(self.args.outfile, 'wb') as f:
            pickle.dump(to_save, f)

    def run(self):
        """don't know what to add here.
        
        """
    
        files = self.get_files() 
        time , dic = self.all_times(files)
        time = [float(t) for t in time]
        df_data = self.data(files, dic, time) 
        self.configHandler._data = df_data
        w = self.w 
        tol = self.tolerance(df_data, w)    
        formulas, formulas_Obs = self.trainingdata2formulas(df_data, tol)
        return formulas, formulas_Obs

if __name__ == '__main__':
    T2F = Train2Form(cmdline=True)
    f, fObs = T2F.run()
    T2F.save_res((f, fObs))
