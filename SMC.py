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
from hyptester import HypothesisTester

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
        # TODO: What else do we need from data_options? any tolerances?
        # any other relevant options that needs passed in? 
        self.t2form = t2f.Train2Form(handler=self.configHandler) 
        self.formulas, self.dic_formulas = self.t2form.run()
        self.Simulator = SMCSimulator(self.dic_formulas, handler=self.configHandler)
        self.MC = ModelChecker(self.formulas)
        # determine hypothesis parameters
        alpha = 0.1
        alpha = float(alpha)/float(n)
        prob=0.9
        beta=0.1
        delta=0.05
        # the tester
        ht = HypothesisTester(prob, alpha, beta, delta)

    def _parse_args(self):
        '''
        Parses the arguments for our command line program
        '''
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('-c', '--config', dest='config_file', type=str, default="config.yaml",
                            help='Sets config yaml file')
        self.parser = parser
        self.args = self.parser.parse_args()

    def prune_result(self, mc_res):
        """
        First throw away some useless parts of the keys of mc_res
        
        """
        mc_res_prune = {}
        for v in list(mc_res.keys()):
            mc_res_prune[(v[1], v[2])] =  mc_res[v]
        return mc_res_prune


    def run(self):
        # Note, self.configHandler has all the estimation stuff 
        # that was given in the YAML file.
        res = self.Simulator.get_new_trajectory()
        # Now we need to check the results
        check = self.MC.modelcheck(res)
        # need to remove some unnecessary keys
        mc_res = self.prune_result(check)
        n = len(mc_res)
        current = list(mc_res.keys())
        Samples = {}
        NH = []
        AH = []
        for v in current:
            Samples[v] = []
        
        print("#############################")
        while len(current) > 0:
            print("Currently there are {} things left".format(len(current)))
            res = self.Simulator.get_new_trajectory()
            check = self.MC.modelcheck(res)
            mc_res = self.prune_result(check)
            for v in current:
                Samples[v].append(mc_res[v])
                test_res = ht.test(Samples[v])
                if test_res == 0:
                    NH.append(v)
                    current.remove(v)
                elif test_res == 1:
                    AH.append(v)
                    current.remove(v)
            print("Current null hyp: {}".format(NH))
            print("Current alt hyp: {}".format(AH))
            print("left over formulas: {}".format(current))
            print("#############################")
        J = float(len(NH))/float(n)
        # We need to determine what to do given NH/AH/J 
        return NH, AH, J

if __name__ == '__main__':
    S = SMC(cmdline=True)
    NH, AH, J = S.run()
    #print(mc_res)
