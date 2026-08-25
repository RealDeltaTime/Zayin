import tokenizer
from debug import *
from node import *

class Package:
    def __init__(self, content : list[list, list], Convertable : type):
        self.content = content
        self.type = Convertable

    def Elevate(self, context):
        if self.type == Returnable:
            internalComma = "Comma" in self.content[0]
            backNamed = context[-1] == "Name" 
            if internalComma or backNamed:
                return Constructor.ArgsBuild(*Constructor.RecursiveConstruct(*self.content))
            else:
                return Constructor.RecursiveConstruct(*self.content)[0]
        elif self.type == Block:
            return Block(Constructor.Construct(*Constructor.Group(*self.content)))

class Constructor:

    signatures = sorted([
        [Class, Class, ["Class", "Name", Block, Block], ["1", 2, 3]],
        [Access, Access, ["Access", Returnable, "Assignment", Returnable], [1,3]],
        [Assignment, Assignment, [Reference, "Assignment", Returnable], [0,2]],
        [Assignment, Assignment, [Extension, "Assignment", Returnable], [0,2]],
        [FunctionDeclaration, FunctionDeclaration, [tokenizer.TokenCatalog.GenericTypeTokens, "Name", Block, Block], ["0", 1, 2, 3]],
        [FunctionDeclaration, FunctionDeclaration.ext, ["External", tokenizer.TokenCatalog.GenericTypeTokens, "Name", Block], ["1", 2, 3]],
        [FunctionDeclaration, FunctionDeclaration.single, [tokenizer.TokenCatalog.GenericTypeTokens, "Name", Block], ["1", 2, 3]],
        [Return, Return, ["Return", Returnable], [1]],
        [Return, Return.void, ["Return"], []],
        [While, While, ["While", Returnable, Statement], [1, 2]],
        [If, If.single, ["If", Returnable, Statement], [1, 2]],
        [If, If, ["If", Returnable, Statement, "Else", Statement], [1, 2, 4]],
        [If, If.guard, ["Return", Returnable, "If", Returnable], [3, 1]],
        [Declaration, Declaration.empty, [tokenizer.TokenCatalog.GenericTypeTokens, "Name"], ["0", 1]],
        [Declaration, Declaration, [tokenizer.TokenCatalog.GenericTypeTokens, "Name", "Assignment", Returnable], ["0", 1,3]],
        [Declaration, Declaration.auto, ["Var", "Name", "Assignment", Returnable], [1,3]],
        [Wrapper, Wrapper, [Returnable], [0]]
    ], key=lambda x : len(x[2]), reverse=True)

    def Pack(tokens : list[str], raw : list[str], borderTokens : list[str]) -> list[list]:
        start, end, opened, closed = 0, 0, 0, 0
        oT, cT = borderTokens[0], borderTokens[1] if len(borderTokens) > 2 else None 

        if cT == None:
            for i, token in enumerate(tokens):
                if token == borderTokens[0]: 
                    if opened == 0 : start = i
                    opened += 1
                if opened == 2: 
                    end = i
                    break
        else:
            for i, token in enumerate(tokens):
                opened += int(token == oT)
                closed += int(token == cT)
                
                if token == oT and opened == 1: start = i
                if opened == closed and opened + closed != 0:
                    end = i
                    break
        
        if [start, end] != [0, 0]: 
            p = [Package([tokens[start+1:end], raw[start+1:end]], borderTokens[2])]
            raw[start:end+1] = p
            tokens[start:end+1] = p
        
        for i, token in enumerate(tokens):
            if isinstance(token, Package):
                Constructor.PackAll(token.content[0], token.content[1])
        return [tokens, raw]
    
    def PackAll(tokens, raw):
        ScopeKeywords = [
        ["OpenB1", "ClosedB1", Returnable],
        ["BlockOpen", "BlockClosed", Block],
        ["OpenB3", "ClosedB3", None],
        ["Quote", str]            
        ]
        for Tpair in ScopeKeywords:
            packed = Constructor.Pack(tokens, raw, Tpair)
            while Tpair[0] in packed[0]:
                packed = Constructor.Pack(packed[0], packed[1], Tpair)

        return packed
    
    def ConstructKeywords(tokens : list, raw : list):

        convert = [
            ["Null",  Content,[None, "Null"]],
            ["True",  Content,[True, "Boolean"]],
            ["False", Content,[False, "Boolean"]]
        ]
        
        for i, token in enumerate(tokens):
            for pair in convert:
                if pair[0] == token:
                    new = pair[1](*pair[2])
                    tokens[i], raw[i] = new, new

        return [tokens, raw]
    
    def ConstructNames(tokens : list, raw : list):

        ignore = tokenizer.TokenCatalog.GenericTypeTokens + ["Var", "Class"]

        for i, token in enumerate(tokens):
            if token == "Name":                
                if i < len(tokens) - 1: 
                    if isinstance(tokens[i+1], ArgSet):
                        ref = Call(raw[i], raw[i+1])
                        tokens[i:i+2], raw[i:i+2] = [ref], [ref]
                        continue
                if i != 0:
                    if tokens[i-1] in ignore: continue
                ref = Reference(raw[i])
                tokens[i], raw[i] = ref, ref

        return [tokens, raw]

    def ConstructExtensions(tokens : list, raw : list):

        for i, token in enumerate(tokens):
            if token == "Dot" and isinstance(tokens[i-1], Returnable) and isinstance(tokens[i+1], (Reference, Call)):
                new = Extension(tokens[i-1], tokens[i+1])
                tokens[i-1:i+2] = [new]
                raw[i-1:i+2] = [new]

        return [tokens, raw]

    def ConstructMeta(tokens : list, raw : list):

        for i, token in enumerate(tokens):
            if token == "Instance" and tokens[i-2] in meta.Meta.instanceSizeTable and tokens[i+1] == "size":
                new = Extension(tokens[i-1], tokens[i+1])
                tokens[i-1:i+2] = [new]
                raw[i-1:i+2] = [new]

        return [tokens, raw]        
    
    def ArgsBuild(tokens, raw):

        expectedArg = True
        arg = []

        for i, token in enumerate(tokens):
            if isinstance(token, Returnable):
                if expectedArg:
                    expectedArg = False
                    arg += [token]
                else:
                    Abort(SyntaxError("Expected an argument."))
            elif token == "Comma":
                if expectedArg:
                    Abort(SyntaxError("Expected comma."))
                else:
                    expectedArg = True



        return ArgSet(arg)

    def ConstructAtomic(tokens, raw):

        ops = tokenizer.TokenCatalog.GetOperators()
        opConfs = tokenizer.TokenCatalog.OperatorsConfig

        def GetOpCount(token : str) -> int:
            for opc in opConfs:
                if opc[0] == token : return 1 if opc[1][0] == 'U' else 2
            
            return None
        
        for i, token in enumerate(tokens):
            if token == "Dot" and tokens[i-1] == "Number" and tokens[i+1] == "Number":
                new = Content.from_pair(int(raw[i-1]), int(raw[i+1]))
                tokens[i-1:i+2], raw[i-1:i+2] = [new], [new]

        for i, token in enumerate(tokens):
            if token == "Number":
                new = Content.from_num(int(raw[i]))
                tokens[i], raw[i] = new, new

        for i, token in enumerate(tokens): 
            if token in ops:
                new = Expression(token, None, None)
                new.operands = [None] if GetOpCount(token) == 1 else [None, None]
                new.operation = token
                tokens[i], raw[i] = new, new

        return [tokens, raw]

    def ConstructExpressions(tokens : list, raw : list):

        opConfs = tokenizer.TokenCatalog.OperatorsConfig

        for i, token in enumerate(tokens):
            if isinstance(token, Expression) and i == 0 or (isinstance(token, Expression) and token.operation == "Minus" and not isinstance(tokens[i-1], Returnable)):
                tokens[i] = Expression("Negative", [None], token.order)
                print("Negative")

        def GetPower(token : str) -> int:
            for opc in opConfs:
                if opc[0] == token : return opc[2]

            return None
        
        def GetAssocOrder(token : str) -> int:
            for opc in opConfs:
                if opc[0] == token: return 1 if opc[1][1] == 'R' else -1
            
            return None

        def GetOperandSide(token : str) -> int:
            for opc in opConfs:
                if opc[0] == token: 
                    dt = opc[1][2]
                    if dt == 'R':
                        return 1
                    elif dt == 'L':
                        return -1
                    else: return 0
            
            return None

        def GetOperandsType(node : Expression):
            if isinstance(node, Expression):
                for opc in tokenizer.TokenCatalog.OperatorsConfig:
                    if opc[0] == node.operation: return opc[3]

        def GetReturnableType(node : Returnable):             
            if isinstance(node, Expression):
                for opc in tokenizer.TokenCatalog.OperatorsConfig:
                    if opc[0] == node.operation: return opc[4]
            else:
                type = node.GetType()
                if isinstance(type, str): return [type]
                return type

        err = 0
        while any(any(not opr for opr in item.operands) for item in tokens if isinstance(item, Expression)):
            for i, token in enumerate(tokens):
                if err >= len(tokens) and len(tokens) != 1: raise Exception("Expression building iteration falure.")
                if isinstance(token, Returnable) and token:
                    if isinstance(token, Expression) and any(not opr for opr in token.operands): 
                        err += 1
                        continue
                    r = tokens[i+1] if i + 1 <= len(tokens) - 1 and isinstance(tokens[i+1], Expression) and GetOperandSide(tokens[i+1]) != 1 else None
                    l = tokens[i-1] if i != 0 and isinstance(tokens[i-1], Expression) and GetOperandSide(tokens[i-1]) != -1 else None
                    #if r and not isinstance(r, Call) : r = r if bool(set(GetOperandsType(r)[0]) & set(GetReturnableType(token))) else None
                    #if l and not isinstance(l, Call) : l = l if bool(set(GetOperandsType(l)[1]) & set(GetReturnableType(token))) else None

                    if l and r:
                        diff = GetPower(r.operation) - GetPower(l.operation)
                        if diff == 0:
                            x = GetAssocOrder(r.operation)
                        else:
                            x = (1, -1)[diff < 0]

                    elif l and not r:
                        x = -1
                    elif (not l) and r:
                        x = 1
                    else:
                        err += 1
                        continue
                    err = 0
                    ix = tokens[i+x]
    
                    if ix.operands == [None]:
                        ix.operands[0] = token
                    else:
                        ix.operands[int(-x/2+0.5)] = token
                    tokens.pop(i)
                    raw.pop(i)
                    
        return [tokens, raw]
    
    def ConstructStatements(tokens : list, raw : list):

        def isMatchingItem(token, sigpart):
            if isinstance(sigpart, list):
                for element in sigpart:
                    if isMatchingItem(token, element): return True
                return False
            elif isinstance(sigpart, type):
                return isinstance(token, sigpart)
            else: return token == sigpart
                
        def GetSignatureMissPoint(tokenSegment : list, rawSegment : list, signature : list):
            for i, token in enumerate(tokenSegment):
                if i >= len(signature) or i >= len(tokenSegment): 
                    Abort(Error(tokenSegment))
                if not isMatchingItem(token, signature[i]):
                    return i
            return None
        
        def ExtractRaw(sig : list):
            result = []
            for index in sig[3]:
                if isinstance(index, int):result += [raw[index]]
                else:result += [tokens[int(index)]]
            return result
        
        for sig in Constructor.signatures:
            if len(sig[2]) <= len(tokens):
                point = GetSignatureMissPoint(tokens, raw, sig[2])
                if point == None: 
                    new = [sig[1](*ExtractRaw(sig))]
                    return [new, new]

        Abort(Error(f"Can't resolve {raw}"))
        
    
    def ExpressionsDefine(AST : list[Node]):

        autoDefinitions = ["Integer", "Float"]

        def GetExternalType(node : Expression):
            for opc in tokenizer.TokenCatalog.OperatorsConfig:
                if opc[0] == node.operation:
                    mode = opc[5]
                    if mode == "AUTO":
                        prior = 0
                        for op in node.operands:
                            opPriority = None
                            opType = op.GetType()
                            for i, type in enumerate(autoDefinitions):
                                if type in opType: opPriority = i
                            if opPriority > prior : prior = opPriority
                        return autoDefinitions[prior]
                    elif mode == "EXTR":
                        return opc[4][0]
                    else:
                        return opc[3][0][0]

        
        def SingleDefine(token : Expression):
            for opr in token.operands:
                if isinstance(opr, Expression):
                    SingleDefine(opr)
                if isinstance(opr, Call):
                    for arg in opr.arg.args:
                        if isinstance(arg, Expression) : SingleDefine(arg)
            token.finalType = GetExternalType(token)

        for node in AST:
            if not hasattr(node, '__dict__') : continue 
            for name, attr in vars(node).items():
                if isinstance(attr, Block): attr.members = Constructor.ExpressionsDefine(attr.members) 
                if isinstance(attr, Expression) : SingleDefine(attr)
            if isinstance(node, Declaration) and node.type == None: 
                node.type = node.value.GetType()
                for pair in Reference.typeTable:
                    if pair[0] == node.name : pair[1] = node.type

        return AST

    
    def RecursiveConstruct(tokens, raw):
        for i, token in enumerate(tokens):
            if isinstance(token, Package):
                result = token.Elevate(tokens[0:i])
                tokens[i] = result
                raw[i] = result
        
        out = Constructor.ConstructKeywords(tokens, raw)
        out = Constructor.ConstructNames(*out)
        out = Constructor.ConstructAtomic(*out)
        out = Constructor.ConstructExtensions(*out)
        out = Constructor.ConstructExpressions(*out)

        return out
    
    def ConstructSingle(tokens, raw):
        rec = Constructor.RecursiveConstruct(tokens, raw)
        stmt = Constructor.ConstructStatements(rec[0], rec[1])

        return stmt[0]

    def Group(tokens : list, raw : list):
        if len(tokens) == 0 : return [tokens, raw]
        nt, nr = [], []
        stackT, stackR = [], []

        for i, token in enumerate(tokens):
            if token == "EOL":
                nt += [stackT]
                nr += [stackR]
                stackT, stackR = [], []
            else:
                stackT += [token]
                stackR += [raw[i]]

        if token != "EOL":
            nt += [stackT]
            nr += [stackR]


        return [nt, nr]

    def Construct(tokensG, rawG):
        for i, group in enumerate(tokensG):
            new = Constructor.ConstructSingle(group, rawG[i])[0]
            tokensG[i] = new
            rawG[i] = new

        return tokensG
