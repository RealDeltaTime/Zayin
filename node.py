import debug
import meta
import tokenizer

class Node:
    def __init__(self, order = 0):
        self.order = 0

class Returnable(Node):
    
    def GetType(self) -> str:
        return None

class Operation(Node):
    pass

class Statement(Node):
    pass

class Atomic(Node):
    pass

class Overwritable(Node):
    pass

class Content(Atomic, Returnable):
    def __init__(self, value, type : str, order = 0):
        super().__init__(order)
        self.value = value
        self.type = type

    def from_num(Num : int): #Numeric int-like
        return Content(Num, "Integer")

    def from_pair(Num1 : int, Num2 : int): #Numeric float-like
        return Content(float(f"{Num1}.{Num2}"), "Float")

    def from_string(String : str): #String
        return Content(String, "String")

    def from_bool(State : bool): #Boolean
        return Content(State, "Bool")
    
    def null():
        return Content(None, "Null")
    
    def GetType(self):
        return self.type

class LibraryName(Node):
    def __init__(self, name, order=0):
        self.name = name

class Using(Statement):
    def __init__(self, lib : LibraryName, eorder=0):
        self.library = lib
    
class Reference(Atomic, Returnable, Overwritable):
    typeTable = []
    appearance = []
    def __init__(self, name : str, order=0):
        super().__init__(order)
        noticed = False
        for item in Reference.appearance:
            if item[0] == name:
                item[1] += 1
                noticed = True

        
        if not noticed:
            Reference.appearance += [[name, 1]]
        
        self.name = name

    def GetAppearance(name : str) -> int:
        for item in Reference.appearance:
            if item[0] == name:
                return item[1]
            
    def AddAppearance(name : str, amount : int):
        for item in Reference.appearance:
            if item[0] == name:
                item[1] += amount
            
    def ReduceAppearance(name : str):
        for item in Reference.appearance:
            if item[0] == name:
                item[1] -= 1

    def GetType(self):
        for pair in Reference.typeTable:
            if pair[0] == self.name : return pair[1]

        debug.Abort(debug.Error(f"Unknown variable '{self.name}'"))
        

class Declaration(Statement):
    def __init__(self, VarType : str, VarName : Reference, Value : Returnable):
        self.type = VarType
        self.name = VarName
        self.value = Value

        Reference.typeTable += [[VarName, VarType]]

    def auto(name : Reference, value : Returnable):
        return Declaration(value.GetType(), name, value)

    def empty(name : Reference, type : str):
        return Declaration(name, type, Content.null())

class ArgSet(Statement):
    def __init__(self, args : list[Returnable], order=0):
        super().__init__(order)
        self.args = args

class Call(Returnable, Statement):
    typeTable = []

    def __init__(self, name : str, arg : ArgSet):
        self.name = name
        self.arg = arg

    def IsDeclaredByName(name : str):
        return any(pair[0] in name for pair in Call.typeTable)

    def GetType(self):

        for pair in Call.typeTable:
            if pair[0] == self.name : return pair[1]
        
        print(self.name, Call.typeTable)
        return False
           

class Block(Statement):
    def __init__(self, Members : list[Node]):
        self.members = Members

class FunctionDeclaration(Statement):
    def __init__(self, Type : str, FuncName : str, DeclareBlock : Block, MainBlock : Block, order=0):
        super().__init__(order)

        self.name = FuncName
        self.type = Type
        self.dec = DeclareBlock
        self.main = MainBlock
        self.external = False

        Call.typeTable += [[FuncName, Type]]

    def ext(Type : str, FuncName : str, DeclareBlock : Block):
        new= FunctionDeclaration(Type, FuncName, DeclareBlock, Block([]))
        new.external = True
        return new

    def single(Type : str, FuncName : str, DeclareBlock : Block):
        return FunctionDeclaration(Type, FuncName, DeclareBlock, Block([]))
        

class Assignment(Operation):
    def __init__(self, target : Overwritable, value : Returnable,  order=0):
        self.target = target
        self.value = value
        super().__init__(order)

class Expression(Operation, Returnable):
    def __init__(self, operation : str,  operands : list[Returnable], order=0):
        super().__init__(order)
        self.operands = operands
        self.operation = operation
        self.finalType = None

    def GetType(self) -> str:
        return self.finalType

class Access(Statement):
    def __init__(self, pointer : Returnable, value : Returnable):
        self.value = value
        self.pointer = pointer

class Wrapper(Statement):
    def __init__(self, expr : Returnable, order=0):
        super().__init__(order)
        self.expression = expr

class If(Statement):
    def __init__(self, condition : Returnable, stmt : Statement, elseStmt : Statement, order=0):
        super().__init__(order)
        self.condition = condition 
        self.statement = stmt
        self.elseStatement = elseStmt

    def single(cond : Returnable, run : Statement):
        return If(cond, run, None)
    
    def guard(cond : Returnable, ret : Returnable):
        return If(cond, Return(ret, ret.order), None)
    
class While(Statement):
    def __init__(self, condition : Returnable, stmt : Statement, order=0):
        super().__init__(order)
        self.condition = condition
        self.statement = stmt

class Return(Statement):
    def __init__(self, toRet : Returnable, order=0):
        super().__init__(order)
        self.toReturn = toRet

    def void():
        return Return(None)

class Class(Statement):
    nameFieldShiftTable = {}
    def __init__(self, name : str, init : Block, manifest : Block):
        self.name = name
        self.init = init
        self.manifest = manifest

        finalInstanceSize = 0
        
        for statement in manifest.members:
            if isinstance(statement, Declaration):
                finalInstanceSize += meta.Meta.instanceSizeTable[statement.type]

        meta.Meta.instanceSizeTable.update({name: finalInstanceSize})
        meta.Meta.sizeTable.update({name: 8})


class Extension(Operation, Returnable, Overwritable):
    def __init__(self, object : Reference, attribute : Returnable):
        self.object = object
        self.attribute = attribute

def Visualize(node : Node, depth = 0, step = 4):

    print('  ' * depth + node.__class__.__name__)

    for name, val in vars(node).items():
        prefix = '  ' * (depth + 1) + f'{name}: '
        if isinstance(val, Node):
            print(prefix)
            Visualize(val, depth + step)
        elif isinstance(val, list):
            print(prefix)
            for item in val:
                if isinstance(item, Node):
                    Visualize(item, depth + step)
                else:
                    print('  ' * (depth + step) + repr(item))
        else:
            print(prefix + repr(val))