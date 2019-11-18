# Author: Jordan Chapman

# DEPRECATED in favor of cpu2

REG_TABLE = {"000":"b",
            "001":"c",
            "010":"d",
            "011":"e",
            "100":"h",
            "101":"l",
            "110":"hl",
            "111":"a"}

class Memory:
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
    # No hex should make it to the registers
    def __init__(self):
        self.a = 0
        self.b = 0
        self.c = 0
        self.d = 0
        self.e = 0
        self.h = 0
        self.l = 0
        self.sp = 0
        self.pc = 0
        self.flags = [0,0,0,0] # Zero, Sub, Half-Carry, Carry

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
        if reg == "a": return self.a
        if reg == "b": return self.b
        if reg == "c": return self.c
        if reg == "d": return self.d
        if reg == "e": return self.e
        if reg == "f": return self.f
        if reg == "h": return self.h
        if reg == "l": return self.l
        if reg == "sp": return self.sp
        if reg == "af": return self.af
        if reg == "bc": return self.bc
        if reg == "de": return self.de
        if reg == "hl": return self.hl

    def set_register(self, reg, val):
        #print("Set register %s to %s" % (reg,val))
        if reg == "a": self.a = val
        if reg == "b": self.b = val
        if reg == "c": self.c = val
        if reg == "d": self.d = val
        if reg == "e": self.e = val
        if reg == "f": self.f = val
        if reg == "h": self.h = val
        if reg == "l": self.l = val
        if reg == "sp": self.sp = val
        if reg == "af": self.af = val
        if reg == "bc": self.bc = val
        if reg == "de": self.de = val
        if reg == "hl": self.hl = val

    def load(self, reg, val):
        """ Load value "val" into register "reg" """
        self.set_register(reg, val)

    def inc(self, reg, setFlags=True):
        self.set_register(reg, self.get_register(reg)+1)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def dec(self, reg, setFlags=True):
        self.set_register(reg, self.get_register(reg)-1)
        if setFlags:
            self.flags[1] = 1 # Subtraction flag

    def add(self, reg, val, setFlags=True):
        self.set_register(reg, self.get_register(reg)+val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def sub(self, reg, val, setFlags=True):
        self.set_register(reg, self.get_register(reg)-val)
        if setFlags:
            self.flags[1] = 1 # Subtraction flag

    def _and(self, reg, val, setFlags=True):
        self.set_register(reg, self.get_register(reg)&val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def _or(self, reg, val, setFlags=True):
        self.set_register(reg, self.get_register(reg)|val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def xor(self, reg, val, setFlags=True):
        self.set_register(reg, self.get_register(reg)^val)
        if setFlags:
            self.flags[1] = 0 # Subtraction flag

    def cp(self, reg, val, setFlags=True):
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

    def INC(self, reg):
        self.reg.inc(reg)

    def DEC(self, reg):
        self.reg.dec(reg)

    def ADD(self, reg, val):
        self.reg.add(reg, val)

    def ADC(self, reg, val):
        self.reg.add(reg, val+self.reg.flags[3])

    def SUB(self, reg, val):
        self.reg.sub(reg, val)

    def SBC(self, reg, val):
        self.reg.sub(reg, val+self.reg.flags[3])

    def AND(self, reg, val):
        self.reg._and(reg, val)

    def XOR(self, reg, val):
        self.reg.xor(reg, val)

    def OR(self, reg, val):
        self.reg._or(reg, val)

    def CP(self, reg, val):
        self.reg.cp(reg, val)

    def cycle(self, rom, silent=False):
        pc, delay = self.exe(rom, silent)
        self.reg.pc += pc

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
        Returns length in bytes, and cycles used.
        """
        byte = rom[self.reg.pc].upper()
        if not silent:
            print("Excecuting opcode '%s' at position '%s'" % (byte,hex(self.reg.pc)))
        if byte == "00": # NOP
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
        
        elif byte == "10": # STOP
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
        
        elif byte == "20": # JR NZ,r8
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
        
        elif byte == "30": # JR NC,r8
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

        elif byte == "40": # LD B,B
            self.LD("b",self.reg.b)
            return 1,4

        elif byte == "41": # LD B,C
            self.LD("b",self.reg.c)
            return 1,4

        elif byte == "42": # LD B,D
            self.LD("b",self.reg.d)
            return 1,4

        elif byte == "43": # LD B,E
            self.LD("b",self.reg.e)
            return 1,4

        elif byte == "44": # LD B,H
            self.LD("b",self.reg.h)
            return 1,4

        elif byte == "45": # LD B,L
            self.LD("b",self.reg.l)
            return 1,4

        elif byte == "46": # LD B,(HL)
            self.LD("b",self.mem[self.reg.hl])
            return 1,8

        elif byte == "47": # LD B,A
            self.LD("b",self.reg.a)
            return 1,4

        elif byte == "48": # LD C,B
            self.LD("c",self.reg.b)
            return 1,4

        elif byte == "49": # LD C,C
            self.LD("c",self.reg.c)
            return 1,4

        elif byte == "4A": # LD C,D
            self.LD("c",self.reg.d)
            return 1,4

        elif byte == "4B": # LD C,E
            self.LD("c",self.reg.e)
            return 1,4

        elif byte == "4C": # LD C,H
            self.LD("c",self.reg.h)
            return 1,4

        elif byte == "4D": # LD C,L
            self.LD("c",self.reg.l)
            return 1,4

        elif byte == "4E": # LD C,(HL)
            self.LD("c",self.mem[self.reg.hl])
            return 1,4

        elif byte == "4F": # LD C,A
            self.LD("c",self.reg.a)
            return 1,4
        
        elif byte == "50": # LD D,B
            self.LD("d",self.reg.b)
            return 1,4

        elif byte == "51": # LD D,C
            self.LD("d",self.reg.c)
            return 1,4

        elif byte == "52": # LD D,D
            self.LD("d",self.reg.d)
            return 1,4

        elif byte == "53": # LD D,E
            self.LD("d",self.reg.e)
            return 1,4

        elif byte == "54": # LD D,H
            self.LD("d",self.reg.h)
            return 1,4

        elif byte == "55": # LD D,L
            self.LD("d",self.reg.l)
            return 1,4

        elif byte == "56": # LD D,(HL)
            self.LD("d",self.mem[self.reg.hl])
            return 1,8

        elif byte == "57": # LD D,A
            self.LD("d",self.reg.a)
            return 1,4

        elif byte == "58": # LD E,B
            self.LD("e",self.reg.b)
            return 1,4

        elif byte == "59": # LD E,C
            self.LD("e",self.reg.c)
            return 1,4

        elif byte == "5A": # LD E,D
            self.LD("e",self.reg.d)
            return 1,4

        elif byte == "5B": # LD E,E
            self.LD("e",self.reg.e)
            return 1,4

        elif byte == "5C": # LD E,H
            self.LD("e",self.reg.h)
            return 1,4

        elif byte == "5D": # LD E,L
            self.LD("e",self.reg.l)
            return 1,4

        elif byte == "5E": # LD E,(HL)
            self.LD("e",self.mem[self.reg.hl])
            return 1,4

        elif byte == "5F": # LD E,A
            self.LD("e",self.reg.a)
            return 1,4
        
        elif byte == "60": # LD H,B
            self.LD("h",self.reg.b)
            return 1,4

        elif byte == "61": # LD H,C
            self.LD("h",self.reg.c)
            return 1,4

        elif byte == "62": # LD H,D
            self.LD("h",self.reg.d)
            return 1,4

        elif byte == "63": # LD H,E
            self.LD("h",self.reg.e)
            return 1,4

        elif byte == "64": # LD H,H
            self.LD("h",self.reg.h)
            return 1,4

        elif byte == "65": # LD H,L
            self.LD("h",self.reg.l)
            return 1,4

        elif byte == "66": # LD H,(HL)
            self.LD("h",self.mem[self.reg.hl])
            return 1,8

        elif byte == "67": # LD H,A
            self.LD("h",self.reg.a)
            return 1,4

        elif byte == "68": # LD L,B
            self.LD("l",self.reg.b)
            return 1,4

        elif byte == "69": # LD L,C
            self.LD("l",self.reg.c)
            return 1,4

        elif byte == "6A": # LD L,D
            self.LD("l",self.reg.d)
            return 1,4

        elif byte == "6B": # LD L,E
            self.LD("l",self.reg.e)
            return 1,4

        elif byte == "6C": # LD L,H
            self.LD("l",self.reg.h)
            return 1,4

        elif byte == "6D": # LD L,L
            self.LD("l",self.reg.l)
            return 1,4

        elif byte == "6E": # LD L,(HL)
            self.LD("l",self.mem[self.reg.hl])
            return 1,4

        elif byte == "6F": # LD L,A
            self.LD("l",self.reg.a)
            return 1,4
        
        elif byte == "70": # LD (HL),B
            self.mem[self.reg.hl] = self.reg.b
            return 1,8

        elif byte == "71": # LD (HL),C
            self.mem[self.reg.hl] = self.reg.c
            return 1,4

        elif byte == "72": # LD (HL),D
            self.mem[self.reg.hl] = self.reg.d
            return 1,4

        elif byte == "73": # LD (HL),E
            self.mem[self.reg.hl] = self.reg.e
            return 1,4

        elif byte == "74": # LD (HL),H
            self.mem[self.reg.hl] = self.reg.h
            return 1,4

        elif byte == "75": # LD (HL),L
            self.mem[self.reg.hl] = self.reg.l
            return 1,4

        elif byte == "76": # HALT
            # TODO HALT
            input("HALT")
            return 1,4

        elif byte == "77": # LD (HL),A
            self.mem[self.reg.hl] = self.reg.a
            return 1,4

        elif byte == "78": # LD A,B
            self.LD("a",self.reg.b)
            return 1,4

        elif byte == "79": # LD A,C
            self.LD("a",self.reg.c)
            return 1,4

        elif byte == "7A": # LD A,D
            self.LD("a",self.reg.d)
            return 1,4

        elif byte == "7B": # LD A,E
            self.LD("a",self.reg.e)
            return 1,4

        elif byte == "7C": # LD A,H
            self.LD("a",self.reg.h)
            return 1,4

        elif byte == "7D": # LD A,L
            self.LD("a",self.reg.l)
            return 1,4

        elif byte == "7E": # LD A,(HL)
            self.LD("a",self.mem[self.reg.hl])
            return 1,4

        elif byte == "7F": # LD A,A
            self.LD("a",self.reg.a)
            return 1,4
        
        elif byte == "80": # ADD A,B
            self.ADD("a",self.reg.b)
            return 1,4
        
        elif byte == "81": # ADD A,C
            self.ADD("a",self.reg.c)
            return 1,4
        
        elif byte == "82": # ADD A,D
            self.ADD("a",self.reg.d)
            return 1,4
        
        elif byte == "83": # ADD A,E
            self.ADD("a",self.reg.e)
            return 1,4
        
        elif byte == "84": # ADD A,H
            self.ADD("a",self.reg.h)
            return 1,4
        
        elif byte == "85": # ADD A,L
            self.ADD("a",self.reg.l)
            return 1,4
        
        elif byte == "86": # ADD A,(HL)
            self.ADD("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "87": # ADD A,A
            self.ADD("a",self.reg.b)
            return 1,4
        
        elif byte == "88": # ADC A,B
            self.ADC("a",self.reg.b)
            return 1,4
        
        elif byte == "89": # ADC A,C
            self.ADC("a",self.reg.c)
            return 1,4
        
        elif byte == "8A": # ADC A,D
            self.ADC("a",self.reg.d)
            return 1,4
        
        elif byte == "8B": # ADC A,E
            self.ADC("a",self.reg.e)
            return 1,4
        
        elif byte == "8C": # ADC A,H
            self.ADC("a",self.reg.h)
            return 1,4
        
        elif byte == "8D": # ADC A,L
            self.ADC("a",self.reg.l)
            return 1,4
        
        elif byte == "8E": # ADC A,(HL)
            self.ADC("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "8F": # ADC A,A
            self.ADC("a",self.reg.b)
            return 1,4
        
        elif byte == "90": # SUB B
            self.SUB("a",self.reg.b)
            return 1,4
        
        elif byte == "91": # SUB C
            self.SUB("a",self.reg.c)
            return 1,4
        
        elif byte == "92": # SUB D
            self.SUB("a",self.reg.d)
            return 1,4
        
        elif byte == "93": # SUB E
            self.SUB("a",self.reg.e)
            return 1,4
        
        elif byte == "94": # SUB H
            self.SUB("a",self.reg.h)
            return 1,4
        
        elif byte == "95": # SUB L
            self.SUB("a",self.reg.l)
            return 1,4
        
        elif byte == "96": # SUB (HL)
            self.SUB("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "97": # SUB A
            self.SUB("a",self.reg.a)
            return 1,4
        
        elif byte == "98": # SBC B
            self.SBC("a",self.reg.b)
            return 1,4
        
        elif byte == "99": # SBC C
            self.SBC("a",self.reg.c)
            return 1,4
        
        elif byte == "9A": # SBC D
            self.SBC("a",self.reg.d)
            return 1,4
        
        elif byte == "9B": # SBC E
            self.SBC("a",self.reg.e)
            return 1,4
        
        elif byte == "9C": # SBC H
            self.SBC("a",self.reg.h)
            return 1,4
        
        elif byte == "9D": # SBC L
            self.SBC("a",self.reg.l)
            return 1,4
        
        elif byte == "9E": # SBC (HL)
            self.SBC("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "9F": # SBC A
            self.SBC("a",self.reg.a)
            return 1,4
        
        elif byte == "A0": # AND B
            self.AND("a",self.reg.b)
            return 1,4
        
        elif byte == "A1": # AND C
            self.AND("a",self.reg.c)
            return 1,4
        
        elif byte == "A2": # AND D
            self.AND("a",self.reg.d)
            return 1,4
        
        elif byte == "A3": # AND E
            self.AND("a",self.reg.e)
            return 1,4
        
        elif byte == "A4": # AND H
            self.AND("a",self.reg.h)
            return 1,4
        
        elif byte == "A5": # AND L
            self.AND("a",self.reg.l)
            return 1,4
        
        elif byte == "A6": # AND (HL)
            self.AND("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "A7": # AND A
            self.AND("a",self.reg.a)
            return 1,4

        elif byte == "A8": # XOR B
            self.XOR("a",self.reg.b)
            return 1,4

        elif byte == "A9": # XOR C
            self.XOR("a",self.reg.c)
            return 1,4

        elif byte == "AA": # XOR D
            self.XOR("a",self.reg.d)
            return 1,4

        elif byte == "AB": # XOR E
            self.XOR("a",self.reg.e)
            return 1,4

        elif byte == "AC": # XOR H
            self.XOR("a",self.reg.h)
            return 1,4

        elif byte == "AD": # XOR L
            self.XOR("a",self.reg.l)
            return 1,4

        elif byte == "AE": # XOR (HL)
            self.XOR("a",self.mem[self.reg.hl])
            return 1,4

        elif byte == "AF": # XOR A
            self.XOR("a",self.reg.a)
            return 1,4
        
        elif byte == "B0": # OR B
            self.OR("a",self.reg.b)
            return 1,4
        
        elif byte == "B1": # OR C
            self.OR("a",self.reg.c)
            return 1,4
        
        elif byte == "B2": # OR D
            self.OR("a",self.reg.d)
            return 1,4
        
        elif byte == "B3": # OR E
            self.OR("a",self.reg.e)
            return 1,4
        
        elif byte == "B4": # OR H
            self.OR("a",self.reg.h)
            return 1,4
        
        elif byte == "B5": # OR L
            self.OR("a",self.reg.l)
            return 1,4
        
        elif byte == "B6": # OR (HL)
            self.OR("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "B7": # OR A
            self.OR("a",self.reg.a)
            return 1,4
        
        elif byte == "B8": # CP B
            self.CP("a",self.reg.b)
            return 1,4
        
        elif byte == "B9": # CP C
            self.CP("a",self.reg.c)
            return 1,4
        
        elif byte == "BA": # CP D
            self.CP("a",self.reg.d)
            return 1,4
        
        elif byte == "BB": # CP E
            self.CP("a",self.reg.e)
            return 1,4
        
        elif byte == "BC": # CP H
            self.CP("a",self.reg.h)
            return 1,4
        
        elif byte == "BD": # CP L
            self.CP("a",self.reg.l)
            return 1,4
        
        elif byte == "BE": # CP (HL)
            self.CP("a",self.mem[self.reg.hl])
            return 1,8
        
        elif byte == "BF": # CP A
            self.CP("a",self.reg.a)
            return 1,4

        elif byte == "C0":
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
            self.PREFIX_CB(rom[self.reg.pc+1])
            return 2,8

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

        elif byte == "D0":
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

        elif byte == "E0": # LDH (a8),A
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
            # TODO
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

        elif byte == "F0": # LDH A,(a8)
            self.LD("a", self.mem[int(rom[self.reg.pc+1],16)])
            return 2,12

        elif byte == "F1": # POP AF
            self.reg.f = self.mem[self.reg.sp]
            self.reg.sp += 1
            self.reg.a = self.mem[self.reg.sp]
            self.reg.sp += 1
            return 1,12

        elif byte == "F2": # LD A,(C)
            # TODO: Read from memory
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
            # TODO
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
