#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: sinan
""" 

import yaml, sys, argparse
import training2formula as t2f  
from simulate import SMCSimulator
from ConfigHandler import ConfigHandler
from SMC import SMC

"""
Here is a function which will check if a formula is satisfied by the current trajectory that is 
represented by res_data (as in res, formulas = S.run() below). I am assuming that we will eventually 
ensure that it will contain all the relevant time points. Currently it does not do so for two reasons:
(1) We are not gathering the results of all the stages (2) Not all the time points mentioned in the formulas 
appear in res_data['time']

I will use dic_poisson to next update the SMC's hypothesis test.

"""
def modelcheck(res, formulas):
    dic_poisson = {}
    T = res['time'].tolist()
    for f in formulas:
        ob = f[2]
        t = f[1]/24
        if t in T:
            
            i = T.index(t)
            if  res[ob].tolist()[i] - f[4]  <= f[3] and f[3] <= res[ob].tolist()[i] + f[4]:
                dic_poisson[f] = 1
            else:
                dic_poisson[f] = 0
    return dic_poisson
                
                
if __name__ == '__main__':
    
    S = SMC(cmdline=True)
    res_data, formulas = S.run()
    #dic_poisson  = modelcheck(res_data,formulas)
    
    
    
