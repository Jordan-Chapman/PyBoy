# Author: Jordan Chapman
# Heheh, why not
# CPU that ignores all principles of good coding in exchange for the large performance increase
# This CPU is able to reach 70 FPS on an Intel I5 8th gen at 4.1ghz boost speed
#   Note: this test was performed without sprite functionality

from consts import *

class CPU:
    def __init__(self, mem):
        self.mem = mem
        self.b,self.c,self.d,self.e,self.h,self.l,self.a,self.pc,self.sp = 0,0,0,0,0,0,0,0,0
        self.zero = 0
        self.sub = 0
        self.halfcarry = 0
        self.carry = 0

        self.halted = 0
        self.interruptsEnabled = 1
        self.enableNext = False # Enable interrupts next frame

    def cycle(self):
        if self.enableNext:
            self.interruptsEnabled = 1
            self.enableNext = False
        byte = self.mem[self.pc]
        j,c = self.exe(byte)
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

    def exe(self, byte):
        """
        Not meant to be readable to humans
        Binary tree style opcode search for optimal efficiency
        :return: Number of bytes used, Number of cycles used
        """
        #print(hex(byte),hex(self.pc))
        if byte < 0x80:
            if byte < 0x40:
### SECTION 0
                if byte < 0x20:
                    if byte < 0x10:
                        if byte < 0x8:
                            if byte < 0x4:
                                if byte < 0x2:
                                    if not byte: return 1,4 # NOP
                                    else: # LD BC,d16
                                        self.b = self.mem[self.pc+2]
                                        self.c = self.mem[self.pc+1]
                                        return 3,12
                                else:
                                    if byte == 0x2: # LD (BC), A
                                        self.mem[self.b*0x100+self.c] = self.a
                                        return 1,8
                                    else: # INC BC
                                        self.c += 1
                                        if self.c >= 0x100:
                                            self.c %= 0x100
                                            self.b += 1
                                            if self.b >= 0x100: self.b %= 0x100
                                        return 1,8
                            else:
                                if byte < 0x6:
                                    if byte == 0x4: # INC B
                                        self.sub = 0
                                        if ((self.b&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.b += 1
                                        self.b %= 0x100
                                        self.zero = 0 if self.b else 1
                                        return 1,4
                                    else: # DEC B
                                        self.sub = 1
                                        if ((self.b&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.b -= 1
                                        self.b %= 0x100
                                        self.zero = 0 if self.b else 1
                                        return 1,4
                                else:
                                    if byte == 0x6: # LD B,d8
                                        self.b = self.mem[self.pc+1]
                                        return 2,8
                                    else: # RLCA
                                        self.zero = 0
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.a <<= 1
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.a += 1
                                            self.carry = 1
                                        else: self.carry = 0
                                        return 1,4
                        else:
                            if byte < 0xc:
                                if byte < 0xa:
                                    if byte == 0x8: # LD (a16),SP
                                        self.sp = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 3,20
                                    else: # ADD HL,BC
                                        self.sub = 0
                                        self.l += self.c
                                        if self.l > 0xff:
                                            self.l -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        if ((self.h&0xf) + self.b+self.carry)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.h += self.b + self.carry
                                        if self.h > 0xff:
                                            self.h -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        return 1,8
                                else:
                                    if byte == 0xa: # LD A,(BC)
                                        self.a = self.mem[self.b*0x100+self.c]
                                        return 1,8
                                    else: # DEC BC
                                        self.c -= 1
                                        if self.c < 0:
                                            self.c = 0xff
                                            self.b -= 1
                                            if self.b < 0: self.b = 0xff
                                        return 1,8
                            else:
                                if byte < 0xe:
                                    if byte == 0xc: # INC C
                                        self.sub = 0
                                        if ((self.c&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.c += 1
                                        self.c %= 0x100
                                        self.zero = 0 if self.c else 1
                                        return 1,4
                                    else: # DEC C
                                        self.sub = 1
                                        if ((self.c&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.c -= 1
                                        self.c %= 0x100
                                        self.zero = 0 if self.c else 1
                                        return 1,4
                                else:
                                    if byte == 0xe: # LD C,d8
                                        self.c = self.mem[self.pc+1]
                                        return 2,8
                                    else: # RRCA
                                        self.zero = 0
                                        self.sub = 0
                                        self.halfcarry = 0
                                        if self.a%2 == 1:
                                            self.carry = 1
                                            self.a += 0x100
                                        else:
                                            self.carry = 0
                                        self.a >>= 1
                                        return 1,4
### SECTION 1
                    else:
                        if byte < 0x18:
                            if byte < 0x14:
                                if byte < 0x12:
                                    if byte == 0x10: # STOP
                                        input("STOP")
                                        # TODO: STOP
                                        return 2,4
                                    else: # LD DE,d16
                                        self.d = self.mem[self.pc+2]
                                        self.e = self.mem[self.pc+1]
                                        return 3,12
                                else:
                                    if byte == 0x12: # LD (DE),A
                                        self.mem[self.d*0x100+self.e] = self.a
                                        return 1,8
                                    else: # INC DE
                                        self.e += 1
                                        if self.e >= 0x100:
                                            self.e %= 0x100
                                            self.d += 1
                                            if self.d >= 0x100: self.d %= 0x100
                                        return 1,8
                            else:
                                if byte < 0x16:
                                    if byte == 0x14: # INC D
                                        self.sub = 0
                                        if ((self.d&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.d += 1
                                        self.d %= 0x100
                                        self.zero = 0 if self.d else 1
                                        return 1,4
                                    else: # DEC D
                                        self.sub = 1
                                        if ((self.d&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.d -= 1
                                        self.d %= 0x100
                                        self.zero = 0 if self.d else 1
                                        return 1,4
                                else:
                                    if byte == 0x16: # LD D,d8
                                        self.d = self.mem[self.pc+1]
                                        return 2,8
                                    else: # RLA
                                        self.zero = 0
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.a <<= 1
                                        self.a += self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        return 1,4
                        else:
                            if byte < 0x1c:
                                if byte < 0x1a:
                                    if byte == 0x18: # JR r8
                                        jump = self.mem[self.pc+1]
                                        if jump >= 0x80: jump -= 0x100
                                        return 2+jump,12
                                    else: # ADD HL,DE
                                        self.sub = 0
                                        self.l += self.e
                                        if self.l > 0xff:
                                            self.l -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        if ((self.h&0xf) + self.d+self.carry)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.h += self.d + self.carry
                                        if self.h > 0xff:
                                            self.h -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        return 1,8
                                else:
                                    if byte == 0x1a: # LD A,(DE)
                                        self.a = self.mem[self.d*0x100+self.e]
                                        return 1,8
                                    else: # DEC DE
                                        self.e -= 1
                                        if self.e < 0:
                                            self.e = 0xff
                                            self.d -= 1
                                            if self.d < 0: self.d = 0xff
                                        return 1,8
                            else:
                                if byte < 0x1e:
                                    if byte == 0x1c: # INC E
                                        self.sub = 0
                                        if ((self.e&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.e += 1
                                        self.e %= 0x100
                                        self.zero = 0 if self.e else 1
                                        return 1,4
                                    else: # DEC E
                                        self.sub = 1
                                        if ((self.e&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.e -= 1
                                        self.e %= 0x100
                                        self.zero = 0 if self.e else 1
                                        return 1,4
                                else:
                                    if byte == 0x1e: # LD E,d8
                                        self.e = self.mem[self.pc+1]
                                        return 2,8
                                    else: # RRA
                                        self.zero = 0
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.a += self.carry*0x100
                                        if self.a%2 == 1:
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        self.a >>= 1
                                        return 1,4
### SECTION 2
                else:
                    if byte < 0x30:
                        if byte < 0x28:
                            if byte < 0x24:
                                if byte < 0x22:
                                    if byte == 0x20: # JR NZ,r8
                                        if self.zero: return 2,8
                                        jump = self.mem[self.pc+1]
                                        if jump >= 0x80: jump -= 0x100
                                        return 2+jump,12
                                    else: # LD HL,d16
                                        self.h = self.mem[self.pc+2]
                                        self.l = self.mem[self.pc+1]
                                        return 3,12
                                else:
                                    if byte == 0x22: # LD (HL+),A
                                        self.mem[self.h*0x100+self.l] = self.a
                                        self.l += 1
                                        if self.l > 0xff:
                                            self.l = 0
                                            self.h += 1
                                            if self.h > 0xff: self.h = 0
                                        return 1,8
                                    else: # INC HL
                                        self.l += 1
                                        if self.l >= 0x100:
                                            self.l %= 0x100
                                            self.h += 1
                                            if self.h >= 0x100: self.h %= 0x100
                                        return 1,8
                            else:
                                if byte < 0x26:
                                    if byte == 0x24: # INC H
                                        self.sub = 0
                                        if ((self.h&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.h += 1
                                        self.h %= 0x100
                                        self.zero = 0 if self.h else 1
                                        return 1,4
                                    else: # DEC H
                                        self.sub = 1
                                        if ((self.h&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.h -= 1
                                        self.h %= 0x100
                                        self.zero = 0 if self.h else 1
                                        return 1,4
                                else:
                                    if byte == 0x26: # LD H,d8
                                        self.h = self.mem[self.pc+1]
                                        return 2,8
                                    else: # DAA
                                        input("DAA")
                                        # TODO: DAA
                                        return 1,4
                        else:
                            if byte < 0x2c:
                                if byte < 0x2a:
                                    if byte == 0x28: # JR Z,r8
                                        if not self.zero: return 2,8
                                        jump = self.mem[self.pc+1]
                                        if jump >= 0x80: jump -= 0x100
                                        return 2+jump,12
                                    else: # ADD HL,HL
                                        self.sub = 0
                                        self.l += self.l
                                        if self.l > 0xff:
                                            self.l -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        if ((self.h&0xf) + self.h+self.carry)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.h += self.h + self.carry
                                        if self.h > 0xff:
                                            self.h -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        return 1,8
                                else:
                                    if byte == 0x2a: # LD A,(HL+)
                                        self.a = self.mem[self.h*0x100+self.l]
                                        self.l += 1
                                        if self.l > 0xff:
                                            self.l = 0
                                            self.h += 1
                                            if self.h > 0xff:
                                                self.h = 0
                                        return 1,8
                                    else: # DEC HL
                                        self.l -= 1
                                        if self.l < 0:
                                            self.l = 0xff
                                            self.h -= 1
                                            if self.h < 0: self.h = 0xff
                                        return 1,8
                            else:
                                if byte < 0x2e:
                                    if byte == 0x2c: # INC L
                                        self.sub = 0
                                        if ((self.l&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.l += 1
                                        self.l %= 0x100
                                        self.zero = 0 if self.l else 1
                                        return 1,4
                                    else: # DEC L
                                        self.sub = 1
                                        if ((self.l&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.l -= 1
                                        self.l %= 0x100
                                        self.zero = 0 if self.l else 1
                                        return 1,4
                                else:
                                    if byte == 0x2e: # LD L,d8
                                        self.l = self.mem[self.pc+1]
                                        return 2,8
                                    else: # CPL
                                        self.a = 0xff-self.a
                                        self.sub = 1
                                        self.halfcarry = 1
                                        return 1,4
### SECTION 3
                    else:
                        if byte < 0x38:
                            if byte < 0x34:
                                if byte < 0x32:
                                    if byte == 0x30: # JR NC,r8
                                        if self.carry: return 2,8
                                        jump = self.mem[self.pc+1]
                                        if jump >= 0x80: jump -= 0x100
                                        return 2+jump,12
                                    else: # LD SP,d16
                                        self.sp = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 3,12
                                else:
                                    if byte == 0x32: # LD (HL-),A
                                        self.mem[self.h*0x100+self.l] = self.a
                                        self.l -= 1
                                        if self.l < 0:
                                            self.l = 0xff
                                            self.h -= 1
                                            if self.h < 0: self.h = 0xff
                                        return 1,8
                                    else: # INC SP
                                        self.sp += 1
                                        if self.sp >= 0x10000: self.sp = 0
                                        return 1,8
                            else:
                                if byte < 0x36:
                                    if byte == 0x34: # INC (HL)
                                        self.sub = 0
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((val&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        val += 1
                                        val %= 0x100
                                        self.zero = 0 if val else 1
                                        self.mem[self.h*0x100+self.l] = val
                                        return 1,4
                                    else: # DEC (HL)
                                        self.sub = 1
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((val&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        val -= 1
                                        val %= 0x100
                                        self.zero = 0 if val else 1
                                        self.mem[self.h*0x100+self.l] = val
                                        return 1,4
                                else:
                                    if byte == 0x36: # LD (HL),d8
                                        self.mem[self.h*0x100+self.l] = self.mem[self.pc+1]
                                        return 2,12
                                    else: # SCF
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 1
                                        return 1,4
                        else:
                            if byte < 0x3c:
                                if byte < 0x3a:
                                    if byte == 0x38: # JR C,r8
                                        if not self.carry: return 2,8
                                        jump = self.mem[self.pc+1]
                                        if jump >= 0x80: jump -= 0x100
                                        return 2+jump,12
                                    else: # ADD HL,SP
                                        self.sub = 0
                                        s = self.sp //0x100
                                        p = self.sp %0x100
                                        self.l += p
                                        if self.l > 0xff:
                                            self.l -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        if ((self.h&0xf) + s+self.carry)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.h += s+ self.carry
                                        if self.h > 0xff:
                                            self.h -= 0x100
                                            self.carry = 1
                                        else:
                                            self.carry = 0
                                        return 1,8
                                else:
                                    if byte == 0x3a: # LD A,(HL-)
                                        self.a = self.mem[self.h*0x100+self.l]
                                        self.l -= 1
                                        if self.l < 0:
                                            self.l = 0x100
                                            self.h -= 1
                                            if self.h < 0:
                                                self.h = 0x100
                                        return 1,8
                                    else: # DEC SP
                                        self.sp -= 1
                                        if self.sp < 0: self.sp = 0xffff
                                        return 1,8
                            else:
                                if byte < 0x3e:
                                    if byte == 0x3c: # INC A
                                        self.sub = 0
                                        if ((self.a&0xf) + 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.a += 1
                                        self.a %= 0x100
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # DEC A
                                        self.sub = 1
                                        if ((self.a&0xf) - 1)&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.a -= 1
                                        self.a %= 0x100
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x3e: # LD A,d8
                                        self.a = self.mem[self.pc+1]
                                        return 2,8
                                    else: # CCF
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0 if self.carry else 1
                                        return 1,4
### SECTION 4 - LOADS 1
            else:
                if byte < 0x60:
                    if byte < 0x50:
                        if byte < 0x48:
                            if byte < 0x44:
                                if byte < 0x42:
                                    if byte == 0x40: return 1,4
                                    else: self.b=self.c; return 1,4
                                else:
                                    if byte == 0x42: self.b=self.d; return 1,4
                                    else: self.b=self.e; return 1,4
                            else:
                                if byte < 0x46:
                                    if byte == 0x44: self.b=self.h; return 1,4
                                    else: self.b=self.l; return 1,4
                                else:
                                    if byte == 0x46: self.b=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: self.b=self.a; return 1,4
                        else:
                            if byte < 0x4c:
                                if byte < 0x4a:
                                    if byte == 0x48: self.c=self.b; return 1,4
                                    else: return 1,4
                                else:
                                    if byte == 0x4a: self.c=self.d; return 1,4
                                    else: self.c=self.e; return 1,4
                            else:
                                if byte < 0x4e:
                                    if byte == 0x4c: self.c=self.h; return 1,4
                                    else: self.c=self.l; return 1,4
                                else:
                                    if byte == 0x4e: self.c=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: self.c=self.a; return 1,4
### SECTION 5 - LOADS 2
                    else:
                        if byte < 0x58:
                            if byte < 0x54:
                                if byte < 0x52:
                                    if byte == 0x50: self.d=self.b; return 1,4
                                    else: self.d=self.c; return 1,4
                                else:
                                    if byte == 0x52: return 1,4
                                    else: self.d=self.e; return 1,4
                            else:
                                if byte < 0x56:
                                    if byte == 0x54: self.d=self.h; return 1,4
                                    else: self.d=self.l; return 1,4
                                else:
                                    if byte == 0x56: self.d=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: self.d=self.a; return 1,4
                        else:
                            if byte < 0x5c:
                                if byte < 0x5a:
                                    if byte == 0x58: self.e=self.b; return 1,4
                                    else: self.e=self.c; return 1,4
                                else:
                                    if byte == 0x5a: self.e=self.d; return 1,4
                                    else: return 1,4
                            else:
                                if byte < 0x5e:
                                    if byte == 0x5c: self.e=self.h; return 1,4
                                    else: self.e=self.l; return 1,4
                                else:
                                    if byte == 0x5e: self.e=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: self.e=self.a; return 1,4
### SECTION 6 - LOADS 3
                else:
                    if byte < 0x70:
                        if byte < 0x68:
                            if byte < 0x64:
                                if byte < 0x62:
                                    if byte == 0x60: self.h=self.b; return 1,4
                                    else: self.h=self.c; return 1,4
                                else:
                                    if byte == 0x62: self.h=self.d; return 1,4
                                    else: self.h=self.e; return 1,4
                            else:
                                if byte < 0x66:
                                    if byte == 0x64: return 1,4
                                    else: self.h=self.l; return 1,4
                                else:
                                    if byte == 0x66: self.h=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: self.h=self.a; return 1,4
                        else:
                            if byte < 0x6c:
                                if byte < 0x6a:
                                    if byte == 0x68: self.l=self.b; return 1,4
                                    else: self.l=self.c; return 1,4
                                else:
                                    if byte == 0x6a: self.l=self.d; return 1,4
                                    else: self.l=self.e; return 1,4
                            else:
                                if byte < 0x6e:
                                    if byte == 0x6c: self.l=self.h; return 1,4
                                    else: return 1,4
                                else:
                                    if byte == 0x6e: self.l=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: self.l=self.a; return 1,4
### SECTION 7 - LOADS 4
                    else:
                        if byte < 0x78:
                            if byte < 0x74:
                                if byte < 0x72:
                                    if byte == 0x70: self.mem[self.h*0x100+self.l]=self.b; return 1,8
                                    else: self.mem[self.h*0x100+self.l]=self.c; return 1,8
                                else:
                                    if byte == 0x72: self.mem[self.h*0x100+self.l]=self.d; return 1,8
                                    else: self.mem[self.h*0x100+self.l]=self.e; return 1,8
                            else:
                                if byte < 0x76:
                                    if byte == 0x74: self.mem[self.h*0x100+self.l]=self.h; return 1,8
                                    else: self.mem[self.h*0x100+self.l]=self.l; return 1,8
                                else:
                                    if byte == 0x76: # HALT
                                        input("HALT")
                                        self.halted = True
                                        return 1,4
                                    else: self.mem[self.h*0x100+self.l]=self.a; return 1,8
                        else:
                            if byte < 0x7c:
                                if byte < 0x7a:
                                    if byte == 0x78: self.a=self.b; return 1,4
                                    else: self.a=self.c; return 1,4
                                else:
                                    if byte == 0x7a: self.a=self.d; return 1,4
                                    else: self.a=self.e; return 1,4
                            else:
                                if byte < 0x7e:
                                    if byte == 0x7c: self.a=self.h; return 1,4
                                    else: self.a=self.l; return 1,4
                                else:
                                    if byte == 0x7e: self.a=self.mem[self.h*0x100+self.l]; return 1,8
                                    else: return 1,4
### SECTION 8 - ADD/ADC
        else:
            if byte < 0xc0:
                if byte < 0xa0:
                    if byte < 0x90:
                        if byte < 0x88:
                            if byte < 0x84:
                                if byte < 0x82:
                                    if byte == 0x80: # ADD A,B
                                        if ((self.a&0xf)+(self.b&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.b
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # ADD A,C
                                        if ((self.a&0xf)+(self.c&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.c
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x82: # ADD A,D
                                        if ((self.a&0xf)+(self.d&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.d
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # ADD A,E
                                        if ((self.a&0xf)+(self.e&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.e
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                            else:
                                if byte < 0x86:
                                    if byte == 0x84: # ADD A,H
                                        if ((self.a&0xf)+(self.h&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.h
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # ADD A,L
                                        if ((self.a&0xf)+(self.l&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.l
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x86: # ADD A,(HL)
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((self.a&0xf)+(val&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += val
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,8
                                    else: # ADD A,A
                                        if ((self.a&0xf)+(self.a&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.a
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                        else:
                            if byte < 0x8c:
                                if byte < 0x8a:
                                    if byte == 0x88: # ADC A,B
                                        if ((self.a&0xf)+((self.b+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.b + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # ADC A,C
                                        if ((self.a&0xf)+((self.c+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.c + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x8a: # ADC A,D
                                        if ((self.a&0xf)+((self.d+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.d + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # ADC A,E
                                        if ((self.a&0xf)+((self.e+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.e + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                            else:
                                if byte < 0x8e:
                                    if byte == 0x8c: # ADC A,H
                                        if ((self.a&0xf)+((self.h+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.h + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # ADC A,L
                                        if ((self.a&0xf)+((self.l+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.l + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x8e: # ADC A,(HL)
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((self.a&0xf)+((val+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += val + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,8
                                    else: # ADC A,A
                                        if ((self.a&0xf)+((self.a+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += self.a + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
### SECTION 9 - SUB/SBC
                    else:
                        if byte < 0x98:
                            if byte < 0x94:
                                if byte < 0x92:
                                    if byte == 0x90: # SUB B
                                        if ((self.a&0xf)-(self.b&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.b
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # SUB C
                                        if ((self.a&0xf)-(self.c&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.c
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x92: # SUB D
                                        if ((self.a&0xf)-(self.d&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.d
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # SUB E
                                        if ((self.a&0xf)-(self.e&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.e
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                            else:
                                if byte < 0x96:
                                    if byte == 0x94: # SUB H
                                        if ((self.a&0xf)-(self.h&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.h
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # SUB L
                                        if ((self.a&0xf)-(self.l&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.l
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x96: # SUB (HL)
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((self.a&0xf)-(val&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= val
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,8
                                    else: # SUB A
                                        if ((self.a&0xf)-(self.a&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= self.a
                                        if self.a < 0:
                                            self.a += 0xff
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                        else:
                            if byte < 0x9c:
                                if byte < 0x9a:
                                    if byte == 0x98: # SBC B
                                        if ((self.a&0xf)-((self.b+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.b + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # SBC C
                                        if ((self.a&0xf)-((self.c+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.c + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x9a: # SBC D
                                        if ((self.a&0xf)-((self.d+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.d + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # SBC E
                                        if ((self.a&0xf)-((self.e+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.e + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                            else:
                                if byte < 0x9e:
                                    if byte == 0x9c: # SBC H
                                        if ((self.a&0xf)-((self.h+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.h + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                    else: # SBC L
                                        if ((self.a&0xf)-((self.l+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.l + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
                                else:
                                    if byte == 0x9e: # SBC (HL)
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((self.a&0xf)-((val+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (val + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,8
                                    else: # SBC A
                                        if ((self.a&0xf)-((self.a+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (self.a + self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 1,4
### SECTION A - AND/XOR
                else:
                    if byte < 0xb0:
                        if byte < 0xa8:
                            if byte < 0xa4:
                                if byte < 0xa2:
                                    if byte == 0xa0: # AND B
                                        self.a &= self.b
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                                    else: # AND C
                                        self.a &= self.c
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                                else:
                                    if byte == 0xa2: # AND D
                                        self.a &= self.d
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                                    else: # AND E
                                        self.a &= self.e
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                            else:
                                if byte < 0xa6:
                                    if byte == 0xa4: # AND H
                                        self.a &= self.h
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                                    else: # AND L
                                        self.a &= self.l
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                                else:
                                    if byte == 0xa6: # AND (HL)
                                        self.a &= self.mem[self.h*0x100+self.l]
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,8
                                    else: # AND A
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 1,4
                        else:
                            if byte < 0xac:
                                if byte < 0xaa:
                                    if byte == 0xa8: # XOR B
                                        self.a ^= self.b
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                    else: # XOR C
                                        self.a ^= self.c
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                else:
                                    if byte == 0xaa: # XOR D
                                        self.a ^= self.d
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                    else: # XOR E
                                        self.a ^= self.e
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                            else:
                                if byte < 0xae:
                                    if byte == 0xac: # XOR H
                                        self.a ^= self.h
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                    else: # XOR L
                                        self.a ^= self.l
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                else:
                                    if byte == 0xae: # XOR (HL)
                                        self.a ^= self.mem[self.h*0x100+self.l]
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,8
                                    else: # XOR A
                                        self.a = 0
                                        self.zero = 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
### SECTION B - OR/CP
                    else:
                        if byte < 0xb8:
                            if byte < 0xb4:
                                if byte < 0xb2:
                                    if byte == 0xb0: # OR B
                                        self.a |= self.b
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                    else: # OR C
                                        self.a |= self.c
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                else:
                                    if byte == 0xb2: # OR D
                                        self.a |= self.d
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                    else: # OR E
                                        self.a |= self.e
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                            else:
                                if byte < 0xb6:
                                    if byte == 0xb4: # OR H
                                        self.a |= self.h
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                    else: # OR L
                                        self.a |= self.l
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                                else:
                                    if byte == 0xb6: # OR (HL)
                                        self.a |= self.mem[self.h*0x100+self.l]
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,8
                                    else: # OR A
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 1,4
                        else:
                            if byte < 0xbc:
                                if byte < 0xba:
                                    if byte == 0xb8: # CP B
                                        if ((self.a&0xf)-(self.b&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.b < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.b else 1
                                        return 1,4
                                    else: # CP C
                                        if ((self.a&0xf)-(self.c&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.c < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.c else 1
                                        return 1,4
                                else:
                                    if byte == 0xba: # CP D
                                        if ((self.a&0xf)-(self.d&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.d < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.d else 1
                                        return 1,4
                                    else: # CP E
                                        if ((self.a&0xf)-(self.e&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.e < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.e else 1
                                        return 1,4
                            else:
                                if byte < 0xbe:
                                    if byte == 0xbc: # CP H
                                        if ((self.a&0xf)-(self.h&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.h < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.h else 1
                                        return 1,4
                                    else: # CP L
                                        if ((self.a&0xf)-(self.l&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.l < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.l else 1
                                        return 1,4
                                else:
                                    if byte == 0xbe: # CP (HL)
                                        val = self.mem[self.h*0x100+self.l]
                                        if ((self.a&0xf)-(val&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-val < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-val else 1
                                        return 1,8
                                    else: # CP A
                                        if ((self.a&0xf)-(self.a&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-self.a < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-self.a else 1
                                        return 1,4
### SECTION C
            else:
                if byte < 0xe0:
                    if byte < 0xd0:
                        if byte < 0xc8:
                            if byte < 0xc4:
                                if byte < 0xc2:
                                    if byte == 0xc0: # RET NZ
                                        if self.zero: return 1,8
                                        self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp]
                                        self.sp += 2
                                        return 0,20
                                    else: # POP BC
                                        self.c = self.mem[self.sp]
                                        self.b = self.mem[self.sp+1]
                                        self.sp += 2
                                        return 1,12
                                else:
                                    if byte == 0xc2: # JP NZ,a16
                                        if self.zero: return 3,12
                                        self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 0,16
                                    else: # JP a16
                                        self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 0,16
                            else:
                                if byte < 0xc6:
                                    if byte == 0xc4: # CALL NZ,a16
                                        if self.zero: return 3,12
                                        pc = self.pc + 3
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]
                                        return 0,24
                                    else: # PUSH BC
                                        self.mem[self.sp-1] = self.b
                                        self.mem[self.sp-2] = self.c
                                        self.sp -= 2
                                        return 1,16
                                else:
                                    if byte == 0xc6: # ADD A,d8
                                        val = self.mem[self.pc+1]
                                        if ((self.a&0xf)+(val&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += val
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 2,8
                                    else: # RST 0x0
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x0
                                        return 0,16
                        else:
                            if byte < 0xcc:
                                if byte < 0xca:
                                    if byte == 0xc8: # RET Z
                                        if not self.zero: return 1,8
                                        self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp]
                                        self.sp += 2
                                        return 0,20
                                    else: # RET
                                        self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp]
                                        self.sp += 2
                                        return 0,16
                                else:
                                    if byte == 0xca: # JP Z,a16
                                        if not self.zero: return 3,12
                                        self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 0,16
                                    else: # PREFIX CB
                                        return self.CB(self.mem[self.pc+1])
                            else:
                                if byte < 0xce:
                                    if byte == 0xcc: # CALL Z,a16
                                        if not self.zero: return 3,12
                                        pc = self.pc + 3
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]
                                        return 0,24
                                    else: # CALL a16
                                        pc = self.pc + 3
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]
                                        return 0,24
                                else:
                                    if byte == 0xce: # ADC A,d8
                                        val = self.mem[self.pc+1]
                                        if ((self.a&0xf)+((val+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 0
                                        self.a += val + self.carry
                                        if self.a > 0xff:
                                            self.a -= 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 2,8
                                    else: # RST 0x8
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x8
                                        return 0,16
### SECTION D
                    else:
                        if byte < 0xd8:
                            if byte < 0xd4:
                                if byte < 0xd2:
                                    if byte == 0xd0: # RET NC
                                        if self.carry: return 1,8
                                        self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp]
                                        self.sp += 2
                                        return 0,20
                                    else: # POP DE
                                        self.e = self.mem[self.sp]
                                        self.d = self.mem[self.sp+1]
                                        self.sp += 2
                                        return 1,12
                                else:
                                    if byte == 0xd2: # JP NC,a16
                                        if self.carry: return 3,12
                                        self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 0,16
                                    else: # DOES NOT EXIST
                                        pass
                            else:
                                if byte < 0xd6:
                                    if byte == 0xd4: # CALL NC,a16
                                        if self.carry: return 3,12
                                        pc = self.pc + 3
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]
                                        return 0,24
                                    else: # PUSH DE
                                        self.mem[self.sp-1] = self.d
                                        self.mem[self.sp-2] = self.e
                                        self.sp -= 2
                                        return 1,16
                                else:
                                    if byte == 0xd6: # SUB d8
                                        val = self.mem[self.pc+1]
                                        if ((self.a&0xf)-(val&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= val
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 2,8
                                    else: # RST 0x10
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x10
                                        return 0,16
                        else:
                            if byte < 0xdc:
                                if byte < 0xda:
                                    if byte == 0xd8: # RET C
                                        if not self.carry: return 1,8
                                        self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp]
                                        self.sp += 2
                                        return 0,20
                                    else: # RETI
                                        self.pc = self.mem[self.sp+1]*0x100+self.mem[self.sp]
                                        self.sp += 2
                                        self.interruptsEnabled = 1
                                        return 0,16
                                else:
                                    if byte == 0xda: # JP C,a16
                                        if not self.carry: return 3,12
                                        self.pc = self.mem[self.pc+2]*0x100 + self.mem[self.pc+1]
                                        return 0,16
                                    else: # DOES NOT EXIST
                                        pass
                            else:
                                if byte < 0xde:
                                    if byte == 0xdc: # CALL C,a16
                                        if not self.carry: return 3,12
                                        pc = self.pc + 3
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = self.mem[self.pc + 2] * 0x100 + self.mem[self.pc + 1]
                                        return 0,24
                                    else: # DOES NOT EXIST
                                        pass
                                else:
                                    if byte == 0xde: # SBC d8
                                        val = self.mem[self.pc+1]
                                        if ((self.a&0xf)-((val+self.carry)&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        self.a -= (val+self.carry)
                                        if self.a < 0:
                                            self.a += 0x100
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a else 1
                                        return 2,8
                                    else: # RST 0x18
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x18
                                        return 0,16
### SECTION E
                else:
                    if byte < 0xf0:
                        if byte < 0xe8:
                            if byte < 0xe4:
                                if byte < 0xe2:
                                    if byte == 0xe0: # LDH (a8), A
                                        self.mem[self.mem[self.pc+1]+0xff00] = self.a
                                        return 2,12
                                    else: # POP HL
                                        self.l = self.mem[self.sp]
                                        self.h = self.mem[self.sp+1]
                                        self.sp += 2
                                        return 1,12
                                else:
                                    if byte == 0xe2: # LD (C),A
                                        self.mem[self.c+0xff00] = self.a
                                        return 1,8
                                    else: # DOES NOT EXIST
                                        pass
                            else:
                                if byte < 0xe6:
                                    if byte == 0xe4: # DOES NOT EXIST
                                        pass
                                    else: # PUSH HL
                                        self.mem[self.sp-1] = self.h
                                        self.mem[self.sp-2] = self.l
                                        self.sp -= 2
                                        return 1,16
                                else:
                                    if byte == 0xe6: # AND d8
                                        self.a &= self.mem[self.pc+1]
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 1
                                        self.carry = 0
                                        return 2,8
                                    else: # RST 0x20
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x20
                                        return 0,16
                        else:
                            if byte < 0xec:
                                if byte < 0xea:
                                    if byte == 0xe8: # ADD SP,r8
                                        val = self.mem[self.pc+1]
                                        if val >= 0x80: val -= 0x100
                                        if ((self.sp&0xfff)+(val&0xfff))&0x1000: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.zero = 0
                                        self.sub = 0
                                        self.sp += val
                                        if self.sp >= 0x10000:
                                            self.sp -= 0x10000
                                            self.carry = 1
                                        else: self.carry = 0
                                        return 2,16
                                    else: # JP (HL)
                                        self.pc = self.h*256 + self.l
                                        return 0,4
                                else:
                                    if byte == 0xea: # LD (a16),A
                                        self.mem[self.mem[self.pc+2]*256+self.mem[self.pc+1]] = self.a
                                        return 3,16
                                    else: # DOES NOT EXIST
                                        pass
                            else:
                                if byte < 0xee:
                                    if byte == 0xec: # DOES NOT EXIST
                                        pass
                                    else: # DOES NOT EXIST
                                        pass
                                else:
                                    if byte == 0xee: # XOR d8
                                        self.a ^= self.mem[self.pc+1]
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 2,8
                                    else: # RST 0x28
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x28
                                        return 0,16
### SECTION F
                    else:
                        if byte < 0xf8:
                            if byte < 0xf4:
                                if byte < 0xf2:
                                    if byte == 0xf0: # LDH A,(a8)
                                        self.a = self.mem[self.mem[self.pc+1]+0xff00]
                                        return 2,12
                                    else: # POP AF
                                        flags = self.mem[self.sp]
                                        self.zero = flags>>7
                                        self.sub = (flags>>6)%2
                                        self.halfcarry = (flags>>5)%2
                                        self.carry = (flags>>4)%2
                                        self.a = self.mem[self.sp+1]
                                        self.sp += 2
                                        return 1,12
                                else:
                                    if byte == 0xf2: # LD A,(C)
                                        self.a = self.mem[self.c+0xff00]
                                        return 1,8
                                    else: # DI
                                        self.interruptsEnabled = 0
                                        return 1,4
                            else:
                                if byte < 0xf6:
                                    if byte == 0xf4: # DOES NOT EXIST
                                        pass
                                    else: # PUSH AF
                                        self.mem[self.sp-1] = self.a
                                        flags = self.zero*128 + self.sub*64 + self.halfcarry*32 + self.carry*16
                                        self.mem[self.sp-2] = flags
                                        self.sp -= 2
                                        return 1,16
                                else:
                                    if byte == 0xf6: # OR d8
                                        self.a |= self.mem[self.pc+1]
                                        self.zero = 0 if self.a else 1
                                        self.sub = 0
                                        self.halfcarry = 0
                                        self.carry = 0
                                        return 2,8
                                    else: # RST 0x30
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x30
                                        return 0,16
                        else:
                            if byte < 0xfc:
                                if byte < 0xfa:
                                    if byte == 0xf8: # LD HL,SP+r8
                                        val = self.mem[self.pc+1]
                                        sp = self.sp
                                        if val >= 0x80: val -= 0x100
                                        if ((sp&0xfff)+(val&0xfff))&0x1000: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.zero = 0
                                        self.sub = 0
                                        sp += val
                                        if sp >= 0x10000:
                                            sp -= 0x10000
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.h = sp//256
                                        self.l = sp%256
                                        return 2,12
                                    else: # LD SP,HL
                                        self.sp = self.h*256 + self.l
                                        return 1,8
                                else:
                                    if byte == 0xfa: # LD A,(a16)
                                        self.a = self.mem[self.mem[self.pc + 2] * 256 + self.mem[self.pc + 1]]
                                        return 3,16
                                    else: # EI
                                        self.enableNext = True
                                        return 1,4
                            else:
                                if byte < 0xfe:
                                    if byte == 0xfc: # DOES NOT EXIST
                                        pass
                                    else: # DOES NOT EXIST
                                        pass
                                else:
                                    if byte == 0xfe: # CP d8
                                        val = self.mem[self.pc+1]
                                        if ((self.a&0xf)-(val&0xf))&0x10: self.halfcarry = 1
                                        else: self.halfcarry = 0
                                        self.sub = 1
                                        if self.a-val < 0:
                                            self.carry = 1
                                        else: self.carry = 0
                                        self.zero = 0 if self.a-val else 1
                                        return 2,8
                                    else: # RST 0x38
                                        pc = self.pc + 1
                                        if pc >= 0x10000: pc -= 0x10000
                                        self.mem[self.sp-1] = pc//0x100
                                        self.mem[self.sp-2] = pc%0x100
                                        self.sp -= 2
                                        self.pc = 0x38
                                        return 0,16
        input("ILLEGAL OPCODE %s" % hex(byte)) # Only happens when a non-existent opcode reaches the function
