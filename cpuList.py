# Author: Jordan Chapman
# Another attempt at a fast/janky CPU; reading opcodes straight from a list, indexing them.
# But is it faster than the binary tree? Remains to be seen...

from consts import *

# <editor-fold desc="0X">
def f0x00(self): return 1,4
def f0x01(self): self.b = self.mem[self.pc+2]; self.c = self.mem[self.pc+1]; return 3,12
def f0x02(self): self.mem[(self.b<<8)+self.c] = self.a; return 1,8
def f0x03(self):
    self.c += 1
    if self.c >= 0x100:
        self.c %= 0x100; self.b += 1
        if self.b >= 0x100: self.b %= 0x100
    return 1,8
def f0x04(self): self.sub = 0; self.halfcarry = 1 if ((self.b&0xf) + 1)&0x10 else 0; self.b += 1; self.b %= 0x100; self.zero = 0 if self.b else 1; return 1,4
def f0x05(self): self.sub = 1; self.halfcarry = 1 if ((self.b&0xf) - 1)&0x10 else 0; self.b -= 1; self.b %= 0x100; self.zero = 0 if self.b else 1; return 1,4
def f0x06(self): self.b = self.mem[self.pc+1]; return 2,8
def f0x07(self):
    self.zero = 0; self.sub = 0; self.halfcarry = 0; self.a <<= 1
    if self.a >= 0x100:
        self.a -= 0x100
        self.a += 1
        self.carry = 1
    else: self.carry = 0
    return 1,4
def f0x08(self): self.sp = (self.mem[self.pc+2]<<8) + self.mem[self.pc+1]; return 3,20
def f0x09(self): self.sub = 0; self.l += self.c; self.carry = 1 if self.l >= 0x100 else 0; self.l %= 0x100; self.halfcarry = 1 if ((self.h&0xf) + self.b+self.carry)&0x10 else 0; self.h += self.b + self.carry; self.carry = 1 if self.h >= 0x100 else 0; self.h %= 0x100; return 1,8
def f0x0a(self): self.a = self.mem[(self.b<<8)+self.c]; return 1,8
def f0x0b(self):
    self.c -= 1
    if self.c < 0:
        self.c = 0xff; self.b -= 1
        if self.b < 0: self.b = 0xff
    return 1,8
def f0x0c(self): self.sub = 0; self.halfcarry = 1 if ((self.c&0xf) + 1)&0x10 else 0; self.c += 1; self.c %= 0x100; self.zero = 0 if self.c else 1; return 1,4
def f0x0d(self): self.sub = 1; self.halfcarry = 1 if ((self.c&0xf) - 1)&0x10 else 0; self.c -= 1; self.c %= 0x100; self.zero = 0 if self.c else 1; return 1,4
def f0x0e(self): self.c = self.mem[self.pc+1]; return 2,8
def f0x0f(self):
    self.zero = 0; self.sub = 0; self.halfcarry = 0
    if self.a%2 == 1:
        self.carry = 1
        self.a += 0x100
    else:
        self.carry = 0
    self.a >>= 1; return 1,4
# </editor-fold>
# <editor-fold desc="1X">
def f0x10(self): input("STOP"); return 2,4 # TODO: STOP
def f0x11(self): self.d = self.mem[self.pc+2]; self.e = self.mem[self.pc+1]; return 3,12
def f0x12(self): self.mem[(self.d<<8)+self.e] = self.a; return 1,8
def f0x13(self):
    self.e += 1
    if self.e >= 0x100:
        self.e %= 0x100; self.d += 1
        if self.d >= 0x100: self.d %= 0x100
    return 1,8
def f0x14(self): self.sub = 0; self.halfcarry = 1 if ((self.d&0xf) + 1)&0x10 else 0; self.d += 1; self.d %= 0x100; self.zero = 0 if self.d else 1; return 1,4
def f0x15(self): self.sub = 1; self.halfcarry = 1 if ((self.d&0xf) - 1)&0x10 else 0; self.d -= 1; self.d %= 0x100; self.zero = 0 if self.d else 1; return 1,4
def f0x16(self): self.d = self.mem[self.pc+1]; return 2,8
def f0x17(self): self.zero = 0; self.sub = 0; self.halfcarry = 0; self.a <<= 1; self.a += self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; return 1,4
def f0x18(self):
    jump = self.mem[self.pc+1]
    if jump >= 0x80: jump -= 0x100
    return 2+jump,12
def f0x19(self): self.sub = 0; self.l += self.e; self.carry = 1 if self.l >= 0x100 else 0; self.l %= 0x100; self.halfcarry = 1 if ((self.h&0xf) + self.d+self.carry)&0x10 else 0; self.h += self.d + self.carry; self.carry = 1 if self.h >= 0x100 else 0; self.h %= 0x100; return 1,8
def f0x1a(self): self.a = self.mem[(self.d<<8)+self.e]; return 1,8
def f0x1b(self):
    self.e -= 1
    if self.e < 0:
        self.e = 0xff; self.d -= 1
        if self.d < 0: self.d = 0xff
    return 1,8
def f0x1c(self): self.sub = 0; self.halfcarry = 1 if ((self.e&0xf) + 1)&0x10 else 0; self.e += 1; self.e %= 0x100; self.zero = 0 if self.e else 1; return 1,4
def f0x1d(self): self.sub = 1; self.halfcarry = 1 if ((self.e&0xf) - 1)&0x10 else 0; self.e -= 1; self.e %= 0x100; self.zero = 0 if self.e else 1; return 1,4
def f0x1e(self): self.e = self.mem[self.pc+1]; return 2,8
def f0x1f(self): self.zero = 0; self.sub = 0; self.halfcarry = 0; self.a += self.carry*0x100; self.carry = 1 if self.a&2 == 1 else 0; self.a >>= 1; return 1,4
# </editor-fold>
# <editor-fold desc="2X">
def f0x20(self):
    if self.zero: return 2,8
    jump = self.mem[self.pc+1]
    if jump >= 0x80: jump -= 0x100
    return 2+jump,12
def f0x21(self): self.h = self.mem[self.pc+2]; self.l = self.mem[self.pc+1]; return 3,12
def f0x22(self):
    self.mem[(self.h<<8)+self.l] = self.a; self.l += 1
    if self.l == 0x100: self.l = 0; self.h += 1; self.h %= 0x100
    return 1,8
def f0x23(self):
    self.l += 1
    if self.l >= 0x100:
        self.l %= 0x100; self.h += 1
        if self.h >= 0x100: self.h %= 0x100
    return 1,8
def f0x24(self): self.sub = 0; self.halfcarry = 1 if ((self.h&0xf) + 1)&0x10 else 0; self.h += 1; self.h %= 0x100; self.zero = 0 if self.h else 1; return 1,4
def f0x25(self): self.sub = 1; self.halfcarry = 1 if ((self.h&0xf) - 1)&0x10 else 0; self.h -= 1; self.h %= 0x100; self.zero = 0 if self.h else 1; return 1,4
def f0x26(self): self.h = self.mem[self.pc+1]; return 2,8
def f0x27(self): input("DAA"); return 1,4 # TODO: DAA
def f0x28(self):
    if not self.zero: return 2,8
    jump = self.mem[self.pc+1]
    if jump >= 0x80: jump -= 0x100
    return 2+jump,12
def f0x29(self): self.sub = 0; self.l += self.l; self.carry = 1 if self.l >= 0x100 else 0; self.l %= 0x100; self.halfcarry = 1 if ((self.h&0xf) + self.h+self.carry)&0x10 else 0; self.h += self.h + self.carry; self.carry = 1 if self.h >= 0x100 else 0; self.h %= 0x100; return 1,8
def f0x2a(self):
    self.a = self.mem[(self.h<<8)+self.l]; self.l += 1
    if self.l == 0x100: self.l = 0; self.h += 1; self.h %= 0x100
    return 1,8
def f0x2b(self):
    self.l -= 1
    if self.l < 0:
        self.l = 0xff; self.h -= 1
        if self.h < 0: self.h = 0xff
    return 1,8
def f0x2c(self): self.sub = 0; self.halfcarry = 1 if ((self.l&0xf) + 1)&0x10 else 0; self.l += 1; self.l %= 0x100; self.zero = 0 if self.l else 1; return 1,4
def f0x2d(self): self.sub = 1; self.halfcarry = 1 if ((self.l&0xf) - 1)&0x10 else 0; self.l -= 1; self.l %= 0x100; self.zero = 0 if self.l else 1; return 1,4
def f0x2e(self): self.l = self.mem[self.pc+1]; return 2,8
def f0x2f(self): self.a = 0xff-self.a; self.sub = 1; self.halfcarry = 1; return 1,4
# </editor-fold>
# <editor-fold desc="3X">
def f0x30(self):
    if self.carry: return 2,8
    jump = self.mem[self.pc+1]
    if jump >= 0x80: jump -= 0x100
    return 2+jump,12
def f0x31(self): self.sp = (self.mem[self.pc+2]<<8) + self.mem[self.pc+1]; return 3,12
def f0x32(self):
    self.mem[(self.h<<8)+self.l] = self.a; self.l -= 1
    if self.l < 0: self.l = 0xff; self.h -= 1; self.h %= 0x100
    return 1,8
def f0x33(self): self.sp += 1; self.sp %= 0x10000; return 1,8
def f0x34(self): self.sub = 0; val = self.mem[self.h*0x100+self.l]; self.halfcarry = 1 if ((val&0xf) + 1)&0x10 else 0; val += 1; val %= 0x100; self.zero = 0 if val else 1; self.mem[self.h*0x100+self.l] = val; return 1,4
def f0x35(self): self.sub = 1; val = self.mem[self.h*0x100+self.l]; self.halfcarry = 1 if ((val&0xf) - 1)&0x10 else 0; val -= 1; val %= 0x100; self.zero = 0 if val else 1; self.mem[self.h*0x100+self.l] = val; return 1,4
def f0x36(self): self.mem[(self.h<<8)+self.l] = self.mem[self.pc+1]; return 2,12
def f0x37(self): self.sub = 0; self.halfcarry = 0; self.carry = 1; return 1,4
def f0x38(self):
    if not self.carry: return 2,8
    jump = self.mem[self.pc+1]
    if jump >= 0x80: jump -= 0x100
    return 2+jump,12
def f0x39(self): s=self.sp//0x100; p=self.sp%0x100; self.sub = 0; self.l += p; self.carry = 1 if self.l >= 0x100 else 0; self.l %= 0x100; self.halfcarry = 1 if ((self.h&0xf) + s+self.carry)&0x10 else 0; self.h += s + self.carry; self.carry = 1 if self.h >= 0x100 else 0; self.h %= 0x100; return 1,8
def f0x3a(self):
    self.a = self.mem[(self.h<<8)+self.l]; self.l -= 1
    if self.l < 0: self.l = 0xff; self.h -= 1; self.h %= 0x100
    return 1,8
def f0x3b(self): self.sp -= 1; self.sp %= 0x10000; return 1,8
def f0x3c(self): self.sub = 0; self.halfcarry = 1 if ((self.a&0xf) + 1)&0x10 else 0; self.a += 1; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x3d(self): self.sub = 1; self.halfcarry = 1 if ((self.a&0xf) - 1)&0x10 else 0; self.a -= 1; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x3e(self): self.a = self.mem[self.pc+1]; return 2,8
def f0x3f(self): self.sub = 0; self.halfcarry = 0; self.carry = 0 if self.carry else 1; return 1,4
# </editor-fold>
# <editor-fold desc="LOADS">
def f0x40(self): return 1,4
def f0x41(self): self.b = self.c; return 1,4
def f0x42(self): self.b = self.d; return 1,4
def f0x43(self): self.b = self.e; return 1,4
def f0x44(self): self.b = self.h; return 1,4
def f0x45(self): self.b = self.l; return 1,4
def f0x46(self): self.b = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x47(self): self.b = self.a; return 1,4
def f0x48(self): self.c = self.b; return 1,4
def f0x49(self): return 1,4
def f0x4a(self): self.c = self.d; return 1,4
def f0x4b(self): self.c = self.e; return 1,4
def f0x4c(self): self.c = self.h; return 1,4
def f0x4d(self): self.c = self.l; return 1,4
def f0x4e(self): self.c = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x4f(self): self.c = self.a; return 1,4
def f0x50(self): self.d = self.b; return 1,4
def f0x51(self): self.d = self.c; return 1,4
def f0x52(self): return 1,4
def f0x53(self): self.d = self.e; return 1,4
def f0x54(self): self.d = self.h; return 1,4
def f0x55(self): self.d = self.l; return 1,4
def f0x56(self): self.d = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x57(self): self.d = self.a; return 1,4
def f0x58(self): self.e = self.b; return 1,4
def f0x59(self): self.e = self.c; return 1,4
def f0x5a(self): self.e = self.d; return 1,4
def f0x5b(self): return 1,4
def f0x5c(self): self.e = self.h; return 1,4
def f0x5d(self): self.e = self.l; return 1,4
def f0x5e(self): self.e = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x5f(self): self.e = self.a; return 1,4
def f0x60(self): self.h = self.b; return 1,4
def f0x61(self): self.h = self.c; return 1,4
def f0x62(self): self.h = self.d; return 1,4
def f0x63(self): self.h = self.e; return 1,4
def f0x64(self): return 1,4
def f0x65(self): self.h = self.l; return 1,4
def f0x66(self): self.h = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x67(self): self.h = self.a; return 1,4
def f0x68(self): self.l = self.b; return 1,4
def f0x69(self): self.l = self.c; return 1,4
def f0x6a(self): self.l = self.d; return 1,4
def f0x6b(self): self.l = self.e; return 1,4
def f0x6c(self): self.l = self.h; return 1,4
def f0x6d(self): return 1,4
def f0x6e(self): self.l = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x6f(self): self.l = self.a; return 1,4
def f0x70(self): self.mem[(self.h<<8)+self.l] = self.b; return 1,8
def f0x71(self): self.mem[(self.h<<8)+self.l] = self.c; return 1,8
def f0x72(self): self.mem[(self.h<<8)+self.l] = self.d; return 1,8
def f0x73(self): self.mem[(self.h<<8)+self.l] = self.e; return 1,8
def f0x74(self): self.mem[(self.h<<8)+self.l] = self.h; return 1,8
def f0x75(self): self.mem[(self.h<<8)+self.l] = self.l; return 1,8
def f0x76(self): input("HALT"); return 1,4 # TODO: HALT
def f0x77(self): self.mem[(self.h<<8)+self.l] = self.a; return 1,8
def f0x78(self): self.a = self.b; return 1,4
def f0x79(self): self.a = self.c; return 1,4
def f0x7a(self): self.a = self.d; return 1,4
def f0x7b(self): self.a = self.e; return 1,4
def f0x7c(self): self.a = self.h; return 1,4
def f0x7d(self): self.a = self.l; return 1,4
def f0x7e(self): self.a = self.mem[(self.h<<8)+self.l]; return 1,8
def f0x7f(self): return 1,4
# </editor-fold>
# <editor-fold desc="Operations">
def f0x80(self): self.halfcarry = 1 if ((self.a&0xf)+(self.b&0xf))&0x10 else 0; self.sub = 0; self.a += self.b; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x81(self): self.halfcarry = 1 if ((self.a&0xf)+(self.c&0xf))&0x10 else 0; self.sub = 0; self.a += self.c; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x82(self): self.halfcarry = 1 if ((self.a&0xf)+(self.d&0xf))&0x10 else 0; self.sub = 0; self.a += self.d; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x83(self): self.halfcarry = 1 if ((self.a&0xf)+(self.e&0xf))&0x10 else 0; self.sub = 0; self.a += self.e; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x84(self): self.halfcarry = 1 if ((self.a&0xf)+(self.h&0xf))&0x10 else 0; self.sub = 0; self.a += self.h; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x85(self): self.halfcarry = 1 if ((self.a&0xf)+(self.l&0xf))&0x10 else 0; self.sub = 0; self.a += self.l; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x86(self): val = self.mem[(self.h<<8)+self.l]; self.halfcarry = 1 if ((self.a&0xf)+(val&0xf))&0x10 else 0; self.sub = 0; self.a += val; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,8
def f0x87(self): self.halfcarry = 1 if ((self.a&0xf)+(self.a&0xf))&0x10 else 0; self.sub = 0; self.a += self.a; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x88(self): self.halfcarry = 1 if ((self.a&0xf)+((self.b+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.b+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x89(self): self.halfcarry = 1 if ((self.a&0xf)+((self.c+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.c+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x8a(self): self.halfcarry = 1 if ((self.a&0xf)+((self.d+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.d+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x8b(self): self.halfcarry = 1 if ((self.a&0xf)+((self.e+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.e+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x8c(self): self.halfcarry = 1 if ((self.a&0xf)+((self.h+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.h+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x8d(self): self.halfcarry = 1 if ((self.a&0xf)+((self.l+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.l+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x8e(self): val = self.mem[(self.h<<8)+self.l]; self.halfcarry = 1 if ((self.a&0xf)+((val+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += val+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,8
def f0x8f(self): self.halfcarry = 1 if ((self.a&0xf)+((self.a+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += self.a+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x90(self): self.halfcarry = 1 if ((self.a&0xf)-(self.b&0xf))&0x10 else 0; self.sub = 1; self.a -= self.b; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x91(self): self.halfcarry = 1 if ((self.a&0xf)-(self.c&0xf))&0x10 else 0; self.sub = 1; self.a -= self.c; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x92(self): self.halfcarry = 1 if ((self.a&0xf)-(self.d&0xf))&0x10 else 0; self.sub = 1; self.a -= self.d; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x93(self): self.halfcarry = 1 if ((self.a&0xf)-(self.e&0xf))&0x10 else 0; self.sub = 1; self.a -= self.e; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x94(self): self.halfcarry = 1 if ((self.a&0xf)-(self.h&0xf))&0x10 else 0; self.sub = 1; self.a -= self.h; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x95(self): self.halfcarry = 1 if ((self.a&0xf)-(self.l&0xf))&0x10 else 0; self.sub = 1; self.a -= self.l; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x96(self): val = self.mem[(self.h<<8)+self.l]; self.halfcarry = 1 if ((self.a&0xf)-(val&0xf))&0x10 else 0; self.sub = 1; self.a -= val; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,8
def f0x97(self): self.halfcarry = 1 if ((self.a&0xf)-(self.a&0xf))&0x10 else 0; self.sub = 1; self.a -= self.a; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x98(self): self.halfcarry = 1 if ((self.a&0xf)-((self.b+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.b+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x99(self): self.halfcarry = 1 if ((self.a&0xf)-((self.c+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.c+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x9a(self): self.halfcarry = 1 if ((self.a&0xf)-((self.d+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.d+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x9b(self): self.halfcarry = 1 if ((self.a&0xf)-((self.e+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.e+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x9c(self): self.halfcarry = 1 if ((self.a&0xf)-((self.h+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.h+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x9d(self): self.halfcarry = 1 if ((self.a&0xf)-((self.l+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.l+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0x9e(self): val = self.mem[(self.h<<8)+self.l]; self.halfcarry = 1 if ((self.a&0xf)-((val+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (val+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,8
def f0x9f(self): self.halfcarry = 1 if ((self.a&0xf)-((self.a+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (self.a+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 1,4
def f0xa0(self): self.a &= self.b; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa1(self): self.a &= self.c; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa2(self): self.a &= self.d; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa3(self): self.a &= self.e; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa4(self): self.a &= self.h; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa5(self): self.a &= self.l; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa6(self): self.a &= self.mem[(self.h<<8)+self.l]; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,8
def f0xa7(self): self.a &= self.a; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 1,4
def f0xa8(self): self.a ^= self.b; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xa9(self): self.a ^= self.c; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xaa(self): self.a ^= self.d; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xab(self): self.a ^= self.e; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xac(self): self.a ^= self.h; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xad(self): self.a ^= self.l; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xae(self): self.a ^= self.mem[(self.h<<8)+self.l]; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,8
def f0xaf(self): self.a ^= self.a; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb0(self): self.a |= self.b; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb1(self): self.a |= self.c; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb2(self): self.a |= self.d; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb3(self): self.a |= self.e; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb4(self): self.a |= self.h; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb5(self): self.a |= self.l; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb6(self): self.a |= self.mem[(self.h<<8)+self.l]; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,8
def f0xb7(self): self.a |= self.a; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 1,4
def f0xb8(self): self.halfcarry = 1 if ((self.a&0xf)-(self.b&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.b < 0 else 0; self.zero = 0 if self.a-self.b else 1; return 1,4
def f0xb9(self): self.halfcarry = 1 if ((self.a&0xf)-(self.c&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.c < 0 else 0; self.zero = 0 if self.a-self.c else 1; return 1,4
def f0xba(self): self.halfcarry = 1 if ((self.a&0xf)-(self.d&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.d < 0 else 0; self.zero = 0 if self.a-self.d else 1; return 1,4
def f0xbb(self): self.halfcarry = 1 if ((self.a&0xf)-(self.e&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.e < 0 else 0; self.zero = 0 if self.a-self.e else 1; return 1,4
def f0xbc(self): self.halfcarry = 1 if ((self.a&0xf)-(self.h&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.h < 0 else 0; self.zero = 0 if self.a-self.h else 1; return 1,4
def f0xbd(self): self.halfcarry = 1 if ((self.a&0xf)-(self.l&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.l < 0 else 0; self.zero = 0 if self.a-self.l else 1; return 1,4
def f0xbe(self): val = self.mem[(self.h<<8)+self.l]; self.halfcarry = 1 if ((self.a&0xf)-(val&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-val < 0 else 0; self.zero = 0 if self.a-val else 1; return 1,8
def f0xbf(self): self.halfcarry = 1 if ((self.a&0xf)-(self.a&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-self.a < 0 else 0; self.zero = 0 if self.a-self.a else 1; return 1,4
# </editor-fold>
# <editor-fold desc="CX">
def f0xc0(self):
    if self.zero: return 1,8
    self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp];self.sp += 2; return 0,20
def f0xc1(self): self.c = self.mem[self.sp]; self.b = self.mem[self.sp+1]; self.sp += 2; return 1,12
def f0xc2(self):
    if self.zero: return 3,12
    self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]; return 0,16
def f0xc3(self):
    self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]; return 0,16
def f0xc4(self):
    if self.zero: return 3,12
    pc = (self.pc + 3) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]; return 0,24
def f0xc5(self): self.mem[self.sp-1] = self.b; self.mem[self.sp-2] = self.c; self.sp -= 2; return 1,16
def f0xc6(self): val = self.mem[self.pc+1]; self.halfcarry = 1 if ((self.a & 0xf) + (val & 0xf)) & 0x10 else 0; self.sub = 0; self.a += val; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 2, 8
def f0xc7(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x0; return 0,16
def f0xc8(self):
    if not self.zero: return 1,8
    self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp];self.sp += 2; return 0,20
def f0xc9(self): self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp];self.sp += 2; return 0,16
def f0xca(self):
    if not self.zero: return 3,12
    self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]; return 0,16
def f0xcb(self): return self.CB(self.mem[self.pc+1])
def f0xcc(self):
    if not self.zero: return 3,12
    pc = (self.pc + 3) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]; return 0,24
def f0xcd(self):
    pc = (self.pc + 3) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]; return 0,24
def f0xce(self): val = self.mem[self.pc+1]; self.halfcarry = 1 if ((self.a&0xf)+((val+self.carry)&0xf))&0x10 else 0; self.sub = 0; self.a += val+self.carry; self.carry = 1 if self.a >= 0x100 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 2,8
def f0xcf(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x8; return 0,16
# </editor-fold>
# <editor-fold desc="DX">
def f0xd0(self):
    if self.carry: return 1,8
    self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp];self.sp += 2; return 0,20
def f0xd1(self): self.e = self.mem[self.sp]; self.d = self.mem[self.sp+1]; self.sp += 2; return 1,12
def f0xd2(self):
    if self.carry: return 3,12
    self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]; return 0,16
def f0xd4(self):
    if self.carry: return 3,12
    pc = (self.pc + 3) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]; return 0,24
def f0xd5(self): self.mem[self.sp-1] = self.d; self.mem[self.sp-2] = self.e; self.sp -= 2; return 1,16
def f0xd6(self): val = self.mem[self.pc+1]; self.halfcarry = 1 if ((self.a&0xf)-(val&0xf))&0x10 else 0; self.sub = 1; self.a -= val; self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 2,8
def f0xd7(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x10; return 0,16
def f0xd8(self):
    if not self.carry: return 1,8
    self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp];self.sp += 2; return 0,20
def f0xd9(self): self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp];self.sp += 2; self.interruptsEnabled=1; return 0,16
def f0xda(self):
    if not self.carry: return 3,12
    self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]; return 0,16
def f0xdc(self):
    if not self.carry: return 3,12
    pc = (self.pc + 3) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]; return 0,24
def f0xde(self): val = self.mem[self.pc+1]; self.halfcarry = 1 if ((self.a&0xf)-((val+self.carry)&0xf))&0x10 else 0; self.sub = 1; self.a -= (val+self.carry); self.carry = 1 if self.a < 0 else 0; self.a %= 0x100; self.zero = 0 if self.a else 1; return 2,8
def f0xdf(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x18; return 0,16
# </editor-fold>
# <editor-fold desc="EX">
def f0xe0(self): self.mem[self.mem[self.pc+1]+0xff00] = self.a; return 2,12
def f0xe1(self): self.l = self.mem[self.sp]; self.h = self.mem[self.sp+1]; self.sp += 2; return 1,12
def f0xe2(self): self.mem[self.c+0xff00] = self.a; return 1,8
def f0xe5(self): self.mem[self.sp-1] = self.h; self.mem[self.sp-2] = self.l; self.sp -= 2; return 1,16
def f0xe6(self): self.a &= self.mem[self.pc+1]; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 1; self.carry = 0; return 2,8
def f0xe7(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x20; return 0,16
def f0xe8(self):
    val = self.mem[self.pc+1]
    if val >= 0x80: val -= 0x100
    self.halfcarry = 1 if ((self.sp&0xfff)+(val&0xfff))&0x1000 else 0; self.zero = 0; self.sub = 0; self.sp += val; self.carry = 1 if self.sp >= 0x10000 else 0; self.sp %= 0x10000; return 2,16
def f0xe9(self): self.pc = (self.h<<8) + self.l; return 0,4
def f0xea(self): self.mem[self.mem[self.pc+2]*256+self.mem[self.pc+1]] = self.a; return 3,16
def f0xee(self): self.a ^= self.mem[self.pc+1]; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 2,8
def f0xef(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x28; return 0,16
# </editor-fold>
# <editor-fold desc="FX">
def f0xf0(self): self.a = self.mem[self.mem[self.pc+1]+0xff00]; return 2,12
def f0xf1(self): flags = self.mem[self.sp]; self.zero = flags>>7; self.sub = (flags>>6)%2; self.halfcarry = (flags>>5)%2; self.carry = (flags>>4)%2; self.a = self.mem[self.sp+1]; self.sp += 2; return 1,12
def f0xf2(self): self.a = self.mem[self.c+0xff00]; return 1,8
def f0xf3(self): self.interruptsEnabled = 0; return 1,4
def f0xf5(self): self.mem[self.sp-1] = self.a; flags = self.zero*128 + self.sub*64 + self.halfcarry*32 + self.carry*16; self.mem[self.sp-2] = flags; self.sp -= 2; return 1,16
def f0xf6(self): self.a |= self.mem[self.pc+1]; self.zero = 0 if self.a else 1; self.sub = 0; self.halfcarry = 0; self.carry = 0; return 2,8
def f0xf7(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x30; return 0,16
def f0xf8(self):
    val = self.mem[self.pc+1]; sp = self.sp
    if val >= 0x80: val -= 0x100
    self.halfcarry = 1 if ((sp&0xfff)+(val&0xfff))&0x1000 else 0; self.zero = 0; self.sub = 0; sp += val; self.carry = 1 if sp >= 0x10000 else 0; sp %= 0x10000; self.h = sp//256; self.l = sp%256; return 2,12
def f0xf9(self): self.sp = self.h*256 + self.l; return 1,8
def f0xfa(self): self.a = self.mem[self.mem[self.pc+2]*256+self.mem[self.pc+1]]; return 3,16
def f0xfb(self): self.enableNext = 1; return 1,4
def f0xfe(self): val = self.mem[self.pc+1]; self.halfcarry = 1 if ((self.a&0xf)-(val&0xf))&0x10 else 0; self.sub = 1; self.carry = 1 if self.a-val < 0 else 0; self.zero = 0 if self.a-val else 1; return 2,8
def f0xff(self): pc = (self.pc + 1) % 0x10000; self.mem[self.sp-1] = pc//0x100; self.mem[self.sp-2] = pc%0x100; self.sp -= 2; self.pc = 0x38; return 0,16
# </editor-fold>

def ERR(self): input("ILLEGAL OPCODE: %s" % self.mem[self.pc])

OPS = (f0x00,f0x01,f0x02,f0x03,f0x04,f0x05,f0x06,f0x07,f0x08,f0x09,f0x0a,f0x0b,f0x0c,f0x0d,f0x0e,f0x0f,f0x10,f0x11,f0x12,f0x13,f0x14,f0x15,f0x16,f0x17,f0x18,f0x19,f0x1a,f0x1b,f0x1c,f0x1d,f0x1e,f0x1f,f0x20,f0x21,f0x22,f0x23,f0x24,f0x25,f0x26,f0x27,f0x28,f0x29,f0x2a,f0x2b,f0x2c,f0x2d,f0x2e,f0x2f,f0x30,f0x31,f0x32,f0x33,f0x34,f0x35,f0x36,f0x37,f0x38,f0x39,f0x3a,f0x3b,f0x3c,f0x3d,f0x3e,f0x3f,f0x40,f0x41,f0x42,f0x43,f0x44,f0x45,f0x46,f0x47,f0x48,f0x49,f0x4a,f0x4b,f0x4c,f0x4d,f0x4e,f0x4f,f0x50,f0x51,f0x52,f0x53,f0x54,f0x55,f0x56,f0x57,f0x58,f0x59,f0x5a,f0x5b,f0x5c,f0x5d,f0x5e,f0x5f,f0x60,f0x61,f0x62,f0x63,f0x64,f0x65,f0x66,f0x67,f0x68,f0x69,f0x6a,f0x6b,f0x6c,f0x6d,f0x6e,f0x6f,f0x70,f0x71,f0x72,f0x73,f0x74,f0x75,f0x76,f0x77,f0x78,f0x79,f0x7a,f0x7b,f0x7c,f0x7d,f0x7e,f0x7f,f0x80,f0x81,f0x82,f0x83,f0x84,f0x85,f0x86,f0x87,f0x88,f0x89,f0x8a,f0x8b,f0x8c,f0x8d,f0x8e,f0x8f,f0x90,f0x91,f0x92,f0x93,f0x94,f0x95,f0x96,f0x97,f0x98,f0x99,f0x9a,f0x9b,f0x9c,f0x9d,f0x9e,f0x9f,f0xa0,f0xa1,f0xa2,f0xa3,f0xa4,f0xa5,f0xa6,f0xa7,f0xa8,f0xa9,f0xaa,f0xab,f0xac,f0xad,f0xae,f0xaf,f0xb0,f0xb1,f0xb2,f0xb3,f0xb4,f0xb5,f0xb6,f0xb7,f0xb8,f0xb9,f0xba,f0xbb,f0xbc,f0xbd,f0xbe,f0xbf,f0xc0,f0xc1,f0xc2,f0xc3,f0xc4,f0xc5,f0xc6,f0xc7,f0xc8,f0xc9,f0xca,f0xcb,f0xcc,f0xcd,f0xce,f0xcf,f0xd0,f0xd1,f0xd2,ERR,f0xd4,f0xd5,f0xd6,f0xd7,f0xd8,f0xd9,f0xda,ERR,f0xdc,ERR,f0xde,f0xdf,f0xe0,f0xe1,f0xe2,ERR,ERR,f0xe5,f0xe6,f0xe7,f0xe8,f0xe9,f0xea,ERR,ERR,ERR,f0xee,f0xef,f0xf0,f0xf1,f0xf2,f0xf3,ERR,f0xf5,f0xf6,f0xf7,f0xf8,f0xf9,f0xfa,f0xfb,ERR,ERR,f0xfe,f0xff)


class CPU:

    def __init__(self, mem):
        self.mem = mem
        self.b,self.c,self.d,self.e,self.h,self.l,self.a,self.pc,self.sp = 0,0,0,0,0,0,0,0,0
        self.zero,self.sub,self.halfcarry,self.carry = 0,0,0,0
        self.halted,self.interruptsEnabled,self.enableNext = 0,1,0

    def cycle(self):
        if self.enableNext:
            self.interruptsEnabled = 1
            self.enableNext = False
        j,c = OPS[self.mem[self.pc]](self)
        self.pc += j
        if self.interruptsEnabled:
            interrupts = self.mem[IF] & self.mem[IE]
            if interrupts:
                self.interruptsEnabled = 0
                checker = 1
                if interrupts & checker:
                    self.mem[self.sp-1] = self.pc//256
                    self.mem[self.sp-2] = self.pc%256
                    self.sp -= 2
                    self.pc = VBLANK
                elif (interrupts>>1)& checker:
                    self.mem[IF] &= 0b11111101
                    self.interruptsEnabled = 0
                    self.mem[self.sp-1] = self.pc//256
                    self.mem[self.sp-2] = self.pc%256
                    self.sp -= 2
                    self.pc = LCDSTATUS
                elif (interrupts>>2)& checker:
                    self.mem[IF] &= 0b11111011
                    self.interruptsEnabled = 0
                    self.mem[self.sp-1] = self.pc//256
                    self.mem[self.sp-2] = self.pc%256
                    self.sp -= 2
                    self.pc = TIMER
                elif (interrupts>>3)& checker:
                    self.mem[IF] &= 0b11110111
                    self.interruptsEnabled = 0
                    self.mem[self.sp-1] = self.pc//256
                    self.mem[self.sp-2] = self.pc%256
                    self.sp -= 2
                    self.pc = SERIAL
                elif (interrupts>>4)& checker:
                    self.mem[IF] &= 0b11101111
                    self.interruptsEnabled = 0
                    self.mem[self.sp-1] = self.pc//256
                    self.mem[self.sp-2] = self.pc%256
                    self.sp -= 2
                    self.pc = JOYPAD
        return c

    def bitop(self, reg, level, func):
        if reg < 4:
            if reg < 2:
                if not reg:
                    self.b = func(self.b, level)
                else:
                    self.c = func(self.c, level)
            else:
                if reg == 2:
                    self.d = func(self.d, level)
                else:
                    self.e = func(self.e, level)
        else:
            if reg < 6:
                if reg == 4:
                    self.h = func(self.h, level)
                else:
                    self.l = func(self.l, level)
            else:
                if reg == 6:
                    self.mem[self.h*0x100+self.l] = func(self.mem[self.h*0x100+self.l], level)
                    return 16
                else:
                    self.a = func(self.a, level)
        return 8

    def test(self, val, bit):
        self.zero = 0 if (val>>bit)%2 else 1
        self.sub = 0
        self.halfcarry = 1
        return val

    def set(self, val, bit):
        return val|(2**bit)

    def reset(self, val, bit):
        return val&(0xff-(2**bit))

    def rotate(self, val, bit):
        if bit < 4:
            if bit < 2:
                if not bit: # RLC
                    val <<= 1
                    if val > 0xff:
                        val -= 0x100
                        val += 1
                        self.carry = 1
                    else: self.carry = 0
                else: # RRA
                    if val % 2 == 1:
                        self.carry = 1
                        val += 0x100
                    else: self.carry = 0
                    val >>= 1
            else:
                if bit == 2: # RL
                    val <<= 1
                    val += self.carry
                    if val > 0xff:
                        val -= 0x100
                        self.carry = 1
                    else: self.carry = 0
                else: # RR
                    val += self.carry*0x100
                    if val%2 == 1: self.carry = 1
                    else: self.carry = 0
                    val >>= 1
        else:
            if bit < 6:
                if bit == 4: # SLA
                    val <<= 1
                    if val >= 0x100:
                        val -= 0x100
                        self.carry = 1
                    else: self.carry = 0
                else: # SRA
                    self.carry = val%2
                    if val >= 0x80:
                        val += 256
                    val >>= 1
            else:
                if bit == 6: # SWAP
                    low = val>>4
                    val = (val&0xff)<<4 + low
                    self.carry = 0
                else: # SRL
                    self.carry = val%2
                    val >>= 1
        self.sub = 0
        self.halfcarry = 0
        self.zero = 0 if val else 1
        return val

    def CB(self, byte):
        """
        Due to the infrequency of CB operations I feel justified in minimizing the table at the cost of performance
        :param byte:
        :return:
        """
        op = byte>>6
        level = (byte>>3)&0b111
        reg = byte&0b111

        if op < 0b10:
            if not op: # Rotations
                c = self.bitop(reg, level, self.rotate)
            else: # Tests
                c = self.bitop(reg, level, self.test)
        else:
            if op == 0b10: # Resets
                c = self.bitop(reg, level, self.reset)
            else: # Sets
                c = self.bitop(reg, level, self.set)
        return 2,c
