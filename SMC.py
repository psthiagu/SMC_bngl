#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: sinan
""" 

import yaml, sys, argparse
import training2formula as t2f  
import numpy as np
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
        self.fail_rates = []
        self.call_counts = [] 

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


    def run(self, values):
        # Note, self.configHandler has all the estimation stuff 
        # that was given in the YAML file.
        # print("#############################")
        print("values: {}".format(values))
        self.Simulator.reset_simulator()
        self.Simulator.set_curr_params(values)
        orig_res, fail_rate = self.Simulator.get_new_trajectory()
        self.fail_rates.append(fail_rate)
        # Now we need to check the results
        check = self.MC.modelcheck(orig_res)
        # need to remove some unnecessary keys
        mc_res = self.prune_result(check)
        n = len(mc_res)
        # determine hypothesis parameters
        alpha = 0.1
        alpha = float(alpha)/float(n)
        prob=0.9
        beta=0.1
        delta=0.05
        # the tester
        ht = HypothesisTester(prob, alpha, beta, delta)
        current = list(mc_res.keys())
        Samples = {}
        NH = []
        AH = []
        for v in current:
            Samples[v] = []
        
        ctr = 0 
        # print("#############################")
        while len(current) > 0:
            ctr += 1
            res, fail_rate = self.Simulator.get_new_trajectory()
            self.fail_rates.append(fail_rate)
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
            # print("Current null hyp: {}".format(NH))
            # print("Current alt hyp: {}".format(AH))
            # print("left over formulas: {}".format(current))
            # print("#############################")
        J = float(len(NH))/float(n)
        # We need to determine what to do given NH/AH/J 
        print("Values: {}".format(values))
        print("Result NH: {}, AH: {}, J: {}, fitness: {}".format(NH, AH, J, (1.0-J)))
        curr_fail_rates = np.array(self.fail_rates)
        print("current fail rate mean: {} std: {}, len: {}".format(curr_fail_rates.mean(), curr_fail_rates.std(), len(curr_fail_rates)))
        self.call_counts.append(ctr)
        curr_call_cts = np.array(self.call_counts)
        print("call count: {}, mean: {}, std: {}".format(ctr, curr_call_cts.mean(), curr_call_cts.std()))
        return orig_res, NH, AH, J

if __name__ == '__main__':
    S = SMC(cmdline=True)
    vals = dict([(S.configHandler.est_parms[i], getattr(S.Simulator.simulator, S.configHandler.est_parms[i])) for i in range(len(S.configHandler.est_parms))])
    NH, AH, J = S.run(vals)
    print(NH, AH, J)
