# Author: Jordan Chapman
# Memory object; stores ROM/RAM, watches hardware registers

from consts import * # Constants for hardware register locations
from array import array


class BiosError(Exception):
    pass


class RomError(Exception):
    pass


class Memory:
    def __init__(self, size, rom=None, bios=None):
        """
        Initialize the memory with a given size.
        Loads the given ROM and BIOS
        :param size:
        :param roms:
        """
        self.mem = array('B',[0]*size)
        self.bios = array('B',bios) if bios else None
        self.rom = array('B',rom) if rom else None

        # self.mem = [0]*size
        # self.bios = bios
        # self.rom = rom

        # Tile flag
        self.redraw_tiles = True
        self.redraw_background = True

        # IO register flags
        self.unmapped_bios = False

        # Joypad
        self.pressed_start = 0
        self.pressed_select = 0
        self.preseed_a = 0
        self.pressed_b = 0
        self.pressed_up = 0
        self.pressed_down = 0
        self.pressed_left = 0
        self.pressed_right = 0

        # Defaults
        self.mem[JOY] = 0xff # Read high from all inputs. Low is pressed

    def load_bios(self):
        """
        Load the bios into memory
        """
        if type(self.bios) != type(None):
            self.mem[:0x100] = self.bios
        else:
            raise BiosError("No bios has been given to memory")

    def load_rom(self):
        """
        Load the ROM into memory, remembering the possible existence of a bios
        """
        if type(self.rom) != type(None):
            rom_end = min(0x7fff, len(self.rom))
            self.mem[0x100:rom_end] = self.rom[0x100:rom_end]
        else:
            raise RomError("No rom has been given to memory")

    def unload_bios(self):
        """
        Fill memory at 0x0-0x100 with the ROM header, or 0s if no rom exists
        """
        if type(self.rom) != type(None):
            self.mem[:0x100] = self.rom[:0x100]
        else:
            self.mem[:0x100] = [0]*0x100

    def get_joypad(self):
        joy = self.mem[JOY]
        out = 0xf
        if joy&0b00100000: # CPU requested button inputs
            if self.pressed_start: out -= 0b1000
            if self.pressed_select: out -= 0b100
            if self.pressed_b: out -= 0b10
            if self.preseed_a: out -= 0b1
        elif joy&0b00010000: # CPU requested direction inputs
            if self.pressed_down: out -= 0b1000
            if self.pressed_up: out -= 0b100
            if self.pressed_left: out -= 0b10
            if self.pressed_right: out -= 0b1
        if out != 0xf: self.mem[IF]|= 0b10000 # Joypad Interrupt enable
        else: self.mem[IF] &= 0b11101111 # Joypad Interrupt disable
        return joy+out


    def check_memory(self, loc, value):
        """
        Check for events on change of the memory at that location
        :param loc: Memory location written to
        :param value: Value written at location
        :return: None
        """
        if TILESTART <= loc <= TILEEND:
            self.redraw_tiles = True
        elif BG1START <= loc <= BG1END:
            self.redraw_tiles = True
            self.redraw_background = True
        elif loc == UNMAP_BIOS:
            self.unload_bios()

    def __len__(self):
        return len(self.mem)

    def __iter__(self):
        pass

    def __getitem__(self, key):
        # if key == IF:
        #     return self.mem[IF] | 0b11100000
        if key == JOY:
            return self.get_joypad()
        return self.mem[key]

    def __setitem__(self, key, value):
        if type(key) == int:
            self.check_memory(key, value)
        self.mem[key] = value
