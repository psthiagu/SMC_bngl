def simulate(yaml_dict, rr):
    import IPython 
    IPython.embed()
    res1 = rr.simulate(yaml_dict.get("start",0), yaml_dict.get("end",100),
                       yaml_dict.get("num", 100))
    # some complicated resetting
    pulled_anything = yaml_dict.get("anything")
    print(pulled_anything)
    return res1
