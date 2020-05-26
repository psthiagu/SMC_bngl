#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 19:18:59 2019

@author: thiyagu
"""
import argparse, glob, os, pickle
import roadrunner
import training2formula as t2f  
import numpy as np
from os import path
from libsbml import *
from ConfigHandler import ConfigHandler

class SMCSimulator:
    def __init__(self, dic_formulas, config_file=None, handler=None):
        if config_file is not None:
            # Parse config file here
            self.configHandler = ConfigHandler(config_file)
        elif handler is not None:
            self.configHandler = handler
        else:
            print("no way to get config file specified")
            sys.exit()
        # use parsed configs
        self.dic_formulas = dic_formulas
        self.times = self.get_times_from_formulas(dic_formulas)
        # TODO: the times are not accurate right now
        # remove this once it's fixed
        self.times = np.array(self.times)/60.0
        self.xml_file = self.configHandler.xml_file
        self.bngl_file = self.configHandler.bngl_file
        self.name2id = self.backward_associations(self.xml_file, self.bngl_file)
        # parameters to estimate
        self.est_parms = self.configHandler.est_parms
        # set the simulation command using the info from the config file
        self.configHandler.set_simulate_command(self)
        # TODO: This is a bit much, we might want to figure out a nicer
        # way to pull all this out or maybe we want to do this internally 
        # instead of explicitly
        self.simulator, self.species_index, self.est_parms_index, \
                self.obs_index = self.initialize_rr(self.xml_file, \
                        self.name2id, self.est_parms, self.dic_formulas)
        if self.configHandler.obs_list is not None:
            # sel = self.simulator.timeCourseSelections
            # self.simulator.timeCourseSelections = sel + self.configHandler.obs_list
            conv_obs_list = []
            rev_obs_list  = []
            flt_names = map(lambda x: "["+x+"]", self.floating_ids)
            for elem in self.configHandler.obs_list:
                rev_obs_list.append(elem)
                if elem in self.name2id.keys():
                    conv_obs_list.append("["+self.name2id[elem]+"]")
                elif hasattr(self.simulator, elem) or (elem in flt_names) or elem == "time":
                    conv_obs_list.append(elem)
                else:
                    print("observable {} is neither in species conversion table nor in roadrunner object".format(elem))
            if "time" not in conv_obs_list:
                conv_obs_list = ["time"] + conv_obs_list
                rev_obs_list  = ["time"] + rev_obs_list
            try:
                self.simulator.timeCourseSelections = conv_obs_list
            except RuntimeError:
                print("an element in the observables list doesn't match with roadrunner simulator. given list after attempting to convert: {}".format(conv_obs_list))
            self.conv_obs_list = conv_obs_list
            self.rev_obs_list = rev_obs_list

    def get_times_from_formulas(self, formulas):
        all_times = []
        for key in formulas:
            formula = formulas[key]
            formula_times = list(map(lambda x: x[1], formula))
            all_times += formula_times
        times = sorted(list(set(all_times)))
        return times

    def extract_basic_species_names(self, bngl_file):
        """get the species mentioned in the bngl model
        
        Parameters
        ----------
        
        bngl_file: txt file
        
        Contains the bngl model.
        
        Returns
        -------
        set_N : list
        
        The list of species names but where the name is broken down into its set of components. This is needed for 
        matching the species names in the sbml file where the components of a name are often arranged in a different order.
        
        """
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
        
    def backward_associations(self, xml_file, bngl_file):
        """Establishes a link  between the species names in the bngl file and the corresponding ids in the sbml file.
        
        Parameters
        ----------
        
        xml_file : The xml file corresponding to the bngl model. here it is generated by the bngl tool.
        
        bngl_file : text file
        
        As before.
        
        Returns
        -------
        
        name2index : dictionary
        
        Each species name in the bngl model is assigned its corresponding id in the sbml file.
        
        name2conc : dictionary
        
        Each name 
        
        """
        
        doc = readSBMLFromFile("comp31_sbml.xml")
        model = doc.getModel()
        S = model.species
        set_N = self.extract_basic_species_names(bngl_file)
        name2index = {}
        for s in S:
            n = s.getName()
            m = n.replace("(", ",")
            m = m.replace(")", "")
            N = set(m.split(","))
            if N in set_N:
                name2index[n] = s.getId()
        return (name2index)
    
    def initialize_rr(self, xml_file, name2index, est_parms, dic_formulas):
        """Extract from the sbml file the indices of the species, parameters and observables.
        
        For each simulation run we will be supplying new initial sampled initial concentrations of the species.
        We will also be supplying sampled values for the parameters to be estimated. Finally we will want to 
        extract the reported values of the observables from the results of the simulation.
        
        Parameters
        ----------
        
        xml_file : text file
        
        As before
        
        name2index : dictionary
        
        As before
        
        est_parms : list
        
        The list of parameters to be estimated. This is the tricky one. Here I have hard-wired it just in 
        order to be able to run everything.
        
        dic_formulas: dictionary
        
        The dictionary which assigns to each observable a list of future formulas; one for each time point at 
        which there is data for the observable. Used merely to extract the observables.
        
        Returns
        -------
        
        I : list
        
        The list of floating species Ids extracted from the sbml model. This is
        probably not necessary. Will prune later.
        
        parms: list
        
        This is the list of all parameters extracted from the sbml model.
        
        species_index : dictionary
        
        Assigns the index of the id in the sbml model to the species name in the bngl model.
        
        species_conc : dictionary
        
        Assigns to a species its the initial concentration.
        
        params_index : dictionary
        
        Assigns to each parameter to be estimated its index in the list of all the parameters in the sbml model.
        
        obs_index : dictionary
        
        Assigns to each observable its in the in the list all parmeters in the sbml model.
        
        """
        rr = roadrunner.RoadRunner(xml_file)
        m = rr.model
        I = m.getFloatingSpeciesIds()
        # setting this here
        self.floating_ids = I
        C = m.getFloatingSpeciesConcentrations()
        species_index = {}
        species = name2index.keys()
        species_conc = {}
        for s in species:
            species_index[s] = I.index(name2index[s])
            species_conc[s] = C[species_index[s]]
        # 
        self.spec_conc = species_conc
        # 
        P = m.getGlobalParameterIds()
        # setting this here
        self.param_ids = P
        
        parms_index = {}
        for p in est_parms:
            parms_index[p] =  P.index(p)
        
        obs = dic_formulas.keys()
        
        obs_index = {}
        for o in obs:
            obs_index[o] =  P.index(o)        

        self.init_ids = []
        for init_id in rr.getFloatingSpeciesInitialConcentrationIds():
            iid = init_id.replace("init([","")
            iid = iid.replace("])", "")
            self.init_ids.append((iid,init_id))
        
        return (rr, species_index, parms_index, obs_index)

    def simulate(self):
        res = self._simulate()
        if hasattr(self, "conv_obs_list"):
            if len(res.dtype.names) == len(self.conv_obs_list):
                new_dtype = [(i,"float64") for i in self.rev_obs_list]
                res = np.array(res, dtype=new_dtype)
                # res.colnames = self.rev_obs_list
        return res

    def sample_vals(self, per):
        # let's get the initial values +- %5
        new_vals = {}
        for fid,init_id in self.init_ids:
            init_val = self.simulator[init_id]
            delta = init_val * per # 5% of the initial value
            val_sample = np.random.uniform(init_val-delta, high=init_val+delta)
            new_vals[fid] = val_sample # adding new value to dictionary
        # parameter values
        for param in self.est_parms:
            pval = self.simulator[param]
            delta = pval * 0.05 # 5% of the current parameter value
            val_sample = np.random.uniform(pval-delta, high=pval+delta)
            new_vals[param] = val_sample
        return new_vals

    def set_values(self, values):
        for name in values:
            self.simulator[name] = values[name]

    def reset_simulator(self, values=None):
        if values is None:
            self.simulator.resetAll()
        else:
            # TODO: Only reset values here
            raise NotImplemented

    
if __name__ == '__main__':
    t = t2f.Train2Form(fpath="data",w=0.1)
    formulas, dic_formulas = t.run()
    config_file = "config.yaml"
    Sim = SMCSimulator(dic_formulas, config_file=config_file)
    print(Sim.simulate())
