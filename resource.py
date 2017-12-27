import pygame, sys
from pygame.locals import *


class Environment:
    """The all-important environment to provide cohesion between loaded images.
    
    An Environment stores variables like animation fps and tile size.
    Each loader requires an Environment argument.
    """
    
    def __init__(self, tile_w=0, tile_h=0, fps=0):
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.fps = fps


class ImageLoader:
    """Load resource from an image file and accompanying .meta file."""
    
    def __init__(seld, filepath, auto=True):
        self.filepath = filepath
        self.metapath = filepath + '.meta'
        
        self.pad_x, self.pad_y = 0, 0
        self.mar_x, self.mar_y = 0, 0
        self.color_key = None
        
        # Type of image to load (tile/sprite/etc.)?
        
        if auto:
            self.init()
    
    def init(self):
        