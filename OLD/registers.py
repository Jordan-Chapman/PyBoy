# Author: Jordan Chapman
# Registers rebuilt using a "Register" object
# Contains:
#   Register object; with methods for getting/setting/math, and flag handling
#   FlagRegister object; Register object specifially for the "f" register
#   DualRegister object; 16 bit combo of 2 8bit registers
#   MemoryRegister object; Memory access interface for a 16 bit register

ADD = 0
SUB = 1


def bin_to_dec(binval):
    """
    Convert a binary list to a decimal integer
    :param binval: List of 8 bits [1,0]
    :return: Decimal value of the binary list
    """
    val = 0
    for bit in binval:
        val = (val << 1) | bit
    return val


def dec_to_bin(val, size=8):
    """
    Convert a decimal integer to a binary list
    :param val: Decimal integer
    :param size: Bit size of list to return
    :return: Binary list of size 'size'
    """
    binvalue = [int(i) for i in bin(val)[2:]]
    binvalue = [0]*(size-len(binvalue)) + binvalue
    return binvalue


class RegisterError(Exception):
    """
    Exception called when a user attempts to index a register with a non-integer
    """
    pass


class Register:
    """
    8bit register that stores its value as a decimal integer and a binary list
    """
    def __init__(self):
        self.value = 0
        self.binvalue = [0]*8
        self.zero = 0
        self.halfcarry = 0
        self.carry = 0

        self.report = False
    
    def get_val(self):
        return self.value
    
    def set_val(self, val):
        val = val%256
        self.value = val
        self.binvalue = [int(i) for i in bin(val)[2:]]
        self.binvalue = [0]*(8-len(self.binvalue)) + self.binvalue

    def get_binval(self):
        return self.binvalue.copy()

    def set_binval(self, binval):
        self.binvalue = binval.copy()
        self.value = bin_to_dec(self.binvalue)

    def add(self, val):
        self.check_flags(val, ADD)
        self.set_val(self.get_val() + val)

    def sub(self, val):
        self.check_flags(val, SUB)
        self.set_val(self.get_val() - val)

    def mod(self, val):
        """
        Modify the value of the register relatively
        This operation does not do flag checking
        """
        self.set_val(self.value + val)

    def test(self, bit):
        if self[bit] == 0:
            self.zero = 1
        else:
            self.zero = 0

    def set_zero(self):
        if self.get_val() == 0:
            self.zero = 1
        else:
            self.zero = 0

    def rlc(self): # Rotate left, copy high bit to carry/low bit
        binval = self.get_binval()
        self.carry = self[7]
        self.set_binval(binval[1:] + [binval[0]])
        self.set_zero()

    def rrc(self): # Rotate right, copy low bit to carry/high bit
        binval = self.get_binval()
        self.carry = self[0]
        self.set_binval([binval[7]] + binval[:7])
        self.set_zero()

    def rl(self, carry): # Rotate left, copy high bit to carry and carry to low bit
        binval = self.get_binval()
        low = carry
        self.carry = self[7]
        self.set_binval(binval[1:] + [low])
        self.set_zero()

    def rr(self, carry): # Rotate right, copy low bit to carry and carry to high bit
        binval = self.get_binval()
        high = carry
        self.carry = self[0]
        self.set_binval([high] + binval[:7])
        self.set_zero()

    def sla(self): # Shift left, copy high bit to carry and reset low bit
        binval = self.get_binval()
        self.carry = self[7]
        self.set_binval(binval[1:] + [0])
        self.set_zero()

    def sra(self): # Shift right, copy low bit to carry and leave high bit
        binval = self.get_binval()
        self.carry = self[0]
        self.set_binval(binval[0] + binval[:7])

    def swap(self): # Swap lower 4 bits with upper 4 bits
        binval = self.get_binval()
        binval = binval[4:8] + binval[0:4]
        self.set_binval(binval)

    def srl(self): # Shift right, copy low bit to carry and reset high bit
        binval = self.get_binval()
        self.carry = self[0]
        self.set_binval([0] + binval[:7])
        self.set_zero()

    def check_flags(self, val, op):
        if op == ADD:
            if ((self.get_val()&0xf) + (val&0xf))&0x10:
                self.halfcarry = 1
            else:
                self.halfcarry = 0
                
            if self.get_val() + val >= 256:
                self.carry = 1
            else:
                self.carry = 0
                
            if (self.get_val() + val) % 256 == 0:
                self.zero = 1
            else:
                self.zero = 0
                
        elif op == SUB:
            if ((self.get_val()&0xf) - (val&0xf))&0x10:
                self.halfcarry = 1
            else:
                self.halfcarry = 0
                
            if self.get_val() - val < 0:
                self.carry = 1
            else:
                self.carry = 0
                
            if (self.get_val() - val) % 256 == 0:
                self.zero = 1
            else:
                self.zero = 0

    ### Builtins ###

    def __getitem__(self, key):
        if type(key) != int:
            raise RegisterError("Registers must be indexed with integers")
        return self.binvalue[7-key]
    def __setitem__(self, key, value):
        if type(key) != int:
            raise RegisterError("Registers must be indexed with integers")
        self.binvalue[7-key] = value
        self.value = bin_to_dec(self.binvalue)
    def __iadd__(self, val):
        self.add(val)
        return self
    def __isub__(self, val):
        self.sub(val)
        return self
    def __add__(self, val):
        return self.get_val() + val
    def __sub__(self, val):
        return self.get_val() - val
    def __str__(self):
        return str(self.binvalue)
    def __repr__(self):
        return str(self.binvalue)


class FlagRegister(Register):
    # Special register that always disposes of the lower 4 bits
    
    def set_val(self, val):
        super().set_val(val & 0b11110000)

    def get_z(self):
        return self[7]
    def set_z(self, val):
        self[7] = val
        self.value = bin_to_dec(self.binvalue)
    z = property(get_z, set_z)

    def get_n(self):
        return self[6]
    def set_n(self, val):
        self[6] = val
        self.value = bin_to_dec(self.binvalue)
    n = property(get_n, set_n)

    def get_h(self):
        return self[5]
    def set_h(self, val):
        self[5] = val
        self.value = bin_to_dec(self.binvalue)
    h = property(get_h, set_h)

    def get_c(self):
        return self[4]
    def set_c(self, val):
        self[4] = val
        self.value = bin_to_dec(self.binvalue)
    c = property(get_c, set_c)


class DualRegister:
    # 16 bit subtraction does not exist; it would be too complex and require 3 carry checks
    def __init__(self, reg1, reg2):
        # reg1 being the higher register, reg2 the lower.
        self.reg1 = reg1
        self.reg2 = reg2
        self.carry = 0
        self.halfcarry = 0
        
    def set_val(self, val):
        self.reg1.set_val(val//256)
        self.reg2.set_val(val%256)

    def get_val(self):
        return self.reg1.get_val()*256 + self.reg2.get_val()
        
    def add(self, val):
        low_val = val%256
        high_val = val//256
        self.reg2.add(low_val)
        self.reg1.add(high_val+self.reg2.carry)
        self.check_flags()
        
    def sub(self, val):
        low_val = val%256
        high_val = val//256
        self.reg2.sub(low_val)
        self.reg1.sub(high_val+self.reg2.carry)
        self.check_flags()

    def mod(self, val):
        self.set_val(self.get_val() + val)

    def check_flags(self):
        self.carry = self.reg1.carry
        self.halfcarry = self.reg1.halfcarry

    def __iadd__(self, val):
        self.add(val)
        return self
    def __isub__(self, val):
        self.sub(val)
        return self
    def __add__(self, val):
        return self.get_val() + val
    def __sub__(self, val):
        return self.get_val() - val
    def __str__(self):
        return str(self.reg1.binvalue + self.reg2.binvalue)
    def __repr__(self):
        return str(self.reg1.binvalue + self.reg2.binvalue)


class MemoryRegister(Register):
    # Way to use a register as a memory address
    def __init__(self, reg, mem):
        super().__init__()
        self.reg = reg
        self.mem = mem
        self.zero = 0
        self.halfcarry = 0
        self.carry = 0
    
    def get_val(self):
        return self.mem[self.reg.get_val()]
    
    def set_val(self, val):
        self.mem[self.reg.get_val()] = val

    def get_binval(self):
        return dec_to_bin(self.get_val())

    def set_binval(self, binval):
        self.set_val(bin_to_dec(binval))

    ### Builtins ###

    def __getitem__(self, key):
        if type(key) != int:
            raise RegisterError("Registers must be indexed with integers")
        return dec_to_bin(self.get_val())[7-key]
    def __setitem__(self, key, value):
        if type(key) != int:
            raise RegisterError("Registers must be indexed with integers")
        binvalue = dec_to_bin(self.get_val())
        binvalue[7-key] = value
        self.set_val(bin_to_dec(binvalue))
    def __str__(self):
        return hex(self.reg.get_val())
    def __repr__(self):
        return hex(self.reg.get_val())
