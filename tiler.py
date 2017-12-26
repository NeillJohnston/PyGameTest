import pygame, sys, app
from pygame.locals import *
from app import *


"""
Bit of in-code documentation on the .tlr file format.

Sample file: mylevel.tlr
----------------------
name:Level 1
dmap:10,5
dtile:16,16
file:0,grass.png
tile:A,0,0,0,block
tile:B,0,1,0,block
tile:C,0,2,0,block
tile:D,0,0,1,coin
tile:E,0,1,1,decor
layer:0,   BBBB             AA DDDD AACCCCCCCCCCCCCCCCCCCC
layer:1,          EE      EE                              |<-- this is here just so that Atom will keep the whitespace
----------------------

Data is given by colon-separated key-value pairs, for example, name and nfile. If multiple values are expected for
a key, they're given in a comma-separated list. Size expects two values, both are given.

Naming conventions:
A key that specifies dimension (x,y) should be prefixed with the letter d.
"""


# An environment for Tiler to work in
class TilerEnvironment:
    # Name, dict of tile info, dict of files used, dict of layers, map w/h in tiles, tile w/h in pixels
    name = ''
    tiles = dict()
    files = dict()
    layers = dict()
    wmap, hmap = 0, 0
    wtile, htile = 0, 0

    def __init__(self, tile_factory):
        self.tile_factory = tile_factory

    # Load a file into this environment
    def load(self, file_path):
        # Shortcut to reset the environment, load('')
        if file_path == '':
            self.name = ''
            self.tiles = dict()
            self.files = dict()
            self.layers = dict()
            self.wmap, self.hmap = 0, 0
            self.wtile, self.htile = 0, 0
            return
        with open(file_path) as file:
            data = file.read().splitlines()
            for pair in data:
                key, value = pair.split(':', 1)
                if key == 'name':
                    self.name = value
                elif key == 'dmap':
                    self.wmap, self.hmap = value.split(',', 1)
                    self.wmap, self.hmap = int(self.wmap), int(self.hmap)
                elif key == 'dtile':
                    self.wtile, self.htile = value.split(',', 1)
                    self.wtile, self.htile = int(self.wtile), int(self.htile)
                elif key == 'file':
                    file_id, filepath = value.split(',', 1)
                    self.files[file_id] = load_tiles(filepath, self.wtile, self.htile)
                elif key == 'tile':
                    tile_id, file_id, x, y, tile_type = value.split(',', 4)
                    x, y = int(x), int(y)
                    self.tiles[tile_id] = (file_id, x, y, tile_type)
                elif key == 'layer':
                    layer_id, layer_str = value.split(',', 1)
                    self.layers[layer_id] = [[] for y in range(self.hmap)]
                    for i, c in enumerate(layer_str):
                        y = i // self.wmap
                        if c == ' ':
                            self.layers[layer_id][y].append(None)
                        else:
                            self.layers[layer_id][y].append(self.tile_factory(self.tiles[c]))
            print('loaded %s' % (file_path))


# Load tile images from a file as a 2d list
def load_tiles(file, width, height, x_offset=0, y_offset=0):
    image = pygame.image.load(file).convert()
    image_w, image_h = image.get_size()
    tiles = []
    for y in range(0, image_h // height):
        row = []
        tiles.append(row)
        for x in range(0, image_w // width):
            tile = (x*width + x*x_offset, y*height + y*y_offset, width, height)
            row.append(image.subsurface(tile))
    return tiles


if __name__ == '__main__':
    class TileSet:
        def __init__(self, tiles, twidth, theight, blank='none'):
            self.tiles = tiles
            self.twidth, self.theight = twidth, theight
            self.blank = blank
            self.width = len(self.tiles[0])
            self.height = len(self.tiles)
            self.tile_types = [[self.blank for x in range(self.width)] for y in range(self.height)]
            self.types = {self.blank}
        
        def get(self, x, y):
            return self.tiles[y][x]
        
        def set_type(self, x, y, type):
            self.tile_types[y][x] = type
            self.types |= {type}
    
    class ModAppEx(Element):
        def __init__(self, parent):
            self.parent = parent
            self.tileset = False
            self.tile = False
        
        def set_tileset(self, tileset):
            self.tileset = tileset
        
        def set_tile(self, tile):
            self.tile = tile
        
        def on_render(self):
            if self.tileset:
                for y, row in enumerate(self.tileset.tiles):
                    for x, tile in enumerate(row):
                        self.parent.surface.blit(tile, (x*self.tileset.twidth, y*self.tileset.theight))
            if self.tile:
                w = self.tileset.twidth
                h = self.tileset.theight
                self.parent.surface.blit(pygame.transform.scale(tile, (4*w, 4*h)), (128-2*w, 256+128-2*h, 4*w, 4*h))
            pygame.draw.line(self.parent.surface, (255,255,255), (256,0), (256,500-17))
            for y in range(16):
                for x in range(16):
                    pygame.draw.circle(self.parent.surface, (255,255,255), (x*16, y*16), 0)
            pygame.draw.line(self.parent.surface, (255,255,255), (0, 500-17), (800, 500-17))
    
    class ModApp(App):
        def __init__(self, width, height):
            super().__init__(width, height)
            self.input_line = InputLine(self, 0, 500-17, 12, lambda buffer: self.commander(buffer), cue=":")
            self.add_element(self.input_line)
            self.ex = ModAppEx(self)
            self.add_element(self.ex)
            self.tilesets = []
            self.current = (-1, 0, 0)

        def on_event(self, event):
            super().on_event(event)
            if event.type == KEYDOWN and event.key == K_RETURN:
                self.focus(self.input_line)
            elif event.type == KEYDOWN and event.key == K_l:
                self.input_line.set_buffer('load ')
                self.focus(self.input_line)
            elif event.type == KEYDOWN and event.key == K_t:
                self.input_line.set_buffer('type ')
                self.focus(self.input_line)
            elif event.type == MOUSEBUTTONDOWN and event.button == 3:
                pass
            elif event.type == MOUSEBUTTONDOWN and event.button == 4:
                if len(self.tilesets) > 0:
                    tilesets_index = self.current[0]
                    tilesets_index -= 1
                    tilesets_index %= len(self.tilesets)
                    self.current = (tilesets_index, 0, 0)
                    self.update_current((tilesets_index, 0, 0))
            elif event.type == MOUSEBUTTONDOWN and event.button == 5:
                if len(self.tilesets) > 0:
                    tilesets_index = self.current[0]
                    tilesets_index += 1
                    tilesets_index %= len(self.tilesets)
                    self.update_current((tilesets_index, 0, 0))
        
        def update_current(self, new_current):
            self.current = new_current
            self.ex.set_tileset(self.tilesets[new_current[0]])
            self.ex.set_tile(self.tilesets[new_current[0]].tiles[new_current[2]][new_current[1]])
                
        def commander(self, cmd):
            args = cmd.split(' ')
            cmd = args[0]
            args = args[1:]

            if cmd == 'load':
                try:
                    tiles = load_tiles(args[0], int(args[1]), int(args[2]))
                    tileset = TileSet(tiles, int(args[1]), int(args[2]))
                    self.tilesets.append(tileset)
                    self.update_current((len(self.tilesets)-1, 0, 0))
                    print('loaded %s' % (args[0]))
                except:
                    print('err: load failed')
            elif cmd == 'type':
                try:
                    pass
                except:
                    print('err: type failed')
            else:
                print('no', cmd, 'command known')

    app = ModApp(800, 500)
    app.run()

