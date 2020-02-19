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
from libsbml import *

"""

class Train2Form:
    def __init__(self, fpath=None, w=0.05):
        '''
        Fpath and w are required arguments
        '''
        self.fpath = fpath
        self.w = w
        self._parse_args()
        self.cmdline = False
        # We assume if fpath is not given, we are running 
        # off of cmdline 
        if fpath == None:
            self.cmdline = True
            self.fpath = self.args.file_path
            self.w = self.args.tolerance

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
        
        dic = {}
        T = []
        for ifile, fpath in enumerate(N):
            fname = os.path.basename(fpath).replace(".csv", "")
            df = pd.read_csv(fpath)
            c = [0]
            # The first column containing the indices -if present- is dropped.
            df.drop(df.columns[c],axis=1, inplace=True)
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
       
        # extract the set of observables
        Obs = df_data.columns.tolist()[1:]
        #define the tolerance for each observable using the parameter w. In general this could be a dictionary.
        tol = {}
        for x in Obs:
            tol[x] = w
        return tol

    def trainingdata2formulas(self, df_data, tol):
       
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
    
    def save_res(self, to_save):
        with open(self.args.outfile, 'wb') as f:
            pickle.dump(to_save, f)
    
    
   
    
    def run(self):
        # first we get the file paths from the file_path 
        # given by the user
        files = self.get_files() 
        # TODO: Comment every line here to explain general program flow
        time , dic = self.all_times(files)
        time = [float(t) for t in time]
        df_data = self.data(files, dic, time) 
        w = self.w # TODO: What is this value and should we allow this to be set via the command line
        #T_response: Yes, it can be set for now via the command line. Eventually  it can be another .csv file since
        # we may want to specify different tolerances for different observables (and perhps even time points)
        tol = self.tolerance(df_data, w)    
        formulas, formulas_Obs = self.trainingdata2formulas(df_data, tol)
        #TODO: What do we want to save here? If this is a command line program it 
        # probably should save some result somewhere
        #T_response: Not necessary. A later script will use these lists.
        if self.cmdline:
            self.save_res((formulas, formulas_Obs))
        return formulas, formulas_Obs

"""

def extract_basic_species_names(bngl_file):
    with open (bngl_file, 'rt') as myfile:
        L = []
        for myline in myfile:
            L.append(myline)
    borders = [i for i in range(len(L)) if 'species' in L[i]]
    L_species = L[borders[0]+1: borders[1]]
    L_species = [tuple(l.split()) for l in L_species]
    N =  [L_species[i][0] for i in range(len(L_species)) if len(L_species[i]) > 0] 
    set_N = []
    for n in N:
        n = n.replace("(", ",")
        n = n.replace(")", "")
        X = set(n.split(","))
        set_N.append(X)
    return(set_N)
    
def backward_associations(xml_file, bngl_file):
        doc = readSBMLFromFile("comp31_sbml.xml")
        model = doc.getModel()
        S = model.species
        set_N = extract_basic_species_names(bngl_file)
        name2index = {}
        name2conc = {}
        for s in S:
            n = s.getName()
            m = n.replace("(", ",")
            m = m.replace(")", "")
            N = set(m.split(","))
            if N in set_N:
                name2index[n] = s.getId()
                name2conc[n] = s.getInitialConcentration()
        return (name2index,name2conc)

if __name__ == '__main__':
    
    xml_file = "comp31_sbml.xml"
    bngl_file = "comp31.bngl"
    #model = backward_associations(xml_file, sp, parm)
    name2index, name2conc = backward_associations(xml_file, bngl_file)