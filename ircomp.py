from node import *
from random import randint

class Index():
    all : list["Index"] = []
    def __init__(self, repr, argument = False, isTemp = False):
        self.index = len(Index.all)
        self.repr = repr
        self.isAsrgument = argument
        self.mentions = []
        self.mentioned = 0
        self.isTemp = isTemp
        Intermediate.current.indices += [self]
        Index.all += [self]

    def GetAppearanceClean(self):
        result = 0
        seen = []
        for pair in self.mentions:
            if not pair[0] in seen:
                result += 1
                seen += [pair[0]]
        return result
    

class Pseudo():
    def __init__(self, operation : str = None, loadInto : Index = None, operands : list[Index] = [], representing : Node = None, special = False, npp = False):
        if operation == None and len(operands) == 0:
            return
        if loadInto == None : loadInto = Index(representing)
        elif loadInto == False : loadInto = None

        self.operation = operation
        self.operands = operands
        self.loadInto = loadInto
        self.representing = representing
        self.special = special
        self.involved = []

        if npp: return
        
        for poss in self.operands + [loadInto]:
            if isinstance(poss, Index): 
                poss.mentions += [[self, poss == loadInto]]
                poss.mentioned += 1
                self.involved += [poss]

        Intermediate.current.data += [self]
    
    def Format(self):
        print(f"{'['+str(self.loadInto.index)+'] = ' if self.loadInto != None else ''}{'SPECIAL ' if self.special else ''}{self.operation + ' with ' if self.operation != None else ''}{' and '.join(['['+str(operand.index)+']' if isinstance(operand, Index) else str(operand) for operand in self.operands]) if self.operands != None else []}")#, representing {self.representing}")

class Context():
    def __init__(self, name : str, data : list[Pseudo] = None, master = None, isDeadEnd = False, forceSync = False):
        self.data = data if data != None else []
        self.name = name 
        self.indices : list[Index] = []
        self.master = master
        self.isDeadEnd = isDeadEnd
        self.forceSync = forceSync

class Intermediate():
    representation : list[Context] = []# = [Context('', [], None, True, False)]
    environment = {}
    lateinset = Context('', [], None, False, False)
    current : Context = None# = representation[0]
    anchor : Context = None

    def RecursiveTransform(node : Node, noRes = False) -> Index:
        if isinstance(node, Reference):
            for id in Index.all:
                if id.repr == [node.name,Intermediate.anchor]:
                    return id
            raise Exception(f"Undeclared variable {node.name}")
                
        elif isinstance(node, Content):
            return node.value
        
        elif isinstance(node, Call):
            result = Index(node, isTemp=True)
            Pseudo("call", result if not noRes else False, [node.name] + [Intermediate.RecursiveTransform(arg) for arg in node.arg.args], node)
            return result
        
        elif isinstance(node, Expression):
            result = Index(node, isTemp=True)
            Pseudo(node.operation, result if not noRes else False, [Intermediate.RecursiveTransform(op) for op in node.operands], node)
            return result

    def Transform(AST : list[Node], env : list[str] = []):
        print(AST)
        for statement in AST:
            if isinstance(statement, FunctionDeclaration):
                if statement.external:
                    Intermediate.lateinset.data += [Pseudo("External", False, [statement.name], statement, npp=True)]
                else:
                    new = Context(statement.name)
                    Intermediate.representation += [new]
                    Intermediate.anchor = new
                    Intermediate.current = new
                    Intermediate.Transform(statement.dec.members, ["arg"])
                    Intermediate.Transform(statement.main.members)
                
            elif isinstance(statement, If):

                anywayName = "ret" + str(len(Intermediate.representation))
                elseName = "else" + str(len(Intermediate.representation))
                ifname = "if" + str(len(Intermediate.representation))

                anyway = Context(anywayName, master=Intermediate.anchor)
                Intermediate.RecursiveTransform(statement.condition, True)
                condId = Intermediate.current.data[-1]
                Pseudo("jump", False, [condId, ifname], statement)
                if statement.elseStatement == None: 
                    Pseudo("jump", False, [True, anywayName], statement)
                else:
                    Pseudo("jump", False, [True, elseName], statement)

                new = Context(ifname, master=Intermediate.anchor)
                Intermediate.current = new
                Intermediate.representation += [new]

                Intermediate.Transform(statement.statement.members)
                Pseudo("sync", False, ["used"])
                ends = 0
                if new.data[-2].operation != "return" : 
                    Pseudo("jump", False, [True, anywayName], statement)
                else:ends +=1
                Intermediate.current = anyway
                Intermediate.representation += [anyway]

                if statement.elseStatement != None:
                    new = Context(elseName, master=Intermediate.anchor)
                    Intermediate.current = new
                    Intermediate.representation += [new]
                    Intermediate.Transform(statement.elseStatement.members)
                    Pseudo("sync", False, ["used"])
                    if new.data[-2].operation != "return" : 
                        Pseudo("jump", False, [True, anywayName], statement)
                    else:ends +=1
                    Intermediate.current = anyway

                if ends == 2:
                    for i, context in enumerate(Intermediate.representation):
                        if context.name == anywayName: 
                            Intermediate.representation.pop(i)
                            break

            elif isinstance(statement, While):
                anywayName = "ret" + str(len(Intermediate.representation))
                whilename = "while" + str(len(Intermediate.representation))

                anyway = Context(anywayName, master=Intermediate.anchor)
                Intermediate.RecursiveTransform(statement.condition, True)
                condId = Intermediate.current.data[-1]
                Pseudo("jump", False, [condId, whilename], statement)
                Pseudo("jump", False, [True, anywayName], statement)

                new = Context(whilename, master=Intermediate.anchor, forceSync=True)
                Intermediate.current = new
                Intermediate.representation += [new]

                Intermediate.Transform(statement.statement.members)
                Pseudo("sync", False, ["used"])
                Intermediate.RecursiveTransform(statement.condition, True)
                Pseudo("jump", False, [condId, whilename], statement)
                Pseudo("jump", False, [True, anywayName], statement)
                Intermediate.current = anyway
                Intermediate.representation += [anyway]
            
            elif isinstance(statement, Assignment):
                load = Intermediate.RecursiveTransform(statement.target)
                target = Intermediate.RecursiveTransform(statement.value)

                Pseudo(None, load, [target], statement)
                
            elif isinstance(statement, Declaration):
                if statement in Intermediate.environment:
                    Intermediate.environment[statement] += [Intermediate.current]
                else:
                    Intermediate.environment.update({statement: Intermediate.current})
                new = Index([statement.name,Intermediate.anchor], "arg" in env)
                if "arg" in env:
                    Pseudo("input", new, [], statement)
                elif statement.value != None:
                    print(statement.value)
                    Pseudo(None, new, [Intermediate.RecursiveTransform(statement.value)], statement.name)
            elif isinstance(statement, Return):
                Intermediate.current.isDeadEnd = True
                Pseudo("return", False, [Intermediate.RecursiveTransform(statement.toReturn)], statement)

            elif isinstance(statement, Access):
                ptrind = Intermediate.RecursiveTransform(statement.pointer)
                valind = Intermediate.RecursiveTransform(statement.value)
                Pseudo("access", False, [ptrind, valind], statement)

