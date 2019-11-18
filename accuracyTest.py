# Author: Jordan Chapman
# For testing the accuracy of some CPUs against others

from cpuList import CPU
from cpuFast import CPU as CPU2
from Memory import Memory
from consts import *


def load_rom(filepath):
    """ Load a ROM array from string:'file' path """
    rom = []
    with open("ROMS/" + filepath, "rb") as file:
        byte = file.read(1)
        while byte:
            rom.append(int.from_bytes(byte, byteorder="big"))
            byte = file.read(1)
    return rom


bios = load_rom("DMG_ROM.bin")  # Load bios
rom = load_rom("tetris.gb")  # Load rom
mem = Memory(0x10000, rom=rom, bios=bios)
mem2 = Memory(0x10000, rom=rom, bios=bios)
mem.load_bios()
mem.load_rom()
mem2.load_bios()
mem2.load_rom()

cpu = CPU(mem)
mem.cpu = cpu
cpu2 = CPU2(mem2)
mem2.cpu = cpu2

clock_rate = 4194304
gpu_rate = 456
cycles = 0
cycles2 = 0


while True:
    lastpc1 = cpu.pc
    lastpc2 = cpu2.pc
    cycles += cpu.cycle()
    cycles2 += cpu2.cycle()
    if cycles > gpu_rate:
        print(hex(cpu.pc),hex(cpu2.pc))
        cycles -= gpu_rate
        cpu.mem[LY] += 1
        if cpu.mem[LY] == 144:
            cpu.mem[IF]|= 1 # VBlank Interrupt enable
        if cpu.mem[LY] == 154:
            cpu.mem[LY] = 0
            cpu.mem[IF] &= 0b11111110 # VBlank Interrupt disable
    if cycles2 > gpu_rate:
        cycles2 -= gpu_rate
        cpu2.mem[LY] += 1
        if cpu2.mem[LY] == 144:
            cpu2.mem[IF]|= 1 # VBlank Interrupt enable
        if cpu2.mem[LY] == 154:
            cpu2.mem[LY] = 0
            cpu2.mem[IF] &= 0b11111110 # VBlank Interrupt disable
    if cpu.pc != cpu2.pc:
        input("PC ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.sp != cpu2.sp:
        input("SP ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.a != cpu2.a:
        input("A ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.b != cpu2.b:
        input("B ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.c != cpu2.c:
        input("C ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.d != cpu2.d:
        input("D ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.e != cpu2.e:
        input("E ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.h != cpu2.h:
        input("H ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.l != cpu2.l:
        input("L ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.zero != cpu2.zero:
        input("ZERO FLAG ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.sub != cpu2.sub:
        input("SUB FLAG ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.halfcarry != cpu2.halfcarry:
        input("HC FLAG ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cpu.carry != cpu2.carry:
        input("CARRY FLAG ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
    if cycles != cycles2:
        input("CYCLE ERROR AT %s, %s" % (hex(lastpc1), hex(lastpc2)))
