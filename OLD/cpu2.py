# Author: Jordan Chapman
# Aiming to be a bit faster than old cpu
#   Opcodes search tree-style
#   LD section (4X-7X) now logical like CB table
#   Operations section (8X-BX) now also logical

# Testing shows more than double speed over original

# FLAG RULES
# Flag setting is passed as an array
#   [Z,N,H,C]
# 0 means reset that flag
# 1 means set that flag
# 2 means normal operation
# 3 means no change

# Example: [1,0,2,3]:
#   Set zero flag
#   Reset subtraction flag
#   Normal operation on half-carry flag
#   No change to carry flag


### CPU INFO ### (Stuff I learned, may be inaccurate)

# Gameboy CPU is based on the Z80, with elements from the intel 8080
#
# Specs:
#   4.19 Mhz (Optional 8Mhz mode for GBC?)
#   8 8bit registers, 2 16bit registers
#   245 operations, with 256 bitwise operations on the CB table
#
# Registers:
#   B, C, D, E, H, L, A, F - 8bit registers
#   SP, PC - 16bit registers
#   BC, DE, HL, AF - 8bit registers used together as 16bit
#
#   Notes:
#       F register is the flag register.
#         Lower 4 bits always 0
#         Upper 4 bits are flags:
#           bit 7 = Zero flag - set when operation results in 0
#           bit 6 = Subtraction flag - set when operation subtracts?
#           bit 5 = Half-carry flag - set when lower 4 bits carry to upper 4
#           bit 4 = Carry flag - set when register overflows
#
#       A register is the main register
#         Many opcodes involve operation on A from the other registers
#         All "Math and Logic" opcodes from 8X-BX
#         All bitwise operations on the PREFIX CB table
#
#       SP register is the Stack Pointer
#         Used as a 16bit memory address
#
#       PC register is the Program Counter
#         Tracks current location in the ROM
#
# Operations:
#   Opcodes D3,DB,DD,E3,E4,EB,EC,ED,F4,FC,FD do not exist
#   Opcode CB redirects to another table (PREFIX CB)
#       Contains bitwise operations on the A register


# Register table; binary code for each register
REG_TABLE = {"000":"b",
             "001":"c",
             "010":"d",
             "011":"e",
             "100":"h",
             "101":"l",
             "110":"(hl)",
             "111":"a"}

def loadRom(filepath):
    """ Load a ROM array from string:'file' path """
    rom = []
    with open(filepath, "rb") as file:
        byte = file.read(1)
        while byte:
            rom.append(byte.hex().upper())
            byte = file.read(1)
    return rom


class OpcodeException(Exception):
    """ Raised when an illegal opcode is requested """
    pass

class Memory:
    """
    Little memory object. Indexible.
    Creates addresses when needed
    """
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

    def __str__(self):
        return str(self.memory)

    def __repr__(self):
        return str(self.memory)

class Registers:
    """ Registers object, keeps track of CPU registers """
    # Registers only deal in integers.
    #  convert all hex to int before passing to registers
    def __init__(self, mem, silent):
        self._a = 0
        self._b = 0
        self._c = 0
        self._d = 0
        self._e = 0
        self._h = 0
        self._l = 0
        self.sp = 0
        self.pc = 0
        self.flags = [0,0,0,0] # Zero, Sub, Half-Carry, Carry
        self.mem = mem

        self.silent = silent


    ### Properties ###

    def get_a(self): return self._a
    def set_a(self, val): self._a = val%256
    a = property(get_a, set_a)
    def get_b(self): return self._b
    def set_b(self, val): self._b = val%256
    b = property(get_b, set_b)
    def get_c(self): return self._c
    def set_c(self, val): self._c = val%256
    c = property(get_c, set_c)
    def get_d(self): return self._d
    def set_d(self, val): self._d = val%256
    d = property(get_d, set_d)
    def get_e(self): return self._e
    def set_e(self, val): self._e = val%256
    e = property(get_e, set_e)
    def get_h(self): return self._h
    def set_h(self, val): self._h = val%256
    h = property(get_h, set_h)
    def get_l(self): return self._l
    def set_l(self, val): self._l = val%256
    l = property(get_l, set_l)

    def get_f(self):
        f=self.flags[0]*128+self.flags[1]*64+self.flags[2]*32+self.flags[3]*16
        return f
    def set_f(self, f):
        f = f%256
        f = bin(f)[2:]
        f = "0"*(8-len(f)) + f
        self.flags[0] = 1 if f[0] == "1" else 0
        self.flags[1] = 1 if f[1] == "1" else 0
        self.flags[2] = 1 if f[2] == "1" else 0
        self.flags[3] = 1 if f[3] == "1" else 0
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

    ### Register methods ###

    def get_register(self, reg):
        """
        Gets a string:'reg' and returns
        the value of the corresponding register
        """
        if reg == "b": return self.b
        elif reg == "c": return self.c
        elif reg == "d": return self.d
        elif reg == "e": return self.e
        elif reg == "h": return self.h
        elif reg == "l": return self.l
        elif reg == "(hl)": return self.mem[self.hl]
        elif reg == "a": return self.a
        elif reg == "f": return self.f
        elif reg == "sp": return self.sp
        elif reg == "af": return self.af
        elif reg == "bc": return self.bc
        elif reg == "de": return self.de
        elif reg == "hl": return self.hl
        elif reg == "(bc)": return self.mem[self.bc]
        elif reg == "(de)": return self.mem[self.de]
        elif reg == "(af)": return self.mem[self.af]

    def set_register(self, reg, val):
        """
        Set the value of the register
        corresponding to the string 'reg'
        """
        if not self.silent: print("Set register %s to %s" % (reg,val))
        if reg == "b": self.b = val
        elif reg == "c": self.c = val
        elif reg == "d": self.d = val
        elif reg == "e": self.e = val
        elif reg == "h": self.h = val
        elif reg == "l": self.l = val
        elif reg == "(hl)": self.mem[self.hl] = val
        elif reg == "a": self.a = val
        elif reg == "f": self.f = val
        elif reg == "sp": self.sp = val
        elif reg == "af": self.af = val
        elif reg == "bc": self.bc = val
        elif reg == "de": self.de = val
        elif reg == "hl": self.hl = val
        elif reg == "(bc)": self.mem[self.bc] = val
        elif reg == "(de)": self.mem[self.de] = val
        elif reg == "(af)": self.mem[self.af] = val
        return val

    def set_flags(self, template, prev, result):
        """
        Set the flag register based on the given parameters
        template = flag template array (see top of the file "FLAG RULES"
        prev = value of register before operation
        result = value of register after operation
        Should only use with 8bit operations
        """
        # Zero flag
        if template[0] == 0:
            self.flags[0] = 0
        elif template[0] == 1:
            self.flags[0] = 1
        elif template[0] == 2:
            self.flags[0] = 1 if result == 0 else 0

        # Subtraction flag
        if template[1] == 0:
            self.flags[1] = 0
        elif template[1] == 1:
            self.flags[1] = 1
        elif template[1] == 2: # Never used in this method
            pass

        # Half-carry flag
        if template[2] == 0:
            self.flags[2] = 0
        elif template[2] == 1:
            self.flags[2] = 1
        elif template[2] == 2:
            input("HALF CARRY AT %s. VALUE %s TO %s" % (self.pc, prev, result))
            pass # GRR

        # Carry flag
        if template[3] == 0:
            self.flags[3] = 0
        elif template[3] == 1:
            self.flags[3] = 1
        elif template[3] == 2:
            input("CARRY AT %s. VALUE %s TO %s" % (self.pc, prev, result))
            pass # TODO FLAGS

        if not self.silent: print("Set flags to %s" % self.flags)

    ### Operations ###

    def load(self, reg, val):
        """ Load value "val" into register "reg" """
        self.set_register(reg, val)

    def inc(self, reg, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev+1)
        self.set_flags(flags, prev, result)

    def dec(self, reg, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev-1)
        self.set_flags(flags, prev, result)

    def add(self, reg, val, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev+val)
        self.set_flags(flags, prev, result)

    def sub(self, reg, val, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev-val)
        self.set_flags(flags, prev, result)

    def _and(self, reg, val, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev&val)
        self.set_flags(flags, prev, result)

    def _or(self, reg, val, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev|val)
        self.set_flags(flags, prev, result)

    def xor(self, reg, val, flags):
        prev = self.get_register(reg)
        result = self.set_register(reg, prev^val)
        self.set_flags(flags, prev, result)

    def cp(self, reg, val, flags):
        prev = self.get_register(reg)
        result = (prev-val) % 256
        self.set_flags(flags, prev, result)

    def test(self, val, bit):
        self.flags[0] = 1 if val[7-bit] == "0" else 0
        self.flags[1] = 0
        self.flags[2] = 1
    

class CPU:
    """
    CPU object.
    Keeps track of RAM ('memory' object)
    Keeps its own 'registers' object

    TO USE:
    Initialize once, call 'cycle()' method
     and pass a ROM ( [list] of hex values in pairs)
    """
    def __init__(self, silent=False):
        self.mem = Memory()
        self.reg = Registers(self.mem, silent)
        self.silent = silent

    def cycle(self, rom):
        """
        Main method of excecution
            Excecutes operation at [PC register] index in ROM
        'rom' parameter - [list] of hex values in pairs
        Returns: Duration in cycles the current operation used
        """
        pc, delay = self.exe(rom)
        self.reg.pc += pc
        return delay

    ### Operations ###

    def LD(self, reg, bts):
        self.reg.load(reg, bts)

    def INC(self, reg, flags=[2,0,2,3]):
        self.reg.inc(reg, flags)

    def DEC(self, reg, flags=[2,1,2,3]):
        self.reg.dec(reg, flags)

    def INC(self, reg, flags=[2,0,2,3]):
        prev = self.reg.get_register(reg)
        result = self.reg.set_register(reg, prev+1)
        self.reg.set_flags(flags, prev, result)

    def DEC(self, reg, flags=[2,1,2,3]):
        prev = self.reg.get_register(reg)
        result = self.reg.set_register(reg, prev-1)
        self.reg.set_flags(flags, prev, result)

    def ADD(self, reg, val, flags=[2,0,2,2]):
        self.reg.add(reg, val, flags)

    def ADC(self, reg, val, flags=[2,0,2,2]):
        self.reg.add(reg, val+self.reg.flags[3], flags)

    def SUB(self, reg, val, flags=[2,1,2,2]):
        self.reg.sub(reg, val, flags)

    def SBC(self, reg, val, flags=[2,1,2,2]):
        self.reg.sub(reg, val+self.reg.flags[3], flags)

    def AND(self, reg, val, flags=[2,0,1,0]):
        self.reg._and(reg, val, flags)

    def XOR(self, reg, val, flags=[2,0,0,0]):
        self.reg.xor(reg, val, flags)

    def OR(self, reg, val, flags=[2,0,0,0]):
        self.reg._or(reg, val, flags)

    def CP(self, reg, val, flags=[2,1,2,2]):
        self.reg.cp(reg, val, flags)

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

        if register == "(hl)":
            time = 16 # Memory access takes longer than register access
        val = self.reg.get_register(register)

        bits = bin(val)[2:]
        bits = "0"*(8-len(bits)) + bits

        # Variable "type_bits" = first 2 bits; determine what type of operation to perform
        # Variable "bits" = binary value of the chosen register (or RAM at location (HL))
        # Variable "bit" = integer value of the "level" bits; different use depending on type_bits

        # CB Table

        if type_bits == "00": # Rotations
            if not self.silent: print("CB rotation operation %s on register: %s" % (bit, register))
            if bit == 0: # RLC
                # Rotate left, copy bit 7 to carry and bit 0
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[0] == "1" else 0
                # TODO: Set zero flag
                bits = bits[1:] + bits[0]

            elif bit == 1: # RRC
                # Rotate right, copy bit 0 to carry and bit 7
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[7] == "1" else 0
                # TODO: Set zero flag
                bits = bits[7] + bits[:7]
            
            elif bit == 2: # RL
                # Rotate left, copy bit 7 to carry, copy carry to bit 0
                carry = self.reg.flags[3]
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[0] == "1" else 0
                # TODO: Set zero flag
                bits = bits[1:] + ("1" if carry else "0")

            elif bit == 3: # RR
                # Rotate right, copy bit 0 to carry, copy carry to bit 7
                carry = self.reg.flags[3]
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[7] == "1" else 0
                # TODO: Set zero flag
                bits = ("1" if carry else "0") + bits[:7] 

            elif bit == 4: # SLA
                # Rotate left, copy bit 7 to carry and reset bit 0
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[0] == "1" else 0
                # TODO: Set zero flag
                bits = bits[1:] + "0"

            elif bit == 5: # SRA
                # Rotate right, copy bit 0 to carry, keep bit 7
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[7] == "1" else 0
                # TODO: Set zero flag
                bits = "0" + bits[:7]

            elif bit == 6: # SWAP
                # TODO
                pass

            elif bit == 7: # SRL
                # Rotate right, copy bit 0 to carry, reset bit 7
                carry = self.reg.flags[3]
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if bits[7] == "1" else 0
                # TODO: Set zero flag
                bits = "0" + bits[:7] 

            self.reg.set_register(register, int(bits,2))

        elif type_bits == "01": # Test bits
            if not self.silent: print("CB testing bit %s of register: %s" % (bit, register))
            self.reg.test(bits,bit) # Testing the "bit"th bit in bits

        elif type_bits == "10": # Resets
            if not self.silent: print("CB resetting bit %s of register: %s" % (bit, register))
            bits = bits[:bit] + "0" + bits[bit:] # Reseting the "bit"th bit in bits
            result = int(bits, 2)
            self.reg.set_register(register, result)

        elif type_bits == "11": # Sets
            if not self.silent: print("CB setting bit %s of register: %s" % (bit, register))
            bits = bits[:bit] + "1" + bits[bit:] # Setting the "bit"th bit in bits
            result = int(bits, 2)
            self.reg.set_register(register, result)

        return time

    ### Opcodes ###

    def exe(self, rom):
        """
        Opcode excecution table
            Excecutes operation at [PC register] index in ROM
        'rom' parameter - [list] of hex values in pairs
        Returns:
            Number of bytes used by the current operation
            Duration in cycles the current operation used
        """
        byte = rom[self.reg.pc] # Reading byte from ROM
        ref = byte[0] # Row on opcode table
        op = byte[1] # Column on opcode table
        
        if not self.silent: print("Excecuting opcode '%s' at position '%s'" % (byte,hex(self.reg.pc)))

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
            if reg_dest == reg_source == "(hl)":
                # TODO HALT
                return 1,4
            self.LD(reg_dest, self.reg.get_register(reg_source))
            if reg_dest == "(hl)" or reg_source == "(hl)":
                return 1,8
            return 1,4

        elif ref in ["8","9","A","B"]: # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
            bits = bin(int(byte,16))[2:]
            bits = "0"*(8-len(bits)) + bits
            operation = bits[2:5]
            reg_source = REG_TABLE[bits[5:8]]

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
            
            if reg_source == "(hl)":
                return 1,8
            return 1,4

        elif ref == "0":
            if op == "0": # NOP
                return 1,4

            elif op == "1": # LD BC,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("bc",int(bts, 16))
                return 3,12

            elif op == "2": # LD (BC),A
                self.mem[self.reg.bc] = self.reg.a
                return 1,8

            elif op == "3": # INC BC
                self.INC("bc", flags=[3,3,3,3])
                return 1,8

            elif op == "4": # INC B
                self.INC("b")
                return 1,4

            elif op == "5": # DEC B
                self.DEC("b")
                return 1,4

            elif op == "6": # LD B,d8
                self.LD("b",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "7": # RLCA
                # TODO: Rotate 'a' left, copy bit 7 to carry and a[0]
                a = bin(self.reg.a)[2:]
                a = "0"*(8-len(a)) + a
                self.reg.flags = [0,0,0,0]
                self.reg.flags[3] = 1 if a[0] == "1" else 0
                a = a[1:] + a[0]
                return 1,4

            elif op == "8": # LD (a16),SP
                self.mem[int(rom[self.reg.pc+1],16)] = self.reg.sp
                return 3,20

            elif op == "9": # ADD HL,BC
                self.ADD("hl",self.reg.bc, flags=[3,0,2,2])
                return 1,8

            elif op == "A": # LD A,(BC)
                self.mem[self.reg.a] = self.reg.bc
                return 1,8

            elif op == "B": # DEC BC
                self.DEC("bc", flags=[3,3,3,3])
                return 1,8

            elif op == "C": # INC C
                self.INC("c")
                return 1,4

            elif op == "D": # DEC C
                self.DEC("c")
                return 1,4

            elif op == "E": # LD C,d8
                self.LD("c",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # RRCA
                # TODO: Rotate 'a' right, copy bit 0 to carry and a[7]
                a = bin(self.reg.a)[2:]
                a = "0"*(8-len(a)) + a
                self.reg.flags = [0,0,0,0]
                self.reg.flags[3] = 1 if a[7] == "1" else 0
                a = a[7] + a[:7]
                return 1,4

        elif ref == "1":
            if op == "0": # STOP
                print("STOPPING")
                return 2,4
            
            elif op == "1": # LD DE,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("de",int(bts, 16))
                return 3,12

            elif op == "2": # LD (DE),A
                self.mem[self.reg.de] = self.reg.a
                return 1,8

            elif op == "3": # INC DE
                self.INC("de", flags=[3,3,3,3])
                return 1,8

            elif op == "4": # INC D
                self.INC("d")
                return 1,4

            elif op == "5": # DEC D
                self.DEC("d")
                return 1,4

            elif op == "6": # LD D,d8
                self.LD("d",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "7": # RLA
                # TODO: Rotate 'a' left, copy bit 7 to carry, copy carry to a[0]
                a = bin(self.reg.a)[2:]
                a = "0"*(8-len(a)) + a
                carry = self.reg.flags[3]
                self.reg.flags = [0,0,0,0]
                self.reg.flags[3] = 1 if a[0] == "1" else 0
                a = a[1:] + ("1" if carry else "0")
                return 1,4

            elif op == "8": # JR r8
                jump = int(rom[self.reg.pc+1], 16)
                if jump > 127: jump -= 255
                return 1+jump,12

            elif op == "9": # ADD HL,DE
                self.ADD("hl",self.reg.de, flags=[3,0,2,2])
                return 1,8

            elif op == "A": # LD A,(DE)
                self.mem[self.reg.a] = self.reg.de
                return 1,8

            elif op == "B": # DEC DE
                self.DEC("DE", flags=[3,3,3,3])
                return 1,8

            elif op == "C": # INC E
                self.INC("e")
                return 1,4

            elif op == "D": # DEC E
                self.DEC("e")
                return 1,4

            elif op == "E": # LD E,d8
                self.LD("e",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # RRA
                # TODO: Rotate 'a' right, copy bit 0 to carry, copy carry to a[7]
                a = bin(self.reg.a)[2:]
                a = "0"*(8-len(a)) + a
                carry = self.reg.flags[3]
                self.reg.flags = [0,0,0,0]
                self.reg.flags[3] = 1 if a[7] == "1" else 0
                a = ("1" if carry else "0") + a[0:7]
                return 1,4

        elif ref == "2":
            if op == "0": # JR NZ,r8
                if not self.reg.flags[0]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8

            elif op == "1": # LD HL,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("hl",int(bts,16))
                return 3,12

            elif op == "2": # LD (HL+),A
                self.mem[self.reg.hl] = self.reg.a
                self.INC("hl", flags=[3,3,3,3])
                return 1,8

            elif op == "3": # INC HL
                self.INC("hl", flags=[3,3,3,3])
                return 1,8

            elif op == "4": # INC H
                self.INC("h")
                return 1,4

            elif op == "5": # DEC H
                self.DEC("h")
                return 1,4

            elif op == "6": # LD H,d8
                self.LD("h",int(rom[self.reg.pc+1],16))
                return 2,8
            
            elif op == "7": # DAA
                # TODO
                return 1,4
                
            elif op == "8": # JR Z,r8
                if self.reg.flags[3]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8

            elif op == "9": # ADD HL,HL
                self.ADD("hl",self.reg.hl, flags=[3,0,2,2])
                return 1,8

            elif op == "A": # LD A,(HL+)
                self.reg.a = self.mem[self.reg.hl]
                self.INC("hl", flags=[3,3,3,3])
                return 1,8

            elif op == "B": # DEC HL
                self.DEC("hl", flags=[3,3,3,3])
                return 1,8

            elif op == "C": # INC L
                self.INC("l")
                return 1,4

            elif op == "D": # DEC L
                self.DEC("l")
                return 1,4

            elif op == "E": # LD L,d8
                self.LD("l",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # CPL
                self.reg.a = 255-self.reg.a
                self.reg.flags[1] = 1
                self.reg.flags[2] = 1
                return 1,4
        
        elif ref == "3":
            if op == "0": # JR NC,r8
                if not self.reg.flags[3]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8
            
            elif op == "1": # LD SP,d16
                bts = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                self.LD("sp",int(bts, 16))
                return 3,12

            elif op == "2": # LD (HL-),A
                self.LD("(hl)", self.reg.a)
                self.DEC("hl", flags=[3,3,3,3])
                return 1,8

            elif op == "3": # INC SP
                self.INC("sp", flags=[3,3,3,3])
                return 1,8

            elif op == "4": # INC (HL)
                self.INC("(hl)")
                return 1,12

            elif op == "5": # DEC (HL)
                self.DEC("(hl)")
                return 1,12

            elif op == "6": # LD (HL),d8
                self.LD("(hl)", int(rom[self.reg.pc+1],16))
                return 2,12

            elif op == "7": # SCF
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1
                # TODO: rly?
                return 1,4

            elif op == "8": # JR C,r8
                if self.reg.flags[3]:
                    jump = int(rom[self.reg.pc+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8

            elif op == "9": # ADD HL,SP
                self.ADD("hl",self.reg.sp, flags=[3,0,2,2])
                return 1,8

            elif op == "A": # LD A,(HL-)
                self.LD("a", self.mem[self.reg.hl])
                self.DEC("hl", flags=[3,3,3,3])
                return 1,8

            elif op == "B": # DEC SP
                self.DEC("sp", flags=[3,3,3,3])
                return 1,8

            elif op == "C": # INC A
                self.INC("a")
                return 1,4

            elif op == "D": # DEC A
                self.DEC("a")
                return 1,4

            elif op == "E": # LD A,d8
                self.LD("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # CCF
                self.reg.flags[1] = 0
                self.reg.flags[2] = 0
                self.reg.flags[3] = 1 if not self.reg.flags[3] else 0
                return 1,4

        elif ref == "C":
            if op == "0": # RET NZ
                # TODO
                return 1,8

            elif op == "1": # POP BC
                self.reg.c = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.b = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif op == "2": # JP NZ,a16
                if not self.reg.flags[0]:
                    address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                    address = int(address, 16)
                    jump = self.mem[address]
                    if jump > 127: jump -= 255
                    return 3+jump, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "3": # JP a16
                address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                address = int(address, 16)
                jump = self.mem[address]
                if jump > 127: jump -= 255
                return 3+jump,16
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "4": # CALL NZ,a16
                # TODO
                return 3,12

            elif op == "5": # PUSH BC
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.b
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.c
                return 1,16

            elif op == "6": # ADD A,d8
                self.ADD("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "7": # RST 00H
                # TODO
                return 1,16

            elif op == "8": # RET Z
                # TODO: Stack stuff
                if self.reg.flags[0]:
                    return 1,20
                return 1,8

            elif op == "9": # RET
                self.reg.pc = self.mem[self.reg.sp]
                return 1,16

            elif op == "A": # JP Z,a16
                if self.reg.flags[0]:
                    address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                    address = int(address, 16)
                    jump = self.mem[address]
                    if jump > 127: jump -= 255
                    return 3+jump, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "B": # PREFIX CB
                t = self.PREFIX_CB(rom[self.reg.pc+1])
                return 2,t

            elif op == "C": # CALL Z,a16
                # TODO CALLS
                if self.reg.flags[0]:
                    return 3,24
                return 3,12

            elif op == "D": # CALL a16
                # TODO CALLS
                return 3,24

            elif op == "E": # ADC A,d8
                self.ADC("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # RST 08H
                # TODO
                return 1,16

        elif ref == "D":
            if op == "0": # RET NC
                # TODO
                return 1,8

            elif op == "1": # POP DE
                self.reg.e = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.d = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif op == "2": # JP NC,a16
                if not self.reg.flags[3]:
                    address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                    address = int(address, 16)
                    jump = self.mem[address]
                    if jump > 127: jump -= 255
                    return 3+jump, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "3": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "4": # CALL NC,a16
                # TODO
                return 3,12

            elif op == "5": # PUSH DE
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.d
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.e
                return 1,16

            elif op == "6": # SUB d8
                self.SUB("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "7": # RST 10H
                # TODO
                return 1,16

            elif op == "8": # RET C
                # TODO: Stack stuff
                if self.reg.flags[3]:
                    return 1,20
                return 1,8

            elif op == "9": # RETI
                # TODO: Stack stuff
                return 1,16

            elif op == "A": # JP C,a16
                if self.reg.flags[3]:
                    address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                    address = int(address, 16)
                    jump = self.mem[address]
                    if jump > 127: jump -= 255
                    return 3+jump, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "B": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "C": # CALL C,a16
                # TODO CALLS
                if self.reg.flags[3]:
                    return 3,24
                return 3,12

            elif op == "D": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "E": # SBC A,d8
                self.SBC("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # RST 18H
                # TODO
                return 1,16

        elif ref == "E":
            if op == "0": # LDH (a8),A
                self.mem[self.reg.a] = int(rom[self.reg.pc+1],16)
                return 2,12

            elif op == "1": # POP HL
                self.reg.l = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.h = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif op == "2": # LD (C),A
                self.mem[self.reg.c] = self.reg.a
                return 2,8

            elif op == "3": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "4": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "5": # PUSH HL
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.h
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.l
                return 1,16

            elif op == "6": # AND d8
                self.AND("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "7": # RST 20H
                # TODO
                return 1,16

            elif op == "8": # ADD SP,r8
                # TODO
                return 2,16

            elif op == "9": # JP (HL)
                jump = self.mem[self.reg.hl]
                if jump > 127: jump -= 255
                return 1,4
                # TODO: Check if I'm right on this

            elif op == "A": # LD (a16),A
                address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                address = int(address, 16)
                self.mem[address] = self.reg.a
                # TODO: Address bytes right order in RAM?
                return 3,16

            elif op == "B": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "C": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "D": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "E": # XOR d8
                self.XOR("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # RST 28H
                # TODO
                return 1,16

        elif ref == "F":
            if op == "0": # LDH A,(a8)
                # TODO: Am I right on this? What's the H for?
                self.LD("a", self.mem[int(rom[self.reg.pc+1],16)])
                return 2,12

            elif op == "1": # POP AF
                self.reg.f = self.mem[self.reg.sp]
                self.reg.sp += 1
                self.reg.a = self.mem[self.reg.sp]
                self.reg.sp += 1
                return 1,12

            elif op == "2": # LD A,(C)
                self.LD("a", self.mem[self.reg.c])
                return 2,8

            elif op == "3": # DI
                # TODO: Reset flipflops?
                return 1,4

            elif op == "4": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "5": # PUSH AF
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.a
                self.reg.sp -= 1
                self.mem[self.reg.sp] = self.reg.f
                return 1,16

            elif op == "6": # OR d8
                self.OR("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "7": # RST 30H
                # TODO
                return 1,16

            elif op == "8": # LD HL,SP+r8
                # TODO
                return 2,12

            elif op == "9": # LD SP,HL
                self.LD("sp",self.reg.hl)
                return 1,8

            elif op == "A": # LD A, (a16)
                address = rom[self.reg.pc+2] + rom[self.reg.pc+1]
                address = int(address, 16)
                self.LD("a",self.mem[address])
                # TODO: Address bytes right order in RAM?
                return 3,16

            elif op == "B": # EI
                # TODO
                return 1,4

            elif op == "C": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "D": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "E": # CP d8
                self.CP("a",int(rom[self.reg.pc+1],16))
                return 2,8

            elif op == "F": # RST 38H
                # TODO
                return 1,16
        
        else:
            raise OpcodeException("Opcode %s does not exist" % byte)
