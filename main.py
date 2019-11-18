from cpuList import CPU
from gpu import GPU
from Memory import Memory
from consts import *

def load_rom(filepath):
    """ Load a ROM array from string:'file' path """
    rom = []
    with open(filepath, "rb") as file:
        byte = file.read(1)
        while byte:
            rom.append(int.from_bytes(byte, byteorder="big"))
            byte = file.read(1)
    return rom

bios_path = input("Enter a relative path to the BIOS: ")
bios = load_rom(bios_path)  # Load bios

rom_path = input("Enter a relative path to the ROM: ")
rom = load_rom(rom_path)  # Load rom

mem = Memory(0x10000, rom=rom, bios=bios)
mem.load_bios()
mem.load_rom()

# TODO: Account for ROM banking
cpu = CPU(mem)  # Initialize CPU. To see stuff happen, make silent=False
gpu = GPU(mem, scale=2)  # Initialize GPU
mem.cpu = cpu

gpu.start()
clock_rate = 4194304
gpu_rate = 456
cycles = 0

highest_pc = -1
while True:
    cycles += cpu.cycle()
    if cycles > gpu_rate:
        cycles -= gpu_rate
        cpu.mem[LY] += 1
        if cpu.mem[LY] == 144:
            gpu.update()
            cpu.mem[IF]|= 1 # VBlank Interrupt enable
        if cpu.mem[LY] == 154:
            cpu.mem[LY] = 0
            cpu.mem[IF] &= 0b11111110 # VBlank Interrupt disable
