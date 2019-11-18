# Author: Jordan Chapman
# Aiming to be a bit faster
# Saving registers in a dictionary for faster getting/setting

# Register table; binary code for each register
REG_TABLE = {"000":"b",
             "001":"c",
             "010":"d",
             "011":"e",
             "100":"h",
             "101":"l",
             "110":"hl",
             "111":"a"}

class Memory:
    # Little memory object. Indexible (mem[0]). Creates addresses when needed
    def __init__(self):
        self.memory = {}

    def __getitem__(self, key):
        try:
            return self.memory[key]
        except:
            self.memory[key] = 0
            return 0

    def __setitem__(self, key, value):
        self.memory[key] = value

class Registers:
    """ Registers object, keeps track of CPU registers """
    # No hex should make it to the registers
    def __init__(self):
        self.registers = {"b":0,"c":0,"d":0,"e":0,
                          "h":0,"l":0,"a":0,
                          "sp":0,"pc":0}
        self.flags = [0,0,0,0] # Zero, Sub, Half-Carry, Carry

    def get_b(self):
        return self.registers["b"]
    def set_b(self, val):
        self.registers["b"] = val
    b = property(get_b, set_b)
    
    def get_c(self):
        return self.registers["c"]
    def set_c(self, val):
        self.registers["c"] = val
    c = property(get_c, set_c)
    
    def get_d(self):
        return self.registers["d"]
    def set_d(self, val):
        self.registers["d"] = val
    d = property(get_d, set_d)
    
    def get_e(self):
        return self.registers["e"]
    def set_e(self, val):
        self.registers["e"] = val
    e = property(get_e, set_e)
    
    def get_h(self):
        return self.registers["h"]
    def set_h(self, val):
        self.registers["h"] = val
    h = property(get_h, set_h)
    
    def get_l(self):
        return self.registers["l"]
    def set_l(self, val):
        self.registers["l"] = val
    l = property(get_l, set_l)
    
    def get_a(self):
        return self.registers["a"]
    def set_a(self, val):
        self.registers["a"] = val
    a = property(get_a, set_a)
    
    def get_pc(self):
        return self.registers["pc"]
    def set_pc(self, val):
        self.registers["pc"] = val
    pc = property(get_pc, set_pc)
    
    def get_sp(self):
        return self.registers["sp"]
    def set_sp(self, val):
        self.registers["sp"] = val
    sp = property(get_sp, set_sp)

    def get_f(self):
        f=self.flags[0]*128+self.flags[1]*64+self.flags[2]*32+self.flags[3]*16
        return f
    def set_f(self, f):
        f = bin(f)[2:]
        f = "0"*(8-len(f)) + f
        self.flags[0] = f[0] == "1"
        self.flags[1] = f[1] == "1"
        self.flags[2] = f[2] == "1"
        self.flags[3] = f[3] == "1"
    f = property(get_f, set_f)

    # Dual-register getters/setters for ease of use
    def get_bc(self):
        return self.b*256 + self.c
    def set_bc(self, bc):
        self.b = bc//256%256
        self.c = bc%256
    bc = property(get_bc, set_bc)

    def get_de(self):
        return self.d*256 + self.e
    def set_de(self, de):
        self.d = de//256%256
        self.e = de%256
    de = property(get_de, set_de)

    def get_hl(self):
        return self.h*256 + self.l
    def set_hl(self, hl):
        self.h = hl//256%256
        self.l = hl%256
    hl = property(get_hl, set_hl)

    def get_af(self):
        return self.a*256 + self.f
    def set_af(self, af):
        self.a = af//256%256
        self.f = af%256
    af = property(get_af, set_af)

    def get_register(self, reg):
        """
        Gets a string:'reg' and returns
        the value of the corresponding register
        """
        if reg == "f":
            return self.f
        else:
            return self.registers[reg]

    def set_register(self, reg, val):
        """
        """
        #print("Set register %s to %s" % (reg,val))
        if reg == "f":
            self.f = val
        else:
            self.registers[reg] = val

    def load(self, reg, val):
        """ Load value "val" into register "reg" """
        self.set_register(reg, val)

    def inc(self, reg, setFlags):
        self.set_register(reg, self.get_register(reg)+1)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def dec(self, reg, setFlags):
        self.set_register(reg, self.get_register(reg)-1)
        if setFlags:
            self.flags[1] = 1 # Subtraction flag

    def add(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)+val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def sub(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)-val)
        if setFlags:
            self.flags[1] = 1 # Subtraction flag

    def _and(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)&val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def _or(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)|val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def xor(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)^val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def cp(self, reg, val, setFlags):
        if setFlags:
            self.flags[1] = 1 # Subtraction flag

    def test(self, val, bit):
        val = bin(val)[2:]
        val = "0"*(8-len(val)) + val
        self.flags[0] = val[bit] != "1"
        self.flags[1] = 0
        self.flags[2] = 1
    

class CPU:
    def __init__(self):
        self.reg = Registers()
        self.mem = Memory()

    def LD(self, reg, bts):
        self.reg.load(reg, bts)

    def INC(self, reg, setFlags=False):
        self.reg.inc(reg, setFlags)

    def DEC(self, reg, setFlags=False):
        self.reg.dec(reg, setFlags)

    def ADD(self, reg, val, setFlags=False):
        self.reg.add(reg, val, setFlags)

    def ADC(self, reg, val, setFlags=False):
        self.reg.add(reg, val+self.reg.flags[3], setFlags)

    def SUB(self, reg, val, setFlags=False):
        self.reg.sub(reg, val, setFlags)

    def SBC(self, reg, val, setFlags=False):
        self.reg.sub(reg, val+self.reg.flags[3], setFlags)

    def AND(self, reg, val, setFlags=False):
        self.reg._and(reg, val, setFlags)

    def XOR(self, reg, val, setFlags=False):
        self.reg.xor(reg, val, setFlags)

    def OR(self, reg, val, setFlags=False):
        self.reg._or(reg, val, setFlags)

    def CP(self, reg, val, setFlags=False):
        self.reg.cp(reg, val, setFlags)

    def cycle(self, rom, silent=False):
        pc, delay = self.exe(rom, silent)
        self.reg.pc += pc
        return delay

    def PREFIX_CB(self, bts):
        """ Does a "Prefix CB" table operation, and returns the cycle duration"""
        time = 8
        bins = bin(int(bts,16))[2:]
        bins = "0"*(8-len(bins)) + bins
        type_bits = bins[0:2]
        
        level_bits = bins[2:5]
        bit = int(level_bits, 2)
        
        reg_bits = bins[5:8]
        register = REG_TABLE[reg_bits]

        # CB Table

        if type_bits == "00": # Rotations
            pass

        if type_bits == "01": # Test bits
            if register == "hl":
                time = 16
                val = self.mem[self.reg.hl]
            else:
                val = self.reg.get_register(register)
            self.reg.test(val,bit)

        if type_bits == "10": # Resets
            if register == "hl":
                time = 16
                bits = bin(self.mem[self.reg.hl])[2:]
                bits = bits[:bit] + "0" + bits[bit:]
                self.mem[self.reg.hl] = int(bits,2)
            else:
                bits = bin(self.reg.get_register(register))[2:]
                bits = bits[:bit] + "0" + bits[bit:]
                self.reg.set_register(register, int(bits,2))

        if type_bits == "11": # Sets
            if register == "hl":
                time = 16
                bits = bin(self.mem[self.reg.hl])[2:]
                bits = bits[:bit] + "1" + bits[bit:]
                self.mem[self.reg.hl] = int(bits,2)
            else:
                bits = bin(self.reg.get_register(register))[2:]
                bits = bits[:bit] + "1" + bits[bit:]
                self.reg.set_register(register, int(bits,2))

        return time

    def exe(self, rom, silent=False):
        """
        Excecute code at position "pos" in the rom
        Parameter "silent" - Prints info if False
        Returns length in bytes, and cycles used.
        """
        byte = rom[self.reg.pc].upper() # Reading byte from ROM
        ref = byte[0] # Row on opcode table
        op = byte[1] # Column on opcode table
        
        if not silent:
            print("Excecuting opcode '%s' at position '%s'" % (byte,hex(self.reg.pc)))

        if ref in ["4","5","6","7"]: # LD operations + HALT
            # Read as binary string
            # Example (01001010)
            #   First 2 bits (01) = LD operations
            #   Next 3 bits (001) = C register
            #   Last 3 bits (010) = D register
            # 01001010 = Load into C from D
            
            bits = bin(int(byte,16))[2:]
            bits = "0"*(8-len(bits)) + bits
            reg_dest = REG_TABLE[bits[2:5]]
            reg_source = REG_TABLE[bits[5:8]]
            if reg_dest == "hl" and reg_source == "hl":
                # TODO HALT
                return 1,4
            elif reg_dest == "hl":
                self.mem[self.reg.hl] = self.reg.get_register(reg_source)
                return 1,8
            elif reg_source == "hl":
                self.LD(reg_dest, self.mem[self.reg.hl])
                return 1,8
            else:
                self.LD(reg_dest, self.reg.get_register(reg_source))
                return 1,4

        elif ref in ["8","9","A","B"]: # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
            bits = bin(int(byte,16))[2:]
            bits = "0"*(8-len(bits)) + bits
            operation = bits[2:5]
            reg_source = REG_TABLE[bits[5:8]]

            if reg_source == "hl":
                val = self.mem[self.reg.hl]
            else:
                val = self.reg.get_register(reg_source)
            
            if operation == "000": # ADD
                self.ADD("a", val)
            elif operation == "001": # ADC
                self.ADC("a", val)
            elif operation == "010": # SUB
                self.SUB("a", val)
            elif operation == "011": # SBC
                self.SBC("a", val)
            elif operation == "100": # AND
                self.AND("a", val)
            elif operation == "101": # XOR
                self.XOR("a", val)
            elif operation == "110": # OR
                self.OR("a", val)
            elif operation == "111": # CP
                self.CP("a", val)
            
            if reg_source == "hl":
                return 1,8
            return 1,4

        elif ref == "0":
            if op == "0": # NOP
                return 1,4

            elif byte == "01": # LD BC,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("bc",int(bts, 16))
                return 3,12

            elif byte == "02": # LD (BC),A
                self.mem[self.reg.bc] = self.reg.a
                return 1,8

            elif byte == "03": # INC BC
                self.INC("bc")
                return 1,8

            elif byte == "04": # INC B
                self.INC("b")
                return 1,4

            elif byte == "05": # DEC B
                self.DEC("b")
                return 1,4

            elif byte == "06": # LD B,d8
                self.LD("b",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "07": # RLCA
                # TODO: Rotate 'a' left, copy bit 7 to carry and a[0]
                a = bin(self.reg.a)[2:]
                self.reg.flags[3] = a[0] == "1"
                a = a[1:] + a[0]
                return 1,4

            elif byte == "08": # LD (a16),SP
                self.mem[int(rom[self.reg.pc+1],16)] = self.reg.sp
                return 3,20

            elif byte == "09": # ADD HL,BC
                self.ADD("hl",self.reg.bc, setFlags = False)
                return 1,8

            elif byte == "0A": # LD A,(BC)
                self.mem[self.reg.a] = self.reg.bc
                return 1,8

            elif byte == "0B": # DEC BC
                self.DEC("bc")
                return 1,8

            elif byte == "0C": # INC C
                self.INC("c")
                return 1,4

            elif byte == "0D": # DEC C
                self.DEC("c")
                return 1,4

            elif byte == "0E": # LD C,d8
                self.LD("c",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "0F": # RRCA
                # TODO: Rotate 'a' right, copy bit 0 to carry and a[7]
                return 1,4

        elif ref == "1":
            if byte == "10": # STOP
                print("STOPPING")
                return 2,4
            
            elif byte == "11": # LD DE,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("de",int(bts, 16))
                return 3,12

            elif byte == "12": # LD (DE),A
                self.mem[self.reg.de] = self.reg.a
                return 1,8

            elif byte == "13": # INC DE
                self.INC("de")
                return 1,8

            elif byte == "14": # INC D
                self.INC("d")
                return 1,4

            elif byte == "15": # DEC D
                self.DEC("d")
                return 1,4

            elif byte == "16": # LD D,d8
                self.LD("d",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "17": # RLA
                # TODO: Rotate 'a' left, copy bit 7 to carry, copy carry to a[0]
                return 1,4

            elif byte == "18": # JR r8
                jump = int(rom[self.reg.pc+1], 16)
                if jump > 127: jump -= 255
                jump = 0 # TODO
                return 2+jump,12

            elif byte == "19": # ADD HL,DE
                self.ADD("hl",self.reg.de, setFlags = False)
                return 1,8

            elif byte == "1A": # LD A,(DE)
                self.mem[self.reg.a] = self.reg.de
                return 1,8

            elif byte == "1B": # DEC DE
                self.DEC("DE")
                return 1,8

            elif byte == "1C": # INC E
                self.INC("e")
                return 1,4

            elif byte == "1D": # DEC E
                self.DEC("e")
                return 1,4

            elif byte == "1E": # LD E,d8
                self.LD("e",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "1F": # RRA
                # TODO: Rotate 'a' right, copy bit 0 to carry, copy carry to a[7]
                return 1,4

        elif ref == "2":
            if byte == "20": # JR NZ,r8
                if not self.reg.flags[0]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    jump = 0 # TODO
                    return 2+jump, 12
                else:
                    return 2, 8

            elif byte == "21": # LD HL,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("hl",int(bts,16))
                return 3,12

            elif byte == "22": # LD (HL+),A
                self.mem[self.reg.hl] = self.reg.a
                self.reg.hl += 1
                return 1,8

            elif byte == "23": # INC HL
                self.INC("hl")
                return 1,8

            elif byte == "24": # INC H
                self.INC("h")
                return 1,4

            elif byte == "25": # DEC H
                self.DEC("h")
                return 1,4

            elif byte == "26": # LD H,d8
                self.LD("h",int(rom[self.reg.pc+1],16))
                return 2,8
            
            elif byte == "27": # DAA
                # TODO
                return 1,4
                
            elif byte == "28": # JR Z,r8
                if self.reg.flags[3]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    jump = 0 # TODO
                    return 2+jump, 12
                else:
                    return 2, 8

            elif byte == "29": # ADD HL,HL
                self.ADD("hl",self.reg.hl, setFlags=False)
                return 1,8

            elif byte == "2A": # LD A,(HL+)
                self.mem[self.reg.a] = self.reg.hl
                self.reg.hl += 1
                return 1,8

            elif byte == "2B": # DEC HL
                self.DEC("hl")
                return 1,8

            elif byte == "2C": # INC L
                self.INC("l")
                return 1,4

            elif byte == "2D": # DEC L
                self.DEC("l")
                return 1,4

            elif byte == "2E": # LD L,d8
                self.LD("l",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "2F": # CPL
                # TODO
                return 1,4
        
        elif ref == "3":
            if byte == "30": # JR NC,r8
                if not self.reg.flags[3]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    jump = 0 # TODO
                    return 2+jump, 12
                else:
                    return 2, 8
            
            elif byte == "31": # LD SP,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("sp",int(bts, 16))
                return 3,12

            elif byte == "32": # LD (HL-),A
                self.mem[self.reg.hl] = self.reg.a
                self.reg.hl -= 1
                return 1,8

            elif byte == "33": # INC SP
                self.INC("sp")
                return 1,8

            elif byte == "34": # INC (HL)
                self.INC("hl")
                return 1,4

            elif byte == "35": # DEC (HL)
                self.DEC("hl")
                return 1,4

            elif byte == "36": # LD (HL),d8
                self.mem[self.reg.hl] = int(rom[self.reg.pc+1],16)
                return 2,12

            elif byte == "37":
                self.reg.flags[3] = 1
                return 1,4

            elif byte == "38": # JR C,r8
                if self.reg.flags[3]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    jump = 0 # TODO
                    return 2+jump, 12
                else:
                    return 2, 8

            elif byte == "39": # ADD HL,SP
                self.ADD("hl",self.reg.sp, setFlags=False)
                return 1,8

            elif byte == "3A": # LD A,(HL-)
                self.mem[self.reg.a] = self.reg.hl
                self.reg.hl -= 1
                return 1,8

            elif byte == "3B": # DEC SP
                self.DEC("sp")
                return 1,8

            elif byte == "3C": # INC A
                self.INC("a")
                return 1,4

            elif byte == "3D": # DEC A
                self.DEC("a")
                return 1,4

            elif byte == "3E": # LD A,d8
                self.LD("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "3F": # CCF
                self.reg.flags[3] = not self.reg.flags[3]
                return 1,4

        elif ref == "C":
            if byte == "C0":
                # TODO
                pass

            elif byte == "C1": # POP BC
                self.reg.c = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.b = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif byte == "C2":
                # TODO
                pass

            elif byte == "C3":
                # TODO
                pass

            elif byte == "C4":
                # TODO
                pass

            elif byte == "C5": # PUSH BC
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.b
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.c
                return 1,16

            elif byte == "C6":
                # TODO
                pass

            elif byte == "C7":
                # TODO
                pass

            elif byte == "C8": # RET Z
                # TODO: Stack stuff
                if self.reg.flags[0]:
                    return 1,20
                return 1,8

            elif byte == "C9": # RET
                self.reg.pc = self.mem[self.reg.sp]
                return 1,16

            elif byte == "CA":
                # TODO
                pass

            elif byte == "CB": # PREFIX CB
                t = self.PREFIX_CB(rom[self.reg.pc+1])
                return 2,t

            elif byte == "CC": # CALL Z,a16
                # TODO CALLS
                if self.reg.flags[0]:
                    return 3,24
                return 3,12

            elif byte == "CD": # CALL a16
                # TODO CALLS
                return 3,24

            elif byte == "CE": # ADC A,d8
                self.ADC("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "CF":
                # TODO
                pass

        elif ref == "D":
            if byte == "D0":
                # TODO
                pass

            elif byte == "D1": # POP DE
                self.reg.e = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.d = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif byte == "D2":
                # TODO
                pass

            elif byte == "D3":
                # TODO
                pass

            elif byte == "D4":
                # TODO
                pass

            elif byte == "D5": # PUSH DE
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.d
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.e
                return 1,16

            elif byte == "D6":
                # TODO
                pass

            elif byte == "D7":
                # TODO
                pass

            elif byte == "D8": # RET C
                # TODO: Stack stuff
                if self.reg.flags[3]:
                    return 1,20
                return 1,8

            elif byte == "D9": # RETI
                # TODO: Stack stuff
                return 1,16

            elif byte == "DA":
                # TODO
                pass

            elif byte == "DB":
                # TODO
                pass

            elif byte == "DC": # CALL C,a16
                # TODO CALLS
                if self.reg.flags[3]:
                    return 3,24
                return 3,12

            elif byte == "DD":
                # TODO
                pass

            elif byte == "DE": # SBC A,d8
                self.SBC("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "DF":
                # TODO
                pass

        elif ref == "E":
            if byte == "E0": # LDH (a8),A
                self.mem[self.reg.a] = int(rom[self.reg.pc+1],16)
                return 2,12

            elif byte == "E1": # POP HL
                self.reg.l = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.h = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif byte == "E2": # LD (C),A
                self.mem[self.reg.c] = self.reg.a
                return 2,8

            elif byte == "E3":
                # TODO
                pass

            elif byte == "E4":
                # TODO
                pass

            elif byte == "E5": # PUSH HL
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.h
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.l
                return 1,16

            elif byte == "E6":
                # TODO
                pass

            elif byte == "E7":
                # TODO
                pass

            elif byte == "E8":
                # TODO
                pass

            elif byte == "E9":
                # TODO
                pass

            elif byte == "EA": # LD (a16),A
                # TODO: Address bytes right order in RAM?
                return 3,16

            elif byte == "EB":
                # TODO
                pass

            elif byte == "EC":
                # TODO
                pass

            elif byte == "ED":
                # TODO
                pass

            elif byte == "EE": # XOR d8
                self.XOR("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "EF":
                # TODO
                pass

        elif ref == "F":
            if byte == "F0": # LDH A,(a8)
                # TODO: Am I right on this? What's the H for?
                self.LD("a", self.mem[int(rom[self.reg.pc+1],16)])
                return 2,12

            elif byte == "F1": # POP AF
                self.reg.f = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.a = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif byte == "F2": # LD A,(C)
                self.LD("a", self.mem[self.reg.c])
                return 2,8

            elif byte == "F3": # DI
                # TODO: Reset flipflops?
                return 1,4

            elif byte == "F4":
                # TODO
                pass

            elif byte == "F5": # PUSH AF
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.a
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.f
                return 1,16

            elif byte == "F6":
                # TODO
                pass

            elif byte == "F7":
                # TODO
                pass

            elif byte == "F8":
                # TODO
                pass

            elif byte == "F9":
                # TODO
                pass

            elif byte == "FA": # LD A, (a16)
                # TODO: Address bytes right order in RAM?
                return 3,16

            elif byte == "FB":
                # TODO
                pass

            elif byte == "FC":
                # TODO
                pass

            elif byte == "FD":
                # TODO
                pass

            elif byte == "FE": # CP d8
                self.CP("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif byte == "FF":
                # TODO
                pass
        
        else:
            input("UNIMPLEMENTED OPCODE: " + byte)
            return 1,0
