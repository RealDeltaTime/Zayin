import node
import tokenizer
from node import Node

class Atom:
    def __init__(self, tokens : list[str], store : bool = False, assocR : bool = False, isTolerant : bool = False):
        self.tokens = tokens
        self.store = store
        self.assocR = assocR
        self.isTolerant = isTolerant

class Signature:
    def __init__(self, atoms : list[Atom], priority : int, conversionTo : Node):
        self.atoms = atoms
        self.priority = priority
        self.conversionTo = conversionTo
        

class SignatureLibrary:
    def GetSignatureSet() -> list[Signature]:            
        return sorted([
            Signature
            (
                atoms = [Atom(["Number"], store=True), Atom(["Dot"]), Atom(["Number"], store=True)], 
                priority = 6,
                conversionTo = node.Number
            ),
            Signature
            (
                atoms = [Atom(["Number"], store=True)],
                priority=5,
                conversionTo = node.Number
            ),
            Signature
            (
                atoms = [Atom(["Quote"]), Atom(["Anything"]), Atom(["Quote"])], 
                priority = 3,
                conversionTo = node.String
            ),
            Signature
            (
                atoms=[Atom(tokenizer.TokenCatalog.GetGenericTypesTokens(), store=True), Atom(["Name"], store=True)],
                priority=1,
                conversionTo=node.Declaration
            ),
            Signature
            (
                atoms=[Atom(tokenizer.TokenCatalog.GetGenericTypesTokens(), store=True), Atom(["Name"], store=True), Atom(["Assignment"]), Atom(["Anything"], store=True), Atom(["EOL"])],
                priority=2,
                conversionTo=node.Declaration
            ),
            Signature
            (
                atoms = [Atom(["BlockOpen"]), Atom(["SeqStart"]), Atom(["Anything"], store=True), Atom(["SeqEnd"]), Atom(["BlockClosed"])],
                priority = 0,
                conversionTo = node.Block
            )
        ], key= lambda s: s.priority, reverse=True)

class Constructor:
    #
    #   Provides "Technical" tokens:
    #       "Anything" Literally anything.
    #       "Token" Any valid token.
    #       "SeqStart" Describes start of sequenece.
    #       "SeqEnd" Describes end of sequenece.
    #       Whatever is between those describes strict repeated pattern, unfinished, incomplete sequence considered to be error.
    #       In case of "SeqStart" store flag on its element will return stored tokens as a list. 
    #

    def GetRawPattern(sig : Signature):
        result = []

        for atom in sig.atoms:
            result += [atom.tokens]

        return result


    def ExtractSequenceSignature(sig : Signature) -> Signature:
        s = 0
        e = 0
        result = Signature([], False, sig.conversionTo)
        store = False
        for atom in sig.atoms:
            if "SeqStart" in atom.tokens: 
                if s+e == 0:
                    s += 1
                    continue
                s += 1

            elif "SeqEnd" in atom.tokens: 
                e += 1
                if s == e:
                    return result
                
            if not s+e == 0 : result.atoms += [atom]

    def MiniConstruct(seqsig : Signature, tokens : list[str], raw : list[str], breakpoint : int, store : bool):
        i = 0

        def next():
            i+=1
            if i == len(seqsig.atoms): i = 0

        def read():
            return seqsig.atoms[i]
        
        for token in tokens[breakpoint:-1]:
            if tokenizer.Tokenizer.Compare(token, read().tokens):
                next()

    def Construct(tokens : list, raw : list):
        signatures = SignatureLibrary.GetSignatureSet()

        for sig in signatures:

            if not isinstance(sig, Signature): raise Exception("Incorrect signature.")
            i = 0
            ai = 0

            while i < len(tokens):

                if tokenizer.Tokenizer.Compare(tokens[i], sig.atoms[ai]):
                    ai += 1
                else:
                    ai = 0

                if ai == len(sig.atoms) - 1:
                    
                    
                
                i += 1



        
        return tokens

            

    
