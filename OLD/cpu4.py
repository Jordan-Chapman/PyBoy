# Author: Jordan Chapman
# 4th cpu - based on 2nd revision, now using the 'registers.py' module

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

from registers import Register, FlagRegister, DualRegister, MemoryRegister

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

class Registers:
    """ Registers object, keeps track of CPU registers """
    # Registers only deal in integers.
    #  convert all hex to int before passing to registers
    def __init__(self, mem, silent):
        self.b = Register()
        self.c = Register()
        self.bc = DualRegister(self.b,self.c)
        self.d = Register()
        self.e = Register()
        self.de = DualRegister(self.d,self.e)
        self.h = Register()
        self.l = Register()
        self.hl = DualRegister(self.h,self.l)
        self.a = Register()
        self.f = FlagRegister()
        self.af = DualRegister(self.a,self.f)
        self.sp = DualRegister(Register(),Register())
        self.pc = DualRegister(Register(),Register())
        self.mem = mem
        self.hlm = MemoryRegister(self.hl, self.mem)
        
        self.REG_TABLE = {"000":self.b,
                          "001":self.c,
                          "010":self.d,
                          "011":self.e,
                          "100":self.h,
                          "101":self.l,
                          "110":self.hlm,
                          "111":self.a}

        self.silent = silent

    def set_flags(self, template, reg):
        """
        Set the flag register based on the given parameters
        template = flag template array (see top of the file "FLAG RULES"
        reg = register to set flags based on
        """
        # Zero flag
        if template[0] == 0:
            self.f.z = 0
        elif template[0] == 1:
            self.f.z = 1
        elif template[0] == 2:
            self.f.z = reg.zero

        # Subtraction flag
        if template[1] == 0:
            self.f.n = 0
        elif template[1] == 1:
            self.f.n = 1
        elif template[1] == 2: # Never used in this method
            pass

        # Half-carry flag
        if template[2] == 0:
            self.f.h = 0
        elif template[2] == 1:
            self.f.h = 1
        elif template[2] == 2:
            self.f.h = reg.halfcarry

        # Carry flag
        if template[3] == 0:
            self.f.c = 0
        elif template[3] == 1:
            self.f.c = 1
        elif template[3] == 2:
            self.f.c = reg.carry

        if not self.silent: print("Set flags to %s" % self.f)

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
        self.mem = [0]*0x10000
        self.stack = []
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

    def ret(self):
        low = self.mem[self.reg.sp.get_val()]
        self.reg.sp += 1
        high = self.mem[self.reg.sp.get_val()]
        self.reg.sp += 1
        self.reg.pc.set_val(high*256 + low)

    def call(self, rom):
        high = (self.reg.pc.get_val()+3)//256
        low = (self.reg.pc.get_val()+3)%256
        self.reg.sp.set_val(self.reg.sp.get_val()-1)
        self.mem[self.reg.sp.get_val()] = high
        self.reg.sp.set_val(self.reg.sp.get_val()-1)
        self.mem[self.reg.sp.get_val()] = low
        address = rom[self.reg.pc + 2] + rom[self.reg.pc + 1]
        address = int(address, 16)
        self.reg.pc.set_val(address)

    def INC(self, dest):
        dest.add(1)

    def DEC(self, dest):
        dest.sub(1)

    def ADD(self, dest, source):
        dest.add(source.get_val())

    def ADC(self, dest, source):
        dest.add(source.get_val() + self.reg.f.c)

    def SUB(self, dest, source):
        dest.sub(source.get_val())

    def SBC(self, dest, source):
        dest.sub(source.get_val() + self.reg.f.c)

    def AND(self, dest, source):
        dest.set_val(source.get_val() & dest.get_val())

    def XOR(self, dest, source):
        dest.set_val(source.get_val() ^ dest.get_val())

    def OR(self, dest, source):
        dest.set_val(source.get_val() | dest.get_val())

    def CP(self, dest, source):
        val = dest.get_val()
        dest.sub(source.get_val())
        dest.set_val(val)

    def PREFIX_CB(self, bts):
        """ Does a "Prefix CB" table operation, and returns the cycle duration"""
        time = 8
        bins = bin(int(bts,16))[2:]
        bins = "0"*(8-len(bins)) + bins
        type_bits = bins[0:2]
        
        level_bits = bins[2:5]
        bit = int(level_bits, 2)
        
        reg_bits = bins[5:8]
        register = self.reg.REG_TABLE[reg_bits]

        if register == self.reg.hlm:
            time = 16 # Memory access takes longer than register access

        # Variable "type_bits" = first 2 bits; determine what type of operation to perform
        # Variable "bits" = binary value of the chosen register (or RAM at location (HL))
        # Variable "bit" = integer value of the "level" bits; different use depending on type_bits

        # CB Table

        if type_bits == "00": # Rotations
            if not self.silent: print("CB rotation operation %s on register: %s" % (bit, register))
            if bit == 0: # RLC
                register.rlc()
                self.reg.set_flags([2,0,0,2], register)

            elif bit == 1: # RRC
                register.rrc()
                self.reg.set_flags([2,0,0,2], register)
            
            elif bit == 2: # RL
                register.rl(self.reg.f.c)
                self.reg.set_flags([2,0,0,2], register)

            elif bit == 3: # RR
                register.rr(self.reg.f.c)
                self.reg.set_flags([2,0,0,2], register)

            elif bit == 4: # SLA
                register.sla()
                self.reg.set_flags([2,0,0,2], register)

            elif bit == 5: # SRA
                register.sra()
                self.reg.set_flags([2,0,0,0], register)

            elif bit == 6: # SWAP
                register.swap()
                self.reg.set_flags([2,0,0,0], register)

            elif bit == 7: # SRL
                register.srl()
                self.reg.set_flags([2,0,0,2], register)

        elif type_bits == "01": # Test bits
            if not self.silent: print("CB testing bit %s of register: %s" % (bit, register))
            register.test(bit)
            self.reg.set_flags([2,0,1,3], register)

        elif type_bits == "10": # Resets
            if not self.silent: print("CB resetting bit %s of register: %s" % (bit, register))
            register[bit] = 0

        elif type_bits == "11": # Sets
            if not self.silent: print("CB setting bit %s of register: %s" % (bit, register))
            register[bit] = 1

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
        byte = rom[self.reg.pc.get_val()] # Reading byte from ROM
        ref = byte[0] # Row on opcode table
        op = byte[1] # Column on opcode table
        
        if not self.silent: print("Excecuting opcode '%s' at position '%s'" % (byte,hex(self.reg.pc.get_val())))

        if ref in ["4","5","6","7"]: # LD operations + HALT
            # Read as binary string
            # Example (01001010)
            #   First 2 bits (01) = LD operations
            #   Next 3 bits (001) = C register
            #   Last 3 bits (010) = D register
            # 01001010 = Load into C from D
            
            bits = bin(int(byte,16))[2:]
            bits = "0"*(8-len(bits)) + bits
            dest = self.reg.REG_TABLE[bits[2:5]]
            source = self.reg.REG_TABLE[bits[5:8]]
            if dest == source == self.reg.hlm:
                input("HALT OPERATION")
                # TODO HALT
                return 1,4
            dest.set_val(source.get_val())
            if dest == self.reg.hlm or source == self.reg.hlm:
                return 1,8
            return 1,4

        elif ref in ["8","9","A","B"]: # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
            bits = bin(int(byte,16))[2:]
            bits = "0"*(8-len(bits)) + bits
            operation = bits[2:5]
            
            dest = self.reg.a
            source = self.reg.REG_TABLE[bits[5:8]]
            
            if operation == "000": # ADD
                self.ADD(dest, source)
                self.reg.set_flags([2,0,2,2], dest)
            elif operation == "001": # ADC
                self.ADC(dest, source)
                self.reg.set_flags([2,0,2,2], dest)
            elif operation == "010": # SUB
                self.SUB(dest, source)
                self.reg.set_flags([2,1,2,2], dest)
            elif operation == "011": # SBC
                self.SBC(dest, source)
                self.reg.set_flags([2,1,2,2], dest)
            elif operation == "100": # AND
                self.AND(dest, source)
                self.reg.set_flags([2,0,0,0], dest)
            elif operation == "101": # XOR
                self.XOR(dest, source)
                self.reg.set_flags([2,0,0,0], dest)
            elif operation == "110": # OR
                self.OR(dest, source)
                self.reg.set_flags([2,0,0,0], dest)
            elif operation == "111": # CP
                self.CP(dest, source)
                self.reg.set_flags([2,1,2,2], dest)
            
            if source == self.reg.hlm:
                return 1,8
            return 1,4

        elif ref == "0":
            if op == "0": # NOP
                return 1,4

            elif op == "1": # LD BC,d16
                bts = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                self.reg.bc.set_val(int(bts, 16))
                return 3,12

            elif op == "2": # LD (BC),A
                self.mem[self.reg.bc.get_val()] = self.reg.a.get_val()
                return 1,8

            elif op == "3": # INC BC
                self.INC(self.reg.bc)
                return 1,8

            elif op == "4": # INC B
                self.INC(self.reg.b)
                self.reg.set_flags([2,0,2,3], self.reg.b)
                return 1,4

            elif op == "5": # DEC B
                self.DEC(self.reg.b)
                self.reg.set_flags([2,1,2,3], self.reg.b)
                return 1,4

            elif op == "6": # LD B,d8
                self.reg.b.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8

            elif op == "7": # RLCA
                self.reg.a.rlc()
                self.reg.set_flags([0,0,0,2],self.reg.a)
                return 1,4

            elif op == "8": # LD (a16),SP
                self.mem[int(rom[self.reg.pc.get_val()+1],16)] = self.reg.sp.get_val()
                return 3,20

            elif op == "9": # ADD HL,BC
                self.ADD(self.reg.hl,self.reg.bc)
                self.reg.set_flags([3,0,2,2], self.reg.hl)
                return 1,8

            elif op == "A": # LD A,(BC)
                self.reg.a.set_val(self.mem[self.reg.bc.get_val()])
                return 1,8

            elif op == "B": # DEC BC
                self.DEC(self.reg.bc)
                return 1,8

            elif op == "C": # INC C
                self.INC(self.reg.c)
                self.reg.set_flags([2,0,2,3], self.reg.c)
                return 1,4

            elif op == "D": # DEC C
                self.DEC(self.reg.c)
                self.reg.set_flags([2,1,2,3], self.reg.c)
                return 1,4

            elif op == "E": # LD C,d8
                self.reg.c.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8

            elif op == "F": # RRCA
                self.reg.a.rrc()
                self.reg.set_flags([0,0,0,2],self.reg.a)
                return 1,4

        elif ref == "1":
            if op == "0": # STOP
                print("STOPPING")
                return 2,4
            
            elif op == "1": # LD DE,d16
                bts = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                self.reg.de.set_val(int(bts, 16))
                return 3,12

            elif op == "2": # LD (DE),A
                self.mem[self.reg.de.get_val()] = self.reg.a.get_val()
                return 1,8

            elif op == "3": # INC DE
                self.INC(self.reg.de)
                return 1,8

            elif op == "4": # INC D
                self.INC(self.reg.d)
                self.reg.set_flags([2,0,2,3], self.reg.d)
                return 1,4

            elif op == "5": # DEC D
                self.DEC(self.reg.d)
                self.reg.set_flags([2,1,2,3], self.reg.d)
                return 1,4

            elif op == "6": # LD D,d8
                self.reg.d.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8

            elif op == "7": # RLA
                self.reg.a.rl(self.reg.f.c)
                self.reg.set_flags([0,0,0,2],self.reg.a)
                return 1,4

            elif op == "8": # JR r8
                jump = int(rom[self.reg.pc.get_val()+1], 16)
                if jump > 127: jump -= 255
                return 1+jump,12

            elif op == "9": # ADD HL,DE
                self.ADD(self.reg.hl,self.reg.de)
                self.reg.set_flags([3,0,2,2], self.reg.hl)
                return 1,8

            elif op == "A": # LD A,(DE)
                self.reg.a.set_val(self.mem[self.reg.de.get_val()])
                return 1,8

            elif op == "B": # DEC DE
                self.DEC(self.reg.de)
                return 1,8

            elif op == "C": # INC E
                self.INC(self.reg.e)
                self.reg.set_flags([2,0,2,3], self.reg.e)
                return 1,4

            elif op == "D": # DEC E
                self.DEC(self.reg.e)
                self.reg.set_flags([2,1,2,3], self.reg.e)
                return 1,4

            elif op == "E": # LD E,d8
                self.reg.e.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8

            elif op == "F": # RRA
                self.reg.a.rr(self.reg.f.c)
                self.reg.set_flags([0,0,0,2],self.reg.a)
                return 1,4

        elif ref == "2":
            if op == "0": # JR NZ,r8
                if not self.reg.f.z:
                    jump = int(rom[self.reg.pc.get_val()+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8

            elif op == "1": # LD HL,d16
                bts = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                self.reg.hl.set_val(int(bts, 16))
                return 3,12

            elif op == "2": # LD (HL+),A
                self.mem[self.reg.hl.get_val()] = self.reg.a.get_val()
                self.INC(self.reg.hl)
                return 1,8

            elif op == "3": # INC HL
                self.INC(self.reg.hl)
                return 1,8

            elif op == "4": # INC H
                self.INC(self.reg.h)
                self.reg.set_flags([2,0,2,3], self.reg.h)
                return 1,4

            elif op == "5": # DEC H
                self.DEC(self.reg.h)
                self.reg.set_flags([2,1,2,3], self.reg.h)
                return 1,4

            elif op == "6": # LD H,d8
                self.reg.h.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8
            
            elif op == "7": # DAA
                input("DAA")
                # TODO
                return 1,4
                
            elif op == "8": # JR Z,r8
                if self.reg.f.z:
                    jump = int(rom[self.reg.pc.get_val()+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8

            elif op == "9": # ADD HL,HL
                self.ADD(self.reg.hl,self.reg.hl)
                self.reg.set_flags([3,0,2,2], self.reg.hl)
                return 1,8

            elif op == "A": # LD A,(HL+)
                self.reg.a.set_val(self.mem[self.reg.hl.get_val()])
                self.INC(self.reg.hl)
                return 1,8

            elif op == "B": # DEC HL
                self.DEC(self.reg.hl)
                return 1,8

            elif op == "C": # INC L
                self.INC(self.reg.l)
                self.reg.set_flags([2,0,2,3], self.reg.l)
                return 1,4

            elif op == "D": # DEC L
                self.DEC(self.reg.l)
                self.reg.set_flags([2,1,2,3], self.reg.l)
                return 1,4

            elif op == "E": # LD L,d8
                self.reg.l.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8

            elif op == "F": # CPL
                self.reg.a = 255-self.reg.a
                self.reg.f.n = 1
                self.reg.f.h = 1
                return 1,4
        
        elif ref == "3":
            if op == "0": # JR NC,r8
                if not self.reg.f.c:
                    jump = int(rom[self.reg.pc.get_val()+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8
            
            elif op == "1": # LD SP,d16
                bts = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                self.reg.sp.set_val(int(bts, 16))
                return 3,12

            elif op == "2": # LD (HL-),A
                self.mem[self.reg.hl.get_val()] = self.reg.a.get_val()
                self.DEC(self.reg.hl)
                return 1,8

            elif op == "3": # INC SP
                self.INC(self.reg.sp)
                return 1,8

            elif op == "4": # INC (HL)
                self.INC(self.reg.hlm)
                self.reg.set_flags([2,0,2,3], self.reg.hlm)
                return 1,12

            elif op == "5": # DEC (HL)
                self.DEC(self.reg.hlm)
                self.reg.set_flags([2,1,2,3], self.reg.hlm)
                return 1,12

            elif op == "6": # LD (HL),d8
                self.reg.hlm.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,12

            elif op == "7": # SCF
                self.reg.f.n = 0
                self.reg.f.h = 0
                self.reg.f.c = 1
                return 1,4

            elif op == "8": # JR C,r8
                if self.reg.f.c:
                    jump = int(rom[self.reg.pc.get_val()+1], 16)
                    if jump > 127: jump -= 255
                    return 1+jump, 12
                else:
                    return 2, 8

            elif op == "9": # ADD HL,SP
                self.ADD(self.reg.hl,self.reg.sp)
                self.reg.set_flags([3,0,2,2], self.reg.hl)
                return 1,8

            elif op == "A": # LD A,(HL-)
                self.reg.a.set_val(self.mem[self.reg.hl.get_val()])
                self.DEC(self.reg.hl)
                return 1,8

            elif op == "B": # DEC SP
                self.DEC(self.reg.sp)
                return 1,8

            elif op == "C": # INC A
                self.INC(self.reg.a)
                self.reg.set_flags([2,0,2,3], self.reg.a)
                return 1,4

            elif op == "D": # DEC A
                self.DEC(self.reg.a)
                self.reg.set_flags([2,1,2,3], self.reg.a)
                return 1,4

            elif op == "E": # LD A,d8
                self.reg.a.set_val(int(rom[self.reg.pc.get_val()+1],16))
                return 2,8

            elif op == "F": # CCF
                self.reg.f.n = 0
                self.reg.f.h = 0
                self.reg.f.c = 1 if not self.reg.f.c else 0
                return 1,4

        elif ref == "C":
            if op == "0": # RET NZ
                if not self.reg.f.z:
                    self.ret()
                    return 0,20
                return 1,8

            elif op == "1": # POP BC
                self.reg.c.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                self.reg.b.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                return 1,12

            elif op == "2": # JP NZ,a16
                if not self.reg.f.z:
                    address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                    address = int(address, 16)
                    self.reg.pc.set_val(address)
                    return 0, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "3": # JP a16
                address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                address = int(address, 16)
                self.reg.pc.set_val(address)
                return 0,16
                
            elif op == "4": # CALL NZ,a16
                if not self.reg.f.z:
                    self.call(rom)
                    return 0,24
                return 3,12

            elif op == "5": # PUSH BC
                self.reg.sp.set_val(self.reg.sp.get_val()-1)
                self.mem[self.reg.sp.get_val()] = self.reg.b.get_val()
                self.reg.sp.set_val(self.reg.sp.get_val()-1)
                self.mem[self.reg.sp.get_val()] = self.reg.c.get_val()
                return 1,16

            elif op == "6": # ADD A,d8
                self.reg.a.add(int(rom[self.reg.pc.get_val()+1],16))
                self.reg.set_flags([2,0,2,2], self.reg.a)
                return 2,8

            elif op == "7": # RST 00H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x0)
                return 1,16

            elif op == "8": # RET Z
                if self.reg.f.z:
                    self.ret()
                    return 0,20
                return 1,8

            elif op == "9": # RET
                self.ret()
                return 0,16

            elif op == "A": # JP Z,a16
                if self.reg.f.z:
                    address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                    address = int(address, 16)
                    self.reg.pc.set_val(address)
                    return 0, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "B": # PREFIX CB
                t = self.PREFIX_CB(rom[self.reg.pc.get_val()+1])
                return 2,t

            elif op == "C": # CALL Z,a16
                if self.reg.f.z:
                    self.call(rom)
                    return 0,24
                return 3,12

            elif op == "D": # CALL a16
                self.call(rom)
                return 0,24

            elif op == "E": # ADC A,d8
                self.reg.a.add(int(rom[self.reg.pc.get_val()+1],16) + self.reg.f.c)
                self.reg.set_flags([2,0,2,2], self.reg.a)
                return 2,8

            elif op == "F": # RST 08H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x8)
                return 1,16

        elif ref == "D":
            if op == "0": # RET NC
                if not self.reg.f.c:
                    self.ret()
                    return 0,20
                return 1,8

            elif op == "1": # POP DE
                self.reg.e.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                self.reg.d.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                return 1,12

            elif op == "2": # JP NC,a16
                if not self.reg.f.c:
                    address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                    address = int(address, 16)
                    self.reg.pc.set_val(address)
                    return 0, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "3": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "4": # CALL NC,a16
                if not self.reg.f.c:
                    self.call(rom)
                    return 0,24
                return 3,12

            elif op == "5": # PUSH DE
                self.reg.sp -= 1
                self.mem[self.reg.sp.get_val()] = self.reg.d.get_val()
                self.reg.sp -= 1
                self.mem[self.reg.sp.get_val()] = self.reg.e.get_val()
                return 1,16

            elif op == "6": # SUB d8
                self.reg.a.sub(int(rom[self.reg.pc.get_val()+1],16))
                self.reg.set_flags([2,1,2,2], self.reg.a)
                return 2,8

            elif op == "7": # RST 10H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x10)
                return 1,16

            elif op == "8": # RET C
                if self.reg.f.c:
                    self.ret()
                    return 0,20
                return 1,8

            elif op == "9": # RETI
                # TODO: Enable interrupts
                self.ret()
                return 0,16

            elif op == "A": # JP C,a16
                if self.reg.f.c:
                    address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                    address = int(address, 16)
                    self.reg.pc.set_val(address)
                    return 0, 16
                else:
                    return 3, 12
                # TODO: Check if I'm right: jumping distance of signed byte at address from ROM

            elif op == "B": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "C": # CALL C,a16
                if self.reg.f.c:
                    self.call(rom)
                    return 0,24
                return 3,12

            elif op == "D": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "E": # SBC A,d8
                self.reg.a.sub(int(rom[self.reg.pc.get_val()+1],16) + self.reg.f.c)
                self.reg.set_flags([2,1,2,2], self.reg.a)
                return 2,8

            elif op == "F": # RST 18H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x18)
                return 1,16

        elif ref == "E":
            if op == "0": # LDH (a8),A
                val = int(rom[self.reg.pc.get_val()+1],16) + 0xFF00
                self.mem[val] = self.reg.a.get_val()
                return 2,12

            elif op == "1": # POP HL
                self.reg.l.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                self.reg.h.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                return 1,12

            elif op == "2": # LD (C),A
                self.mem[0xff00+self.reg.c.get_val()] = self.reg.a.get_val()
                return 1,8

            elif op == "3": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "4": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "5": # PUSH HL
                self.reg.sp -= 1
                self.mem[self.reg.sp.get_val()] = self.reg.h.get_val()
                self.reg.sp -= 1
                self.mem[self.reg.sp.get_val()] = self.reg.l.get_val()
                return 1,16

            elif op == "6": # AND d8
                self.reg.a.set_val(self.reg.a.get_val() & (int(rom[self.reg.pc.get_val()+1],16)))
                self.reg.set_flags([2,0,1,0], self.reg.a)
                return 2,8

            elif op == "7": # RST 20H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x20)
                return 1,16

            elif op == "8": # ADD SP,r8
                jump = int(rom[self.reg.pc.get_val()+1])
                if jump > 127: jump -= 255
                self.reg.sp.add(jump)
                self.reg.set_flags([0,0,2,2], self.reg.sp)
                return 2,16

            elif op == "9": # JP (HL)
                self.reg.pc.set_val(self.reg.hlm.get_val())
                return 0,4

            elif op == "A": # LD (a16),A
                address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                address = int(address, 16)
                self.mem[address] = self.reg.a.get_val()
                # TODO: Address bytes right order in RAM?
                return 3,16

            elif op == "B": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "C": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "D": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "E": # XOR d8
                self.reg.a.set_val(self.reg.a.get_val() ^ (int(rom[self.reg.pc.get_val()+1],16)))
                self.reg.set_flags([2,0,0,0], self.reg.a)
                return 2,8

            elif op == "F": # RST 28H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x28)
                return 1,16

        elif ref == "F":
            if op == "0": # LDH A,(a8)
                val = int(rom[self.reg.pc.get_val()+1],16) + 0xFF00
                self.reg.a.set_val(self.mem[val])
                return 2,12

            elif op == "1": # POP AF
                self.reg.f.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                self.reg.a.set_val(self.mem[self.reg.sp.get_val()])
                self.reg.sp += 1
                return 1,12

            elif op == "2": # LD A,(C)
                self.reg.a.set_val(self.mem[0xff00+self.reg.c.get_val()])
                return 1,8

            elif op == "3": # DI
                # TODO: Reset flipflops?
                return 1,4

            elif op == "4": # DOES NOT EXIST
                raise OpcodeException("Opcode %s does not exist" % byte)

            elif op == "5": # PUSH AF
                self.reg.sp -= 1
                self.mem[self.reg.sp.get_val()] = self.reg.a.get_val()
                self.reg.sp -= 1
                self.mem[self.reg.sp.get_val()] = self.reg.f.get_val()
                return 1,16

            elif op == "6": # OR d8
                self.reg.a.set_val(self.reg.a.get_val() | (int(rom[self.reg.pc.get_val()+1],16)))
                self.reg.set_flags([2,0,0,0], self.reg.a)
                return 2,8

            elif op == "7": # RST 30H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x30)
                return 1,16

            elif op == "8": # LD HL,SP+r8
                input("LD HL,SP+r8")
                # TODO
                return 2,12

            elif op == "9": # LD SP,HL
                self.reg.sp.set_val(self.reg.hl.get_val())
                return 1,8

            elif op == "A": # LD A, (a16)
                address = rom[self.reg.pc.get_val()+2] + rom[self.reg.pc.get_val()+1]
                address = int(address, 16)
                self.reg.a.set_val(self.mem[address])
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
                val = self.reg.a.get_val()
                self.reg.a.sub(int(rom[self.reg.pc.get_val()+1],16))
                self.reg.a.set_val(val)
                self.reg.set_flags([2,1,2,2], self.reg.a)
                return 2,8

            elif op == "F": # RST 38H
                self.reg.sp += 1
                self.stack.append(self.reg.pc.get_val())
                self.reg.sp.set_val(0x38)
                return 1,16
        
        else:
            raise OpcodeException("Opcode %s does not exist" % byte)
