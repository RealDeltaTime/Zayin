import lexer

class TokenCatalog():

    TranslationTable = sorted([
        ["var", "Var"],

        ["int", "Integer"],
        ["float", "Float"],
        ["string", "String"],
        ["bool", "Boolean"],
        ["list", "List"],
        ["set", "Set"],

        ["=", "Assignment"],
        [".", "Dot"],
        [",", "Comma"],

        [";", "EOL"],
        ["(", "OpenB1"],
        [")", "ClosedB1"],
        ["{", "BlockOpen"],
        ["}", "BlockClosed"],
        ["[", "OpenB3"],
        ["]", "ClosedB3"],
        ['"', "Quote"],

        ["+", "Plus"],
        ["-", "Minus"],
        ["*", "Times"],
        ["/", "Divide"],
        ["^", "Power"],

        ["--", "ConsMinus"],
        ["++", "ConsPlus"],
        ["+=", "Increment"],
        ["-=", "Decrement"],
        ["~", "MemAccess"],
            
        ["and", "And"],
        ["or", "Or"],
        ["not", "Not"],
        ["xor", "Xor"],

        ["==", "Equals"],
        ["!=", "NotEquals"],
        [">=", "GreaterOE"],
        ["<=", "LessOE"],
        [">", "Greater"],
        ["<", "Less"],

        ["if", "If"],
        ["else", "Else"],
        ["while", "While"],
        ["for", "For"],
        ["foreach", "Foreach"],
        ["return", "Return"],

        ["null", "Null",],
        ["true", "True"],
        ["false", "False"],

        ["using", "Using"],
        ["extern", "External"],
        ["access", "Access"],

        ["class", "Class"],
        ["instance", "Instance"],
        ["size", "Size"]
    ], key=lambda x : len(x[0]))

    BooleanOperators = [
        "And", "Or", "Xor", "Equals", 
        "GreaterOE", "LessOE", "Greater", "Less"      
    ]

    BinaryOperators = [
        "Plus", "Minus", "Times", "Divide", "Power",
        "And", "Or", "Xor", "Equals", 
        "GreaterOE", "LessOE", "Greater", "Less", 
        "ConsMinus", "ConsPlus", "Increment", "Decrement" 
    ]
    

    def GetArgSeparationSymb():
        return [","]

    def GetAllKeywords() -> list:
        result = []
        for translation in TokenCatalog.TranslationTable:
            result += [translation[0]]
        return result
    
    def GetMinus():
        return "-"
    
    numeric = ["Integer", "Real", "Float", "Double"]

    OperatorsConfig =  sorted([
        ["Plus",      "BLB",  1, [numeric, numeric], numeric, "AUTO"],
        ["Minus",     "BLB",  1, [numeric, numeric], numeric, "AUTO"],
        ["Times",     "BLB",  2, [numeric, numeric], numeric, "AUTO"],
        ["Divide",    "BLB",  2, [numeric, numeric], numeric, "AUTO"],
        ["Power",     "BRB",  3, [numeric, numeric], numeric, "AUTO"],
            
        ["And",       "BRB", -2, [["Bool"], ["Bool"]], ["Bool"], "EXTR"],
        ["Or",        "BRB", -3, [["Bool"], ["Bool"]], ["Bool"], "EXTR"],
        ["Not",       "ULR", -1, [["Bool"]],["Bool"], "EXTR"],
        ["Xor",       "BRB", -3, [["Bool"], ["Bool"]], ["Bool"], "EXTR"],

        ["Equals",    "BLB",  0, [numeric, numeric], ["Bool"], "EXTR"], 
        ["GreaterOE", "BLB",  0, [numeric, numeric], ["Bool"], "EXTR"], 
        ["LessOE",    "BLB",  0, [numeric, numeric], ["Bool"], "EXTR"], 
        ["Greater",   "BLB",  0, [numeric, numeric], ["Bool"], "EXTR"], 
        ["Less",      "BLB",  0, [numeric, numeric], ["Bool"], "EXTR"], 
            
        ["UnDecrem.", "URB", 2.5, [numeric], numeric, "INTR"], 
        ["UnIncrem.", "URB", 2.5, [numeric], numeric, "INTR"],
        ["Increment", "BRB",  0, [numeric, numeric], numeric, "INTR"], 
        ["Decrement", "BRB",  0, [numeric, numeric], numeric, "INTR"],
        ["Negative",  "ULR",  4, [numeric], numeric, "INTR"],
        ["MemAccess", "ULR",  4, [numeric], numeric, "INTR"]
        
    ], key=lambda x: x[2], reverse=True)
    
    def GetOperators():
        result = []
        for item in TokenCatalog.OperatorsConfig: result += [item[0]]
        return result
    
    GenericTypeTokens = [
        "Integer", "Float", "Double", "Real", "String", "Boolean"
    ]
    
    GenericTypesRaw = [
        "int", "float", "string", "bool"
    ]

    AllTypeTokens = GenericTypeTokens
    AllTypesRaw = GenericTypesRaw

    SeparationPair = ["Comma", ","]
    
class UnknownOperator(Exception):
    def __init__(symbol : str):
        super().__init__(f"Cannot resolve following symbol: '{symbol}'")
            

class Tokenizer():
    def Compare(token : str, target : list[str]):
        if target == ["Anything"]: return True
        if target in TokenCatalog.AllKeywords: return True

        return token in target

    def Translate(raw : list) -> list:
        result = []

        for string in raw:
            for translation in TokenCatalog.TranslationTable:
                condition = string == translation[0]
                if condition: 
                    result += [translation[1]]
                    break
            if not condition:
                type = lexer.Lexer.GetCharacterType(string)
                if type == 0:
                    result += ["Name"]
                elif type == 1:
                    result += ["Number"]
                elif string[0] == "-" and string[0:-1]:
                    result += ["Number"]
                else:
                    result += ["ERR"]
        return result
                

    