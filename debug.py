def IR(ir : list):
    for context in ir:
        print(context.name+":")
        for pseudo in context.data:
            pseudo.Format()
        print()

def printMapping(mapping : list["Mapping"]):
    for map in mapping:
        print(f"[{map.index.index}]")
        for usepack in map.map:
            print(f"  {usepack.purpose} {[reg.name for reg in usepack.registers]}")

def Prepare(any):
    if not isinstance(any, str): any = any.__class__.__name__
    return any

def CWarninig(any):
    print(fr"|||WRN||| {Prepare(any)}")

def CInfo(any):
    print(fr"///INF\\\ {Prepare(any)}")

def CError(any):
    print(fr"<<<ERR>>> {Prepare(any)}")


class Error():
    def __init__(self, message : str):
        self.message = message

class BackendASMError(Error):
    def __init__(self, message):
        super().__init__(message)

class SyntaxError(Error):
    def __init__(self, message):
        super().__init__(message)

class TypeError(Error):
    def __init__(self, message):
        super().__init__(message)

def Abort(err : Error):
    print(f"        {err.__class__.__name__}:\n            {err.message}")
    exit()