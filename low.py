from ircomp import Index, Pseudo, Intermediate, Context
from debug import printMapping, IR

class Register:
    def __init__(self, name : str, isa = False):
        self.name = name
        self.occupation = False
        self.isStackAllocated = isa

class Usepack:
    def __init__(self, regs : list[Register], purpose = "INSTR"):
        self.registers = regs
        self.purpose = purpose

    def View(self):
        print(f"  <{self.purpose}> - [{self.index}]")

class Mapping:
    def __init__(self, index : Index, map : list[Usepack]):
        self.index = index
        self.map = map
    
    def Feed(self):
        print(f"[{self.index.index}] is requested")
        if len(self.map) == 0:
            print("  ERR NO REGISTER PRESENT")
            return Usepack([],"MISSING")
        else:
            #print(self.map)
            result = self.map[0]
            self.map.pop(0)
            #print(self.map)
            #print([ind.index for ind in Translator.indicesInUse])
            if len(self.map) == 0:
                if self.index in Translator.indicesInUse : Translator.indicesInUse.remove(self.index)
                #print([ind.index for ind in Translator.indicesInUse])
                print(f"  [{self.index.index}] EOL")
            elif not self.index in Translator.indicesInUse:
                Translator.indicesInUse += [self.index]
            print(f"  Sent {[reg.name for reg in result.registers]} for [{self.index.index}] as {result.purpose}")
            return result

    def SafeFeed(self):
        return self.map[0]

class Spec:
    def __init__(self, operation : str, firstEXPARG : str, secondEXPARG : str, outputEXPARG):
        self.operation = operation
        self.firstEXPARG = firstEXPARG
        self.secondEXPARG = secondEXPARG
        self.outputEXPARG = outputEXPARG

class Managment:
    specs = [Spec(*el)for el in [
        ["add", "ANY", "ANY", "ST"],
        ["sub", "ANY", "ANY", "ST"],
        ["div", "ANY", "ANY", "ST"],
        ["mul", "ANY", "ANY", "ST"],
    ]]
    registers = [Register(name) for name in ["rcx", "rdx", "r8", "r9", "rax", "r10", "r11"]]
    mapping : list[Mapping] = []
    alocatedIndices = []
    defaultLength = len(registers)
    shadowSpace = 32
    maximumAllocationReached = 0
    contextStackData = {}
    callOccured = False
    previousContext = None
    synchronizationIndexTable = {}
    currentIndicesChanged = set()

    def GetAllocInd() : return set(Managment.alocatedIndices)

    def Feed(index : Index) -> Usepack:
        if not isinstance(index, Index) : return str(index) 
        for mapping in Managment.mapping:
            if mapping.index == index:
                return mapping.Feed()

    def GetAvailibleByPurpose(purpose : str) -> list[Usepack]:
        print(f"Requested all {purpose} usepacks.")
        result = []
        for map in Managment.mapping:
            if len(map.map) == 0: continue
            if map.map[0].purpose == purpose:
                result += [map.Feed()]
        return result

    def SetMapping(index : Index, usepack : Usepack):
        found = False
        for mapping in Managment.mapping:
            found = mapping.index == index
            if found: 
                mapping.map += [usepack]
                break
        print(f"  Mapping [{index.index}] is set to {[reg.name for reg in usepack.registers]} to {usepack.purpose}")
        Managment.currentIndicesChanged.add(index)
        if not found: Managment.mapping += [Mapping(index, [usepack])]

    def GetRegisterByName(name : str) -> Register:
        for reg in Managment.registers:
            if reg.name == name: return reg
        return Register("NOT FOUND")

    def GetLastPresense(index : Index) -> Register:
        for mapping in Managment.mapping:
            if mapping.index == index: return mapping.map[-1].registers[-1]

    def GetLatestUsepackExclusive(index : Index, purpose : str) -> Register:
        for mapping in Managment.mapping:
            if mapping.index != index : continue
            for usepack in mapping.map:
                if usepack.purpose == purpose: return usepack.registers[-1]        

    def GetFirstPresense(index : Index) -> Register:
        for mapping in Managment.mapping:
            if mapping.index == index: return mapping.map[0].registers[-1]

    def GetFreeStackRegister() -> Register:
        for register in Managment.registers:
            if register.isStackAllocated and not register.occupation: return register
        shift = Managment.shadowSpace + (len(Managment.registers) - Managment.defaultLength) * 8
        if shift > Managment.maximumAllocationReached: 
            Managment.maximumAllocationReached = shift
        new = Register(f"[rsp+{shift}]", isa=True)
        Managment.registers += [new]
        return new
        
    def GetFreeRegister() -> Register:
        for register in Managment.registers:
            if not register.occupation:
                return register
        stack = Managment.GetFreeStackRegister()
        return stack
    
    def GetOccupiedRegisters() -> list[Register]:
        result = []
        for register in Managment.registers:
            if register.occupation : result += [register]
        return result

    def MapRegisters(context : Context):
        Managment.currentIndicesChanged = set()
        if context.master == None : Managment.maximumAllocationReached = 0
        #for index in context.indices:
        #    if index.isAsrgument:
        #        reg = Managment.GetFreeRegister()
        #        reg.occupation = True
        #        Managment.alocatedIndices += [index]
        #        Managment.SetMapping(index, reg)
        #        print(f"Allocated [{index.index}] into {reg.name} as an argument")

        for pseudo in context.data:

            if pseudo.operation == "sync" :#and not context.isDeadEnd:
                print("Syncing...")
                print(f"Potential {[ind.index for ind in Managment.currentIndicesChanged]}")
                synced = []
                for ind in Managment.currentIndicesChanged:
                    if (not ind.mentioned > 0) and not context.forceSync : continue
                    if ind in Managment.synchronizationIndexTable:
                        print(f"  Found syncpoint for [{ind.index}]. Adding...")
                        sp = Managment.GetLastPresense(ind)
                        Managment.SetMapping(ind, Usepack([sp, Managment.synchronizationIndexTable[ind]], "SYNC"))
                        Managment.alocatedIndices += [ind]
                        sp.occupation = True
                    else:
                        print(f"  Creating syncpoint for [{ind.index}]...")
                        if Managment.GetFirstPresense(ind) == Managment.GetLastPresense(ind): 
                            print("Already in sync. Passing by.")
                            continue
                        sp = Managment.GetLastPresense(ind)
                        Managment.SetMapping(ind, Usepack([sp,Managment.GetFirstPresense(ind)], "SYNC"))
                        Managment.synchronizationIndexTable.update({ind: Managment.GetFirstPresense(ind)})
                        Managment.alocatedIndices += [ind]
                        sp.occupation = True
                    synced += [ind]
                print("Injecting sync info into pseudo instruction.")
                pseudo.operands = synced if synced != [] else ["used"]
                print(f"Succesfuly synced {[ind.index for ind in synced]}")

            unique : list[Index] = pseudo.involved
            if unique != []:

                #print("unique "+', '.join([str(ind.index) for ind in unique]))
                #print("involved "+', '.join(['['+str(ind.index)+"]" for ind in pseudo.involved]))
                print(f"Allocating for {pseudo.operation} involving {[ind.index if isinstance(ind, Index) else ind for ind in pseudo.involved]}...")
                for index in unique:
                    if not index in Managment.GetAllocInd() and not(pseudo.operation == "call" ):#and pseudo.loadInto == index):
                        free = Managment.GetFreeRegister()
                        free.occupation = True
                        print('[NEW!]',end='')
                        Managment.SetMapping(index, Usepack([free], "GENERAL"))
                        Managment.alocatedIndices += [index]
                        #print(f"Allocated [{index.index}] into {free.name}")
                    else:
                        if not(pseudo.operation == "call"):# and pseudo.loadInto == index):
                            stay = Managment.GetLastPresense(index)
                            stay.occupation = True
                            Managment.SetMapping(index, Usepack([stay],"GENERAL"))
                
                if not pseudo.operation == "call" or True:
                    for index in unique:
                        index.mentioned -= 1

                        if index.mentioned == 0:
                            for i, ind in enumerate(Managment.alocatedIndices):
                                if ind == index : 
                                    Managment.alocatedIndices.pop(i)
                                    break
                            Managment.GetLastPresense(index).occupation = False
                            print(f"Last mention of [{index.index}] is eleminated. Marking {Managment.GetLastPresense(index).name} as free.")
                        
                if pseudo.operation == "call":
                    print("Handling call operation:")
                    Managment.callOccured = True
                    pseudo.Format()

                    for index in Managment.GetAllocInd():
                        if (not Managment.GetLastPresense(index).isStackAllocated) and index != pseudo.loadInto and not index.isTemp: 
                            print(f"Swaping to stack space for [{index.index}] ({index.repr})")
                            #if Managment.GetLastPresense(index) == Managment.GetFreeStackRegister(): continue
                            new = Managment.GetFreeStackRegister()
                            Managment.SetMapping(index, Usepack([Managment.GetLatestUsepackExclusive(index, "GENERAL"), Managment.GetFreeStackRegister()],"PRESERVE"))
                            new.occupation = True

                    for index in pseudo.operands[1:len(pseudo.operands)]:
                        if isinstance(index, Index) : 
                            Managment.SetMapping(index, Usepack([Managment.GetLastPresense(index)],"LOAD"))
                            index.mentioned -= 1

                    for reg in Managment.registers:
                        if not reg.isStackAllocated : reg.occupation = False
                
                    out = Managment.GetRegisterByName("rax")
                    out.occupation = True
                    Managment.SetMapping(pseudo.loadInto, Usepack([out], "GENERAL"))
                    Managment.alocatedIndices += [pseudo.loadInto]
                    pseudo.loadInto.mentioned -= 1


        owner = context if context.master == None else context.master
        if Managment.callOccured and Managment.maximumAllocationReached == 0: Managment.maximumAllocationReached = -1
        if owner in Managment.contextStackData:
            if Managment.contextStackData[owner] < Managment.maximumAllocationReached : 
                Managment.contextStackData[owner] = Managment.maximumAllocationReached
        else:
            Managment.contextStackData.update({owner: Managment.maximumAllocationReached})
        

        #print("Leftovers from content data >>>",set().add({len(ind.mentions), ind.mentioned} for ind in context.indices))
        print(f"Allocated                   >>> {[ind.index for ind in Managment.alocatedIndices]}")

class AssemblyPart:
    def Format(self) -> str:
        pass

class Instruction(AssemblyPart):
    specific = ["cmp", "add", "sub", "mul", "div"]
    def __init__(self, operation : str, *operands : list[Register], comment : str = ''):
        self.operation = operation
        self.operands = operands
        self.comment = comment

        print(operation, operands)
        if operation in Instruction.specific and len(operands) == 2:
            if isinstance(operands[0], Register) and operands[0].isStackAllocated and isinstance(operands[1], Register) and operands[1].isStackAllocated:
                temp = Managment.GetRegisterByName("r9")
                Instruction("mov", temp, operands[0])
                self.operands = [temp,self.operands[1]]

        Translator.assembly += [self]

    def Format(self):
        return f"  {self.operation} {', '.join([op.name if isinstance(op, Register) else str(op) for op in self.operands])} ;{self.comment}\n"

class Header(AssemblyPart):
    def __init__(self, *name):
        self.name = ' '.join(name)
        Translator.assembly += [self]

    def Format(self):
        return self.name+"\n"
        
class Translator:

    assembly : list[AssemblyPart] = []

    typeSizeMapping = {
        "Integer": 4,
        "Float": 4,
        "Double": 4,
        "Long": 8
    }

    conditionalMapping = {
        "And": "COMPLEX",
        "Or":  "COMPLEX",
        "Not": "COMPLEX",
        "Xor": "COMPLEX",

        "Equals":    "je" , 
        "GreaterOE": "jge", 
        "LessOE":    "jle", 
        "Greater":   "jg" , 
        "Less":      "jl" 
    }

    mathMapping = {

        "Plus": "add",
        "Minus": "sub",
        "Times": "imul",
        "Divide": "div",

        "Negative": "neg",
        "MemAccess": None
    }

    reverseMapping = {
        "Equals":    None, 
        "GreaterOE": "Less", 
        "LessOE":    "Greater", 
        "Greater":   "LessOE" , 
        "Less":      "GreaterOE"         
    }

    indicesInUse = []

    def Translate(data : list[Context]):
        for ctx in data:
            Managment.MapRegisters(ctx)
            if ctx.master == None: 
                if ctx.name != '' : 
                    Header(f"global {ctx.name}")
        Header("section .text")

        printMapping(Managment.mapping)
        print(Managment.contextStackData)
        IR(data)

        for ctx in data:
            if len(ctx.data) == 0: continue
            returned = False
            Header(ctx.name+":" if ctx.name != '' else '')
            frame = Managment.contextStackData[ctx.master if ctx.master != None else ctx]
            if frame > 0:
                frame += 8 if frame != -1 else 0
                alignment = frame if (frame % 16) == 8 else frame + 8
            elif frame == -1 : alignment = 40
            elif frame == 0 : alignment = 0
            if alignment > 0 and ctx.master == None: Instruction("sub","rsp", alignment)

            for pseudo in ctx.data:
                if pseudo.operation == None:
                    toLoad = Managment.Feed(pseudo.operands[0])
                    toLoad = toLoad.registers[0] if isinstance(toLoad, Usepack) else toLoad
                    Instruction("mov", Managment.Feed(pseudo.loadInto).registers[0], toLoad, comment="direct move command")

                elif pseudo.operation == "sync" and not pseudo.operands[0] == "used":
                    print('Synchronizing.')
                    for pack in Managment.GetAvailibleByPurpose("SYNC"):
                        if not returned: Instruction("mov", pack.registers[1], pack.registers[0], comment="syncpoint")

                elif pseudo.operation == "input" and not returned:
                    Managment.Feed(pseudo.loadInto).registers[0]
                    
                elif pseudo.operation == "return":
                    if len(pseudo.operands) > 0: reg = Managment.Feed(pseudo.operands[0])
                    else:
                        Instruction("ret")
                        continue
                    reg = reg.registers[0] if isinstance(reg, Usepack) else reg
                    if not isinstance(reg, Register) or reg.name != "rax":
                        Instruction("mov", "rax", reg)
                    if alignment > 0 : Instruction("add", "rsp", alignment)
                    Instruction("ret")
                    returned = True

                elif pseudo.operation == "access":
                    ptr = Managment.Feed(pseudo.operands[0])
                    ptr = ptr.registers[0] if isinstance(ptr, Usepack) else ptr

                    val = Managment.Feed(pseudo.operands[1])
                    val = val.registers[0] if isinstance(val, Usepack) else val

                    Instruction("mov", f"[{ptr.name}]", val)

                elif pseudo.operation == "External":
                    Header("extern", pseudo.operands[0])

                elif pseudo.operation == "call":
                    for usepack in Managment.GetAvailibleByPurpose("PRESERVE"):
                        
                        f = usepack.registers[0]
                        s = usepack.registers[1]
                        if s != f:
                            Instruction("mov", s, f, comment="call preserving")

                    trueops = pseudo.operands[1:len(pseudo.operands)]
                    dests = []
                    regs = []
                    for i, op in enumerate(trueops):
                        des = Managment.registers[i]
                        reg = Managment.Feed(op)
                        reg = reg.registers[0] if isinstance(reg, Usepack) else reg
                        if des != reg:
                            dests += [des]
                            regs += [reg]


                        
                    for i, des in enumerate(dests):
                        reg = regs[i]
                        if des in regs[i:len(regs)]:
                            dests.pop(i)
                            regs.pop(i)
                            dests += [des]
                            regs += [reg]

                    for i, des in enumerate(dests):
                        reg = regs[i]
                        if des == reg : continue
                        Instruction("mov", des, reg, comment="argument loading")
                    Instruction("call", pseudo.operands[0])

                elif pseudo.operation == "jump" and not returned :
                    if "reverse" in pseudo.operands:
                        Instruction("jmp", pseudo.operands[1])
                    elif pseudo.operands[0] != True:
                        Instruction(Translator.conditionalMapping[pseudo.operands[0].operation], pseudo.operands[1])
                    else:
                        Instruction("jmp", pseudo.operands[1])
                        continue

                elif pseudo.operation in Translator.mathMapping:
                    if pseudo.operation == "MemAccess":
                        ptr = Managment.Feed(pseudo.operands[0])
                        ptr = ptr.registers[0] if isinstance(ptr, Usepack) else ptr
                        Instruction("mov", Managment.Feed(pseudo.loadInto).registers[0], f"[{ptr.name}]")                     
                    elif not pseudo.loadInto in pseudo.operands:
                        self = Managment.Feed(pseudo.loadInto).registers[0]
                        val = Managment.Feed(pseudo.operands[0])
                        val = val.registers[0] if isinstance(val, Usepack) else val
                        Instruction("mov", self, val, comment="math temporary")
                        if len(pseudo.operands) == 2:
                            operand = Managment.Feed(pseudo.operands[1])
                            operand = operand.registers[0] if isinstance(operand, Usepack) else operand
                            Instruction(Translator.mathMapping[pseudo.operation], self, operand)
                        elif len(pseudo.operands) == 1:
                            Instruction(Translator.mathMapping[pseudo.operation], self)
                    else:
                        Instruction(Translator.mathMapping[pseudo.operation], Managment.Feed(pseudo.operands[0]).registers[0], Managment.Feed(pseudo.operands[1]).registers[0])

                elif pseudo.operation in Translator.conditionalMapping:
                    print(pseudo.operation, *pseudo.operands)
                    f, s = Managment.Feed(pseudo.operands[0]), Managment.Feed(pseudo.operands[1])
                    f = f.registers[0] if isinstance(f, Usepack) else str(f) 
                    s = s.registers[0] if isinstance(s, Usepack) else str(s) 
                    Instruction("cmp", f, s)

        #for ex in externlist:
        #    Translator.assembly.insert(size, ex)
