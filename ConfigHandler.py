#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 3 11:37:30 2020

@author: sinan
""" 

import yaml, sys, imp

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
        if files_dict is not None:
            self.est_parms = est_dict.get("est_parms", None)
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
        # setting libroadrunner type simulation
        start = sim_dict.get("start", 0)
        end   = sim_dict.get("end", 100)
        num   = sim_dict.get("num", 100)
        def simulate():
            return obj.simulator.simulate(start, end, num)
        setattr(obj, "simulate", simulate)

    def _set_bngl_simulate(self, sim_dict):
        raise NotImplemented

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
            return sim_func(sim_dict, obj)
        setattr(obj, "simulate", simulate)

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
