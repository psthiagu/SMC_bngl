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
        data_options = self.configHandler._config_dict["data_options"]
        data_path = data_options["data_path"]
        w = data_options["w"]
        t = t2f.Train2Form(fpath=data_path, w=w)
        formulas, dic_formulas = t.run()
        self.Simulator = SMCSimulator(dic_formulas, handler=self.configHandler)
        return self.Simulator.simulate()

if __name__ == '__main__':
    S = SMC(cmdline=True)
    print(S.run())
