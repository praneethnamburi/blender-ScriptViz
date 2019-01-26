import inspect

def moduleParser(m): # m is a module
    report = {}
    []
    return 


def functionInputs(func):
    inputVarNames = [str(k) for k in inspect.signature(func).parameters.keys()]
    defaultValues = [inspect.signature(func).parameters[k].default for k in [str(k) for k in inspect.signature(func).parameters.keys()]]
    return inputVarNames, defaultValues

def getmembers(mod):
    members = {}
    for name, data in inspect.getmembers(mod):
        if name.startswith('__') or inspect.ismodule(data):
            continue
        members[name] = str(type(inspect.unwrap(data))).split("'")[1]
    return members

#[print(k, ':', str(type(getattr(bpn, k))).split("'")[1]) for k in dir(bpn)]