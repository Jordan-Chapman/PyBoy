# Author: Jordan Chapman
# Aiming to be a bit faster
#   Reading ROM as binary instead of hex

# Not much faster...

# Register table; binary code for each register
REG_TABLE = {"000":"b",
             "001":"c",
             "010":"d",
             "011":"e",
             "100":"h",
             "101":"l",
             "110":"hl",
             "111":"a"}

def loadRom(filepath):
    """ Load a ROM array from string:'file' path """
    rom = []
    with open(filepath, "rb") as file:
        byte = file.read(1)
        while byte:
            bins = bin(int(byte.hex(),16))[2:]
            bins = "0"*(8-len(bins)) + bins
            rom.append(bins)
            byte = file.read(1)
    return rom


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
        """
        Set the value of the register
        corresponding to the string 'reg'
        """
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

    def inc(self, reg, setFlags):
        self.set_register(reg, self.get_register(reg)+1)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 0 # Subtraction flag

    def dec(self, reg, setFlags):
        self.set_register(reg, self.get_register(reg)-1)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 1 # Subtraction flag

    def add(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)+val)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 0 # Subtraction flag

    def sub(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)-val)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 1 # Subtraction flag

    def _and(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)&val)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 0 # Subtraction flag
            self.flags[2] = 1 # Half-Carry flag
            self.flags[3] = 0 # Carry flag

    def _or(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)|val)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 0 # Subtraction flag
            self.flags[2] = 0 # Half-Carry flag
            self.flags[3] = 0 # Carry flag

    def xor(self, reg, val, setFlags):
        self.set_register(reg, self.get_register(reg)^val)
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 0 # Subtraction flag
            self.flags[2] = 0 # Half-Carry flag
            self.flags[3] = 0 # Carry flag

    def cp(self, reg, val, setFlags):
        if setFlags:
            if self.get_register(reg) == 0:
                self.flags[0] = 1 # Zero flag
            self.flags[1] = 1 # Subtraction flag

    def test(self, val, bit):
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
        type_bits = bts[0:2]
        
        level_bits = bts[2:5]
        bit = int(level_bits, 2)
        
        reg_bits = bts[5:8]
        register = REG_TABLE[reg_bits]

        if register == "hl":
            time = 16 # Memory access takes longer than register access
            val = self.mem[self.reg.hl]
        else:
            val = self.reg.get_register(register)

        bits = bin(val)[2:]
        bits = "0"*(8-len(bits)) + bits

        # Variable "type_bits" = first 2 bits; determine what type of operation to perform
        # Variable "bits" = binary value of the chosen register (or RAM at location (HL))
        # Variable "bit" = integer value of the "level" bits; different use depending on type_bits

        # CB Table

        if type_bits == "00": # Rotations
            if bit == 0: # RLC
                pass
            
            elif bit == 1: # RRC
                pass
            
            elif bit == 2: # RL
                pass

            elif bit == 3: # RR
                pass

            elif bit == 4: # SLA
                pass

            elif bit == 5: # SRA
                pass

            elif bit == 6: # SWAP
                pass

            elif bit == 7: # SRL
                pass

            if register == "hl":
                self.mem[self.reg.hl] = int(bits,2)
            else:
                self.reg.set_register(register, int(bits,2))

        if type_bits == "01": # Test bits
            self.reg.test(bits,bit) # Testing the "bit"th bit in bits

        if type_bits == "10": # Resets
            bits = bits[:bit] + "0" + bits[bit:] # Reseting the "bit"th bit in bits
            if register == "hl":
                self.mem[self.reg.hl] = int(bits,2)
            else:
                self.reg.set_register(register, int(bits,2))

        if type_bits == "11": # Sets
            bits = bits[:bit] + "1" + bits[bit:] # Setting the "bit"th bit in bits
            if register == "hl":
                self.mem[self.reg.hl] = int(bits,2)
            else:
                self.reg.set_register(register, int(bits,2))

        return time

    def exe(self, rom, silent=False):
        """
        Excecute code at position "pos" in the rom
        Parameter "silent" - Prints info if False
        Returns length in bytes, and cycles used.
        """
        byte = rom[self.reg.pc] # Reading byte from ROM
        sec = byte[0:2] # Table section
        row = byte[2:4] # Section row
        side = byte[4:6] # Vertical specifier (4 splits)
        col = byte[6:8] # Column specifier
        
        if not silent:
            print("Excecuting opcode '0b%s' at position '%s'" % (byte,hex(self.reg.pc)))

        if sec == "01": # LD operations + HALT
            # Read as binary string
            # Example (01001010)
            #   First 2 bits (01) = LD operations
            #   Next 3 bits (001) = C register
            #   Last 3 bits (010) = D register
            # 01001010 = Load into C from D

            reg_dest = REG_TABLE[byte[2:5]]
            reg_source = REG_TABLE[byte[5:8]]
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

        elif sec == "10": # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
            operation = byte[2:5]
            reg_source = REG_TABLE[byte[5:8]]

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

        elif sec == "00":
            if row == "00":
                if side == "00":
                    if col == "00": # NOP
                        return 1,4

                    elif col == "01": # LD BC,d16
                        bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                        self.LD("bc",int(bts, 2))
                        return 3,12

                    elif col == "02": # LD (BC),A
                        self.mem[self.reg.bc] = self.reg.a
                        return 1,8

                    elif col == "03": # INC BC
                        self.INC("bc")
                        return 1,8

                elif side == "01":
                    if col == "00": # INC B
                        self.INC("b")
                        return 1,4

                    elif col == "01": # DEC B
                        self.DEC("b")
                        return 1,4

                    elif col == "10": # LD B,d8
                        self.LD("b",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11": # RLCA
                        # TODO: Rotate 'a' left, copy bit 7 to carry and a[0]
                        a = bin(self.reg.a)[2:]
                        self.reg.flags[3] = a[0] == "1"
                        a = a[1:] + a[0]
                        return 1,4

                elif side == "10":
                    if col == "00": # LD (a16),SP
                        self.mem[int(rom[self.reg.pc+1],2)] = self.reg.sp
                        return 3,20

                    elif col == "01": # ADD HL,BC
                        self.ADD("hl",self.reg.bc, setFlags = False)
                        return 1,8

                    elif col == "10": # LD A,(BC)
                        self.mem[self.reg.a] = self.reg.bc
                        return 1,8

                    elif col == "11": # DEC BC
                        self.DEC("bc")
                        return 1,8

                elif side == "11":
                    if col == "00": # INC C
                        self.INC("c")
                        return 1,4

                    elif col == "01": # DEC C
                        self.DEC("c")
                        return 1,4

                    elif col == "10": # LD C,d8
                        self.LD("c",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11": # RRCA
                        # TODO: Rotate 'a' right, copy bit 0 to carry and a[7]
                        return 1,4
            elif row == "01":
                if side == "00":
                    if col == "00": # STOP
                        print("STOPPING")
                        return 2,4
                    
                    elif col == "01": # LD DE,d16
                        bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                        self.LD("de",int(bts, 2))
                        return 3,12

                    elif col == "10": # LD (DE),A
                        self.mem[self.reg.de] = self.reg.a
                        return 1,8

                    elif col == "11": # INC DE
                        self.INC("de")
                        return 1,8

                elif side == "01":
                    if col == "00": # INC D
                        self.INC("d")
                        return 1,4

                    elif col == "01": # DEC D
                        self.DEC("d")
                        return 1,4

                    elif col == "10": # LD D,d8
                        self.LD("d",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11": # RLA
                        # TODO: Rotate 'a' left, copy bit 7 to carry, copy carry to a[0]
                        return 1,4

                elif side == "10":
                    if col == "00": # JR r8
                        jump = int(rom[self.reg.pc+1], 2)
                        if jump > 127: jump -= 255
                        jump = 0 # TODO
                        return 2+jump,12

                    elif col == "01": # ADD HL,DE
                        self.ADD("hl",self.reg.de, setFlags = False)
                        return 1,8

                    elif col == "10": # LD A,(DE)
                        self.mem[self.reg.a] = self.reg.de
                        return 1,8

                    elif col == "11": # DEC DE
                        self.DEC("DE")
                        return 1,8

                elif side == "11":
                    if col == "00": # INC E
                        self.INC("e")
                        return 1,4

                    elif col == "01": # DEC E
                        self.DEC("e")
                        return 1,4

                    elif col == "10": # LD E,d8
                        self.LD("e",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11": # RRA
                        # TODO: Rotate 'a' right, copy bit 0 to carry, copy carry to a[7]
                        return 1,4

            elif row == "10":
                if side == "00":
                    if col == "00": # JR NZ,r8
                        if not self.reg.flags[0]:
                            jump = int(rom[self.reg.pc+1], 2)
                            if jump > 127: jump -= 255
                            jump = 0 # TODO
                            return 2+jump, 12
                        else:
                            return 2, 8

                    elif col == "01": # LD HL,d16
                        bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                        self.LD("hl",int(bts,2))
                        return 3,12

                    elif col == "10": # LD (HL+),A
                        self.mem[self.reg.hl] = self.reg.a
                        self.reg.hl += 1
                        return 1,8

                    elif col == "11": # INC HL
                        self.INC("hl")
                        return 1,8

                elif side == "01":
                    if col == "00": # INC H
                        self.INC("h")
                        return 1,4

                    elif col == "01": # DEC H
                        self.DEC("h")
                        return 1,4

                    elif col == "10": # LD H,d8
                        self.LD("h",int(rom[self.reg.pc+1],2))
                        return 2,8
                    
                    elif col == "11": # DAA
                        # TODO
                        return 1,4
                
                elif side == "10":
                    if col == "00": # JR Z,r8
                        if self.reg.flags[3]:
                            jump = int(rom[self.reg.pc+1], 2)
                            if jump > 127: jump -= 255
                            jump = 0 # TODO
                            return 2+jump, 12
                        else:
                            return 2, 8

                    elif col == "01": # ADD HL,HL
                        self.ADD("hl",self.reg.hl, setFlags=False)
                        return 1,8

                    elif col == "10": # LD A,(HL+)
                        self.mem[self.reg.a] = self.reg.hl
                        self.reg.hl += 1
                        return 1,8

                    elif col == "11": # DEC HL
                        self.DEC("hl")
                        return 1,8

                elif side == "11":
                    if col == "00": # INC L
                        self.INC("l")
                        return 1,4

                    elif col == "01": # DEC L
                        self.DEC("l")
                        return 1,4

                    elif col == "10": # LD L,d8
                        self.LD("l",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11": # CPL
                        # TODO
                        return 1,4

            elif row == "11":
                if side == "00":
                    if col == "00": # JR NC,r8
                        if not self.reg.flags[3]:
                            jump = int(rom[self.reg.pc+1], 2)
                            if jump > 127: jump -= 255
                            jump = 0 # TODO
                            return 2+jump, 12
                        else:
                            return 2, 8
                    
                    elif col == "01": # LD SP,d16
                        bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                        self.LD("sp",int(bts, 2))
                        return 3,12

                    elif col == "10": # LD (HL-),A
                        self.mem[self.reg.hl] = self.reg.a
                        self.reg.hl -= 1
                        return 1,8

                    elif col == "11": # INC SP
                        self.INC("sp")
                        return 1,8
                
                elif side == "01":
                    if col == "00": # INC (HL)
                        self.INC("hl")
                        return 1,4

                    elif col == "01": # DEC (HL)
                        self.DEC("hl")
                        return 1,4

                    elif col == "10": # LD (HL),d8
                        self.mem[self.reg.hl] = int(rom[self.reg.pc+1],2)
                        return 2,12

                    elif col == "11":
                        self.reg.flags[3] = 1
                        return 1,4

                elif side == "10":
                    if col == "00": # JR C,r8
                        if self.reg.flags[3]:
                            jump = int(rom[self.reg.pc+1], 2)
                            if jump > 127: jump -= 255
                            jump = 0 # TODO
                            return 2+jump, 12
                        else:
                            return 2, 8

                    elif col == "01": # ADD HL,SP
                        self.ADD("hl",self.reg.sp, setFlags=False)
                        return 1,8

                    elif col == "10": # LD A,(HL-)
                        self.mem[self.reg.a] = self.reg.hl
                        self.reg.hl -= 1
                        return 1,8

                    elif col == "11": # DEC SP
                        self.DEC("sp")
                        return 1,8

                elif side == "11":
                    if col == "00": # INC A
                        self.INC("a")
                        return 1,4

                    elif col == "01": # DEC A
                        self.DEC("a")
                        return 1,4

                    elif col == "10": # LD A,d8
                        self.LD("a",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11": # CCF
                        self.reg.flags[3] = not self.reg.flags[3]
                        return 1,4

        elif sec == "11":
            if row == "00":
                if side == "00":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01": # POP BC
                        self.reg.c = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        self.reg.b = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        return 1,12

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "01":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01": # PUSH BC
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.b
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.c
                        return 1,16

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "10":
                    if col == "00": # RET Z
                        # TODO: Stack stuff
                        if self.reg.flags[0]:
                            return 1,20
                        return 1,8

                    elif col == "01": # RET
                        self.reg.pc = self.mem[self.reg.sp]
                        return 1,16

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11": # PREFIX CB
                        t = self.PREFIX_CB(rom[self.reg.pc+1])
                        return 2,t

                elif side == "11":
                    if col == "00": # CALL Z,a16
                        # TODO CALLS
                        if self.reg.flags[0]:
                            return 3,24
                        return 3,12

                    elif col == "01": # CALL a16
                        # TODO CALLS
                        return 3,24

                    elif col == "10": # ADC A,d8
                        self.ADC("a",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11":
                        # TODO
                        pass

            elif row == "01":
                if side == "00":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01": # POP DE
                        self.reg.e = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        self.reg.d = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        return 1,12

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "01":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01": # PUSH DE
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.d
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.e
                        return 1,16

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "10":
                    if col == "00": # RET C
                        # TODO: Stack stuff
                        if self.reg.flags[3]:
                            return 1,20
                        return 1,8

                    elif col == "01": # RETI
                        # TODO: Stack stuff
                        return 1,16

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "11":
                    if col == "00": # CALL C,a16
                        # TODO CALLS
                        if self.reg.flags[3]:
                            return 3,24
                        return 3,12

                    elif col == "01":
                        # TODO
                        pass

                    elif col == "10": # SBC A,d8
                        self.SBC("a",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11":
                        # TODO
                        pass

            elif row == "10":
                if side == "00":
                    if col == "00": # LDH (a8),A
                        self.mem[self.reg.a] = int(rom[self.reg.pc+1],2)
                        return 2,12

                    elif col == "01": # POP HL
                        self.reg.l = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        self.reg.h = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        return 1,12

                    elif col == "10": # LD (C),A
                        self.mem[self.reg.c] = self.reg.a
                        return 2,8

                    elif col == "11":
                        # TODO
                        pass

                elif side == "01":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01": # PUSH HL
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.h
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.l
                        return 1,16

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "10":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01":
                        # TODO
                        pass

                    elif col == "10": # LD (a16),A
                        # TODO: Address bytes right order in RAM?
                        return 3,16

                    elif col == "11":
                        # TODO
                        pass

                elif side == "11":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01":
                        # TODO
                        pass

                    elif col == "10": # XOR d8
                        self.XOR("a",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11":
                        # TODO
                        pass

            elif row == "11":
                if side == "00":
                    if col == "00": # LDH A,(a8)
                        # TODO: Am I right on this? What's the H for?
                        self.LD("a", self.mem[int(rom[self.reg.pc+1],2)])
                        return 2,12

                    elif col == "01": # POP AF
                        self.reg.f = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        self.reg.a = self.mem[self.reg.sp]
                        self.reg.sp += 1
                        return 1,12

                    elif col == "10": # LD A,(C)
                        self.LD("a", self.mem[self.reg.c])
                        return 2,8

                    elif col == "11": # DI
                        # TODO: Reset flipflops?
                        return 1,4

                elif side == "01":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01": # PUSH AF
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.a
                        self.reg.sp -= 1
                        self.mem[self.reg.sp] = self.reg.f
                        return 1,16

                    elif col == "10":
                        # TODO
                        pass

                    elif col == "11":
                        # TODO
                        pass

                elif side == "10":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01":
                        # TODO
                        pass

                    elif col == "10": # LD A, (a16)
                        # TODO: Address bytes right order in RAM?
                        return 3,16

                    elif col == "11":
                        # TODO
                        pass

                elif side == "11":
                    if col == "00":
                        # TODO
                        pass

                    elif col == "01":
                        # TODO
                        pass

                    elif col == "10": # CP d8
                        self.CP("a",int(rom[self.reg.pc+1],2))
                        return 2,8

                    elif col == "11":
                        # TODO
                        pass
                
        else:
            input("UNIMPLEMENTED OPCODE: " + byte)
            return 1,0
