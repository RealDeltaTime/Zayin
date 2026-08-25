from debug import CInfo, IR

import lexer
import tokenizer
import parse
import node
import ircomp
import low
import time
import lowir

from sys import argv

def main(custom = ''):
    if len(argv) == 1 : raise Exception("Incorrect use. Use '\ main.py <pathToFile>'")
    start_time = time.monotonic()
    

    originalfile = open(argv[1] if custom=='' else custom, "r")
    original = originalfile.read()
    originalfile.close()

    stringed, replace = lexer.Lexer.SeparateStrings(original)
    separated = lexer.Lexer.Separate(stringed)
    bonded = lexer.Lexer.Bond(separated)
    cleaned = lexer.Lexer.Clean(bonded)
    tokenized = tokenizer.Tokenizer.Translate(cleaned)
    defined = []
    todelete = []
    for i, token in enumerate(tokenized):
        if i < len(tokenized)-3:
            if tokenized[i] == "Using":
                if tokenized[i+1] == "Name":
                    todelete += [i, i, i]
                    defined += main(f"{cleaned[i+1]}.ayn")
    print(tokenized)
    for ind in todelete:
        print(tokenized[ind])
        tokenized.pop(ind)
        cleaned.pop(ind)
        print("deleted ", ind)
    print(todelete)
    print(tokenized)
    nested = parse.Constructor.PackAll(tokenized, cleaned)
    grouped = parse.Constructor.Group(nested[0], nested[1])
    constructed = parse.Constructor.Construct(grouped[0], grouped[1])
    defined += parse.Constructor.ExpressionsDefine(constructed)

    print(original)
    print(separated)
    print(bonded)
    CInfo(f"Cleaned {cleaned}")
    CInfo(f"Tokenized {tokenized}")
    CInfo(f"Lenght difference: {len(cleaned) - len(tokenized)}")
    CInfo(f"Nested {nested}")
    CInfo(f"Grouped {grouped}")
    CInfo(f"Constructed {constructed}")
    CInfo(f"Defined {defined}")

    for statement in defined:
        print("\n")
        node.Visualize(statement, step=2)

    CInfo(f"Typetable dump: \n Call:{node.Call.typeTable}, \nReference:{node.Reference.typeTable}\n\n")
    
    if custom != '': return defined
    else : 
        print("Parsing main file")
    ircomp.Intermediate.Transform(defined)
    ir = ircomp.Intermediate.representation
    print(ir)
    IR(ir)

    ircomp.Intermediate.representation.insert(0, ircomp.Intermediate.lateinset)
    lowir.LowIntermediate.Translate(ir)
    end_time = time.monotonic()
    print()
    struct = time.localtime()
    y, m, d, h, mi, s = struct.tm_year, struct.tm_mon, struct.tm_mday, struct.tm_hour, struct.tm_min, struct.tm_sec
    print([[id.index, id.repr]for id in low.Index.all])
    print(f";[{y}/{m}/{d}, {h}:{mi} and {s}s] YMD, GMT+3")
    print(";Zayin 1.0 (Samarkand) unstable")
    print(f";Build complete in ~{end_time-start_time} seconds.")
    #print(''.join([instr.Format() for instr in low.Translator.assembly]))

    

if __name__ == "__main__":
    main()