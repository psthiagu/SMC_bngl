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
from modelcheck import ModelChecker

class SMC:
    def __init__(self, config_file=None, cmdline=False):
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
        self.MC = ModelChecker(self.formulas)
        check = self.MC.modelcheck(res)
        # TODO: reset simulator, note that specific value 
        # resetting is not implemented yet
        # e.g. self.Simulator.reset_simulator()
        # Not implemented: self.Simulator.reset_simulator(["stuff"])
        return check, res

if __name__ == '__main__':
    S = SMC(cmdline=True)
    mc_res, res = S.run()
    #print(mc_res)
