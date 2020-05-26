#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: sinan
""" 

import yaml, sys, argparse, numpy
import training2formula as t2f  
from simulate import SMCSimulator
from ConfigHandler import ConfigHandler
from modelcheck import ModelChecker

class SMC:
    def __init__(self, config_file=None, cmdline=False):
        '''
        Designed work as either a command line tool 
        or loaded in as a library. 

        If using the command line mode, be sure to include a 
        config file via the -c option. If loaded in, be sure
        to point to the correct config file via the 
        config_file keyword argument.

        '''
        if cmdline: 
            self._parse_args()
            self.configHandler = ConfigHandler(self.args.config_file)
        else:
            self.configHandler = ConfigHandler(config_file)

    def _parse_args(self):
        '''
        Parses the arguments for our command line program
        '''
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('-c', '--config', dest='config_file', type=str, default="config.yaml",
                            help='Sets config yaml file')
        self.parser = parser
        self.args = self.parser.parse_args()

    def run(self):
        # TODO: What else do we need from data_options? any tolerances?
        # any other relevant options that needs passed in? 
        self.t2form = t2f.Train2Form(handler=self.configHandler) 
        self.formulas, self.dic_formulas = self.t2form.run()
        self.Simulator = SMCSimulator(self.dic_formulas, handler=self.configHandler)
        # Note, self.configHandler has all the estimation stuff 
        # that was given in the YAML file.
        res = self.Simulator.simulate()
        # Now we need to check the results
        self.MC = ModelChecker(self.formulas)
        check = self.MC.modelcheck(res)
        # let's get the initial values +- %5
        new_vals = {}
        for fid,init_id in self.Simulator.init_ids:
            init_val = self.Simulator.simulator[init_id]
            delta = init_val * 0.05 # 5% of the initial value
            val_sample = numpy.random.uniform(init_val-delta, high=init_val+delta)
            new_vals[fid] = val_sample # adding new value to dictionary
        # parameter values
        for param in self.configHandler.est_parms:
            pval = self.Simulator.simulator[param]
            delta = pval * 0.05 # 5% of the current parameter value
            val_sample = numpy.random.uniform(pval-delta, high=pval+delta)
            new_vals[param] = val_sample
        # we first reset to the initial state
        self.Simulator.reset_simulator()
        # set the values 
        self.Simulator.set_values(values=new_vals)
        new_res = self.Simulator.simulate()
        import IPython;IPython.embed()

if __name__ == '__main__':
    S = SMC(cmdline=True)
    res = S.run()
    #print(mc_res)
