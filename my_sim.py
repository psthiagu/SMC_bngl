def simulate(sim_dict, smc_sim):
    rr = smc_sim.simulator
    print(sim_dict)
    return rr.simulate(0,100,100)
