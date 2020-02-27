#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 19:18:59 2019

@author: thiyagu
"""
from os import path
import pandas as pd
import matplotlib.pyplot as plt
import argparse, glob, os, sys, pickle
from libsbml import *
import roadrunner
import sys
import json
import training2formula as t2f  


def extract_basic_species_names(bngl_file):
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
    
def backward_associations(xml_file, bngl_file):
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
    set_N = extract_basic_species_names(bngl_file)
    name2index = {}
    for s in S:
        n = s.getName()
        m = n.replace("(", ",")
        m = m.replace(")", "")
        N = set(m.split(","))
        if N in set_N:
            name2index[n] = s.getId()
    return (name2index)
    
def initialize_rr(xml_file, name2index, est_parms, dic_formulas):
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
    C = m.getFloatingSpeciesConcentrations()
    species_index = {}
    species = name2index.keys()
    species_conc = {}
    for s in species:
        species_index[s] = I.index(name2index[s])
        species_conc[s] = C[species_index[s]]
    
    P = m.getGlobalParameterIds()
    
    parms_index = {}
    for p in est_parms:
        parms_index[p] =  P.index(p)
    
    obs = dic_formulas.keys()
    
    obs_index = {}
    for o in obs:
        obs_index[o] =  P.index(o)        
    
    return (I, P, species_index, species_conc, parms_index, obs_index)

#def simulate(m, name2index,new_conc, new_parms):
    
    

if __name__ == '__main__':
    # sysargv[1] to be supplied as "list"
    t = t2f.Train2Form(fpath="data",w=0.1)
    formulas, dic_formulas = t.run()
    est_parms = ["k_LeukB_log","k_LeukBM_log", "kf", "nb", "k4_act","k8_act", "k_tcb", "k4_ex", "k8_ex", "k4_kill","k8_kill", \
                 "k4_tox", "k8_tox", "k_adh", "k_migrate_B", "k_migrate_BM", "kf_ifng", "kr_ifng", "kf_il2", "kr_il2", \
                 "kf_il6", "kr_il6", "kf_il10", "kr_il10"]
    xml_file = "comp31_sbml.xml"
    bngl_file = "comp31.bngl"
    #model = backward_associations(xml_file, sp, parm)
    name2id = backward_associations(xml_file, bngl_file)
    
    I, parms, species_index, species_conc, est_parms_index, obs_index  = initialize_rr(xml_file, name2id, est_parms,dic_formulas)
    #print(m)
    