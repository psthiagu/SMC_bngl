def simulate(yaml_dict, rr):
    rr.selections = ["time", "x", "y1", "y2"]
    res1 = rr.simulate(yaml_dict.get("start",0), yaml_dict.get("end",100),
                       yaml_dict.get("num", 100))
    return res1

def simulate_para(yaml_dict, rr):
    rr.selections = ["time", "x", "y1", "y2"]
    res1 = rr.simulate(yaml_dict.get("start",0), yaml_dict.get("end",100),
                       yaml_dict.get("num", 100))
    return res1
