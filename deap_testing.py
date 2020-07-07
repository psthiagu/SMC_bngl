#!/usr/bin/env python
# coding: utf-8

import pyDOE
import numpy as np
import roadrunner as RR
import pandas as pd
import seaborn as sbrn
import matplotlib, pyDOE
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from sklearn.decomposition import PCA
from scipy.stats.distributions import norm

import random

from deap import base
from deap import creator
from deap import tools

from SMC import SMC
import h5py, os


s = SMC(config_file="config_thiagu.yaml")

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

# this is the initialization of the parameters,
# a latin hypercube sampling, gaussians centered 
# on original values with scale determines the 
# sigma
def gen_normal_params():
    ndim = len(s.configHandler.est_parms)
    # means = [getattr(s.Simulator.simulator, rate_name) for rate_name in s.configHandler.est_parms]
    means = np.array([getattr(s.Simulator.simulator, rate_name) for rate_name in s.configHandler.est_parms])
    means = np.log(means)
    means[np.isinf(means)] = 0.0
    sample = list(means)
    for i in range(ndim):
        sigma = means[i]*0.20
        new_val = random.gauss(means[i], sigma)
        sample[i] = np.exp(new_val)
    return sample

def gen_params():
    ndim = len(s.configHandler.est_parms)
    scale = 5
    sample = pyDOE.lhs(ndim, samples=1)
    means = [getattr(s.Simulator.simulator, rate_name) for rate_name in s.configHandler.est_parms]
    log = False
    if not log:
        for i in range(ndim):
            sample[:, i] = abs(norm(loc=means[i]+scale, scale=scale).ppf(sample[:, i]))
    else:
        means = np.log(means)
        for i in range(ndim):
            sample[:, i] = abs(norm(loc=means[i]+scale, scale=scale).ppf(sample[:, i]))
            sample = np.exp(sample)
    return list(sample[0])

def get_curr_params():
    means = [getattr(s.Simulator.simulator, rate_name) for rate_name in s.configHandler.est_parms]
    return list(means)

toolbox = base.Toolbox()
# Structure initializers
toolbox.register("individual", tools.initIterate, creator.Individual, gen_normal_params)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalInd(individual):
    # print("selecting values")
    vals = dict((s.configHandler.est_parms[i],individual[i]) for i in range(len(individual)))
    # calculate fitness given result and return tuple
    # print("running SMC")
    NH, AH, J = s.run(vals)
    # J is max 1 and means that everything fits
    fitness = 1.0 - J
    # print("returning fitness")
    return fitness,

def cxOrderedSameLen(ind1, ind2):
    size = min(len(ind1), len(ind2))
    a, b = random.sample(range(size), 2)
    if a > b:
        a, b = b, a

    # Swap the content between a and b (included)
    for i in range(a, b + 1):
        ind1[i], ind2[i] = ind2[i], ind1[i]

    return ind1, ind2

def mutGaussianKeepMeans(individual, indpb, sigma_perc):
    size = len(individual)
    mu = np.log(np.array(individual))
    mu[np.isinf(mu)] = 0.0
    sigma = [i*sigma_perc for i in mu]
    
    for i, me, si in zip(range(size), mu, sigma):
        if random.random() < indpb:
            new_val = random.gauss(me,si)
            individual[i] = np.exp(new_val)
    return individual,


toolbox.register("evaluate", evalInd)
toolbox.register("mate", cxOrderedSameLen)
toolbox.register("mutate", mutGaussianKeepMeans, indpb=0.05, sigma_perc=0.20)
toolbox.register("select", tools.selTournament, tournsize=3)


def main():
    if os.path.isfile("results.h5"):
        os.remove("results.h5")
    h = h5py.File("results.h5", "w")
    pop = toolbox.population(n=50)
    init_group = h.create_group("initial_population")
    init_group.create_dataset("pop", data=pop)
    # Evaluate the entire population
    print("Evaluating initial population")
    fitnesses = []
    for ip,p in enumerate(pop):
        print("evaluating individual {}".format(ip))
        fitnesses.append(toolbox.evaluate(p))
    init_group.create_dataset("fit", data=fitnesses)
    # fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    # CXPB  is the probability with which two individuals
    # are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB = 0.5, 0.5
    # Extracting all the fitnesses of 
    fits = [ind.fitness.values[0] for ind in pop]
    # Variable keeping track of the number of generations
    g = 0
    
    # Begin the evolution
    iterations = h.create_group("iterations")
    while max(fits) > 1e-3 and g < 100:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)
        iter_group = iterations.create_group("iter_{0:08d}".format(g))
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = []
        for ip,p in enumerate(invalid_ind):
            print("evaluating individual {}".format(ip))
            fitnesses.append(toolbox.evaluate(p))
        # fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        pop[:] = offspring
        # save
        iter_group.create_dataset("pop", data=offspring)
        iter_group.create_dataset("fit", data=fitnesses)
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5
        
        print("  Min %s" % min(fits))
        print("  Max %s" % max(fits))
        print("  Avg %s" % mean)
        print("  Std %s" % std)
        if max(fits) < 1e-3:
            break
        if std < 1e-6:
            break
        # if std < 1e-6:
        #    break
    return pop, fits


p, f = main()

print("fits: {}".format(f))
print("pops: {}".format(p))

# h = h5py.File("results.h5","r")
# p = h['iterations/iter_{:08d}/pop'.format(3)]
# f = h['iterations/iter_{:08d}/fit'.format(3)][:,0]
# p_best = np.where(f == f.max())[0][0]
# vals = dict((s.configHandler.est_parms[i],p_best[i]) for i in range(len(p_best)))
# s.Simulator.set_values()
# s.simulate()

# for cname in res.colnames:
#     if cname != "time":
#         sbrn.lineplot(res['time'], res[cname], label=cname)
# plt.legend(frameon=False)
# plt.xlabel("time")
# plt.ylabel("species conc")
# plt.savefig("spec_conc.png")

# log = False
# pop = toolbox.population(n=1000)
# # this allows us to take a look at the sample 
# # distributions 
# fig = figure(figsize=(10,5))
# ax = fig.gca()
# # turn into dataFrame, seaborn likes it
# if log: 
#     df = pd.DataFrame(np.log(pop), columns=s.configHandler.est_parms)
# else:
#     df = pd.DataFrame(pop, columns=s.configHandler.est_parms)
# # use seaborn to plot onto the axis
# sbrn_ax = sbrn.violinplot(data=df, ax=ax, color="0.7")
# sbrn_ax.set_xticklabels(sbrn_ax.get_xticklabels(), rotation=30, ha="right")
# sbrn_ax.set_ylim((0,200))
# sbrn_ax.set_xlabel("parameter")
# # 
# if log:
#     sbrn_ax.set_ylabel("log param value")
# else:
#     sbrn_ax.set_ylabel("param value")
