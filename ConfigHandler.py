#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: sinan
""" 

import yaml, sys, imp
import numpy as np

class ConfigHandler:
    def __init__(self, config_file):
        with open(config_file, "r") as f:
            self._config_dict = yaml.full_load(f)
        self._set_properties()

    def _set_properties(self):
        files_dict = self._config_dict.get("files", None)
        if files_dict is not None:
            self.xml_file = files_dict.get("xml_file", None)
            self.bngl_file = files_dict.get("bngl_file", None)
        else:
            # TODO: Error out nicely
            print("Files need to be defined in the configuration file")
            sys.exit()
        est_dict = self._config_dict.get("estimation_options", None)
        if est_dict is not None:
            self.est_parms = est_dict.get("est_parms", None)
            self.obs_list = est_dict.get("observables", None)
        else:
            # TODO: Error out nicely or add logical defaults
            print("We need estimation options to be set")
            sys.exit()

    @property
    def xml_file(self):
        return self._xml_file

    @xml_file.setter
    def xml_file(self, path):
        self._xml_file = path

    @property
    def bngl_file(self):
        return self._bngl_file

    @bngl_file.setter
    def bngl_file(self, path):
        self._bngl_file = path

    @property
    def est_parms(self):
        return self._est_parms

    @est_parms.setter
    def est_parms(self, values):
        self._est_parms = values

    @property
    def obs_list(self):
        return self._obs_list

    @obs_list.setter
    def obs_list(self, values):
        self._obs_list = values

    def set_simulate_command(self, obj):
        # given the simulator class, we need to set the simulate command
        sim_dict = self._config_dict.get("simulation_options", None)
        if sim_dict is not None:
            # set according to type
            sim_type = sim_dict.get("type", "librr_sim")
        else:
            # TODO: Error out nicely or add logical defaults
            print("We need simulation options")
            sys.exit()
        if sim_type == "librr_sim":
            self._set_librr_simulate(sim_dict, obj)
        elif sim_type == "from_bngl":
            self._set_bngl_simulate(sim_dict, obj)
        elif sim_type == "from_python":
            self._set_python_simulate(sim_dict, obj)
        else:
            print("unknown simulation type")
            sys.exit()

    def _set_librr_simulate(self, sim_dict, obj):
        '''
        this is the basic way to setup a simulation
        loads in either start/end/num to run the libroadrunner
        simultor or runs multiple stages if "stages" is given 
        in the YAML file.
        '''
        # setting libroadrunner type simulation
        stages = sim_dict.get("stages", None)
        if stages:
            def simulate():
                # TODO: this needs optimized, by a lot. 
                # issue: stacking will copy the arrays, so it's memory inefficient
                # solution: pre-allocate an array first, then run the simulations
                ctr = 0
                for stage in sorted(stages):
                    print("Running stage {}".format(stage))
                    stage_dict = stages[stage]
                    param_sets = stage_dict.get("params",None)
                    if param_sets:
                        # set parameters
                        for param in param_sets:
                            print("setting paramter {} to {}".format(param, param_sets[param]))
                            setattr(obj.simulator, param, param_sets[param])
                    num = stage_dict.get("num", 100)
                    if stage_dict.get("sim_len",None):
                        sim_len = stage_dict.get("sim_len")
                        start = end
                        end += sim_len
                    else:
                        start = stage_dict.get("start", 0)
                        end   = stage_dict.get("end", 100)
                    print("simulating start {}, end {}, num pts {}".format(start, end, num))
                    if ctr > 0:
                        new_res = obj.simulator.simulate(start, end, num)
                        stacked = np.vstack([result, new_res])
                        result = stacked 
                        print(stacked.shape)
                    else:
                        result = obj.simulator.simulate(start, end, num)
                        cnames = result.colnames
                    ctr += 1
                print(stacked.shape)
                stacked = list(map(tuple, stacked))
                dtype = list(zip(cnames, ["float64" for i in range(len(cnames))]))
                return np.array(stacked, dtype=dtype)
        else:
            start = sim_dict.get("start", 0)
            end   = sim_dict.get("end", 100)
            num   = sim_dict.get("num", 100)
            def simulate():
                return obj.simulator.simulate(start, end, num)
        setattr(obj, "_simulate", simulate)

    def _set_python_simulate(self, sim_dict, obj):
        """
        sets the object.simulate function from a loaded 
        function that takes in sim_dict and the SMCSimulator 
        object as arguments
        """
        # TODO: add option to specify the path on top 
        # of the module.function spec
        func_path = sim_dict.get("function")
        sim_func = self._load_function(func_path)
        def simulate():
            return sim_func(sim_dict, obj.simulator)
        setattr(obj, "_simulate", simulate)

    def _load_function(self, func_path):
        """
        load function from module.function spec
        """
        splt = func_path.split(".")
        assert len(splt) == 2, "Function needs to be given in format file.function"
        fname, func_name = splt
        fpath, pname, desc = imp.find_module(fname)
        mod = imp.load_module(fname, fpath, pname, desc)
        func = getattr(mod, func_name)
        return func

    def _set_bngl_simulate(self, sim_dict):
        '''
        load in the BNGL file and parse the action block
        to set the simulate command
        '''
        raise NotImplemented

