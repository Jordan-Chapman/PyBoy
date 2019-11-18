# Author: Jordan Chapman
# GPU for use with the CPU object
# IDK what I'm doing

# Gameboy screen is 160x144 pixels

import pygame
import time
from consts import *

# More memory locations
CMAP = 0x8000 # "Character map" - Contains all the tiles in the game
BG1 = 0x9800 # "Background map" - Contains tile pointers for a loaded background
BG2 = 0xa000 # Another background map. The gameboy has two that it can use.

PALLETTE = {"00":0xff,
            "01":0xaa,
            "10":0x55,
            "11":0x00}


class GPU:
    FPS = 60
    FRAME = 1/FPS
    FPS_SAMPLE_RATE = 0.5 # Seconds between FPS Sampling

    def __init__(self, mem, scale=1):
        self.scale = scale
        self.width = int(160*scale)
        self.height = int(144*scale)
        self.mem = mem
        self.last_frame = time.time()
        self.tileram = [None]*384

        # LCD Control flags
        self.enabled = 0
        self.background_tilemap = BG1

        # FPS
        self.count = 0

    def start(self):
        pygame.init()
        pygame.display.set_caption("Gameboy!")
        self.canvas = pygame.display.set_mode((self.width,self.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.surface = pygame.Surface((256,256))
        self.scaled_surface = pygame.Surface((int(256*self.scale),int(256*self.scale)))
        #self.screen_surface = pygame.Surface((256,256))

    def read_lcdc(self):
        """
        Read the LCD control register
        """
        lcdc = bin(self.mem[LCDC])[2:]
        lcdc = "0"*(8-len(lcdc)) + lcdc
        self.enabled = 1 if lcdc[0] == "1" else 0
        self.background_tilemap = BG2 if lcdc[4] == "1" else BG1

    def handle_input(self):
        keys = pygame.key.get_pressed()

        self.mem.pressed_start = 1 if keys[pygame.K_RETURN] else 0
        self.mem.pressed_select = 1 if keys[pygame.K_RSHIFT] else 0
        self.mem.pressed_b = 1 if keys[pygame.K_j] else 0
        self.mem.pressed_a = 1 if keys[pygame.K_k] else 0
        self.mem.pressed_up = 1 if keys[pygame.K_w] else 0
        self.mem.pressed_down = 1 if keys[pygame.K_s] else 0
        self.mem.pressed_left = 1 if keys[pygame.K_a] else 0
        self.mem.pressed_right = 1 if keys[pygame.K_d] else 0

    def build_all_tiles(self, pallette):
        for i in range(384):
            tile_data = self.mem[(CMAP + (i * 16)):(CMAP + (i * 16) + 16)]
            self.tileram[i] = self.build_tile(tile_data, pallette)

    def build_tile(self, tile_data, pallette):
        tile = pygame.Surface((8,8))
        if sum(tile_data) == 0:
            tile.fill((pallette["00"],pallette["00"],pallette["00"]))
            return tile
        for i in range(8):
            first = bin(tile_data[i*2])[2:]
            first = "0"*(8-len(first))+first
            sec = bin(tile_data[i*2 + 1])[2:]
            sec = "0"*(8-len(sec))+sec
            for j in range(8):
                px = pallette[sec[j]+first[j]]
                color = (px,px,px)
                tile.set_at((j,i),color)
        return tile

    def get_pallette(self):
        byte = bin(self.mem[BGP])[2:]
        byte = "0"*(8-len(byte)) + byte
        pallette = {"11": PALLETTE[byte[0:2]],
                    "10": PALLETTE[byte[2:4]],
                    "01": PALLETTE[byte[4:6]],
                    "00": PALLETTE[byte[6:8]]}
        return pallette
        
    def draw(self):
        self.handle_input()
        self.read_lcdc()
        if not self.enabled:
            return
        if self.mem.redraw_tiles:
            self.build_all_tiles(self.get_pallette())
        if self.mem.redraw_tiles or self.mem.redraw_background:
            self.mem.redraw_tiles = False
            self.mem.redraw_background = False
            for i in range(1024):
                byte = self.mem[self.background_tilemap+i]  # Pointer to tile
                tile = self.tileram[byte]
                x = (i % 32) * 8
                y = (i // 32) * 8
                self.surface.blit(tile, (x,y))
            pygame.transform.scale(self.surface, (int(256*self.scale), int(256*self.scale)), self.scaled_surface)
        self.canvas.blit(self.scaled_surface, (-self.mem[SCX]*self.scale,-self.mem[SCY]*self.scale))
        # for i in range(1024):
        #     byte = self.mem[BG1+i]  # Pointer to tile
        #     # Retrieve tile data from ram to trigger tiledraw flag
        #     tile_data = self.mem[(CMAP+(byte*16)):(CMAP+(byte*16)+16)]
        #     # Each byte in tile_data is 4 pixels
        #     x = (i%32)*8
        #     y = (i//32)*8
        #     tile = self.build_tile(tile_data, pallette)
        #     self.surface.blit(tile,(x,y))
        #pygame.transform.scale(self.screen_surface, (self.width,self.height), self.canvas)
        #pygame.transform.scale2x(self.screen_surface, self.canvas)
        pygame.display.flip()

    def events(self):
        events = pygame.event.get()

    def wait(self):
        t = 0
        while time.time() - self.last_frame < GPU.FRAME: t += 1
        pygame.display.set_caption("Wasted cycles: %s" % t)
        self.last_frame = time.time()

    def get_fps(self):
        self.count += 1
        t = time.time()
        if self.last_frame+GPU.FPS_SAMPLE_RATE <= t:
            pygame.display.set_caption("FPS: %s" % (self.count/GPU.FPS_SAMPLE_RATE))
            self.count = 0
            self.last_frame += GPU.FPS_SAMPLE_RATE
        # pygame.display.set_caption("FPS: %s" % (1/(time.time()-self.last_frame)))
        # self.last_frame = time.time()

    def update(self):
        #self.wait()
        self.get_fps()
        self.draw()
        self.events()
