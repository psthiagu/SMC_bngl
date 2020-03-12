#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: sinan
""" 

class ModelChecker:
    def __init__(self, formulas):
        self.formulas = formulas

    def modelcheck(self, res, formulas=None):
        """
        Here is a function which will check if a formula is satisfied by the current trajectory that is 
        represented by res_data (as in res, formulas = S.run() below). I am assuming that we will eventually 
        ensure that it will contain all the relevant time points. Currently it does not do so for two reasons:
        (1) We are not gathering the results of all the stages (2) Not all the time points mentioned in the formulas 
        appear in res_data['time']
        
        I will use dic_poisson to next update the SMC's hypothesis test.
        
        """
        if formulas is None:
            formulas = self.formulas

        dic_poisson = {}
        T = res['time'].tolist()
        for ob_name in formulas:
            ob_dict = formulas[ob_name]
            for tpts in ob_dict:
                feq, d0, dx, w = tpts
                if d0 in T:
                    i = T.index(d0)
                    if  res[ob_name].tolist()[i] - w <= dx and dx <= res[ob_name].tolist()[i] + w:
                        dic_poisson[ob_name] = 1
                    else:
                        dic_poisson[ob_name] = 0
        return dic_poisson
                
# if __name__ == '__main__':
#     S = SMC(cmdline=True)
#     res_data = S.run()
#     MC = ModelChecker(formulas=S.dic_formulas)
#     dic_poisson = MC.modelcheck(res_data)
#     print(dic_poisson)
    
    
    
