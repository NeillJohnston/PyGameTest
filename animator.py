import pygame, sys
from pygame.locals import *


class SpriteSheet:
    """Create a sprite sheet based on an image and meta file.
    
    A sprite sheet holds both its own sprite frames from a single image file, and meta data from a separate meta file
    (if the sprite sheet is sprites.png, the meta file is sprites.png.meta).
    The most significant meta data held by the SpriteSheet class is the animations constructed from the .meta file, this
    is so that animations only need to be hardcoded/magic-string'd by name and file.
    
    A meta file consists of key/value-lists split into lines. Each line contains one key and its list of values. The
    only separator is a single space between keys or values.
    
    Key/Alias       Description: value list (comma-separated)
    #               comment line: completely ignored while reading
    @/echo          echo line: will print this value to console
    sheet           sheet setup: sprite width (x), sprite height (y), offset x, offset y, border x, border y
                    Only x/y pairs need to be present, so the length of the value list can be 2, 4, or 6
    colorkey/key/bg color key to be set to transparent: r, g, b
    animation/anim  animation: animation name, style, a, b, c, d
                    If only a and b are present: a is the row and b is the column of a single frame
                    If a, b, c: a is row, b is col1, c is col2 of a strip of animation frames
                    If a, b, c, d: a is row1, b is col1, c is row2, d is col2 of a rectangle of frames
    fps             fps to play animation at, single value
    
    Due to the weird formatting, a meta file is kinda finnicky, but hopefully flexible.
    The only values that meta absolutely must have is sprite width and sprite height. You can get away with having a
    one-line meta file, if that's all you need.
    """
    
    def __init__(self, file_path, auto=True):
        """Construct a sprite sheet from the image file file_path and meta file file_path.meta.
        
        auto: Auto-init, if set to false, the sprite sheet will have to be initialized by calling init().
        """
        self.file_path = file_path
        
        # Necessary variables from meta, will throw error if one of these do not exist
        self.sprite_w, self.sprite_h = None, None
        
        # Optional variables from meta
        self.offset_w, self.offset_h = 0, 0
        self.border_w, self.border_h = 0, 0
        self.color_key = None
        self.animations = None
        self.fps = 1
        
        if auto:
            self.init()
    
    def init(self):
        """The actual construction of the sprite sheet."""
        i, key = 0, ''
        try:
            # Load meta
            with open(self.file_path + '.meta') as meta:
                lines = meta.read().splitlines()
                for i, attribute in enumerate(lines):
                    # Add each attribute from meta into the SpriteSheet
                    tokens = attribute.strip().split(' ')
                    key = tokens[0]
                    values = tokens[1:]
                    # Switch on key
                    if key == '#' or key == '':
                        # Comment or blank line, nothing to see here
                        pass
                    elif key == 'echo' or key == '@':
                        # Echo to console, just for fun
                        print(' '.join(values))
                    elif key == 'sheet':
                        # Sheet setup
                        self.sprite_w, self.sprite_h = int(values[0]), int(values[1])
                        if len(values) >= 3:
                            self.offset_w, self.offset_h = int(values[2]), int(values[3])
                        if len(values) >= 5:
                            self.border_w, self.border_h = int(values[4]), int(values[5])
                    elif key == 'key' or key == 'colorkey' or key == 'bg':
                        # Color key
                        self.color_key = (int(values[0]), int(values[1]), int(values[2]))
                    elif key == 'anim' or key == 'animation':
                        # Create an animation
                        if self.animations == None:
                            self.animations = dict()
                        animation = tuple(values[2:])
                        if len(animation) not in (2, 3, 4):
                            raise IndexError()
                        self.animations[values[0]] = [values[1], tuple(int(x) for x in animation)]
                    elif key == 'fps':
                        # Fps setup
                        self.fps = int(values[0])
                    else:
                        print('Error: Unrecognized key %s (line %d). Will try to continue, but there may be an issue with %s.meta.' % (key, i+1, self.file_path))
        except FileNotFoundError:
            print('Error: No %s.meta file found!' % (file_path))
            sys.exit(1)
        except IndexError:
            print('Error: Line %d (key %s) in %s.meta may have the wrong number of arguments.' % (i+1, key, self.file_path))
            sys.exit(1)
        
        # Ensure that all the necessary variables exist
        if not all([x is not None for x in [self.sprite_w, self.sprite_h]]):
            print('Error: SpriteSheet variable missing (maybe meta is incomplete?).')
            sys.exit(1)
            
        # Perform the actual initialization of the sprite sheet
        if key == None:
            image = pygame.image.load(self.file_path).convert_alpha()
        else:
            image = pygame.image.load(self.file_path).convert()
            image.set_colorkey(self.color_key)
        
        image_w, image_h = image.get_size()
        self.w = (image_w + self.offset_w - 2*self.border_w) // (self.sprite_w + self.offset_w)
        self.h = (image_h + self.offset_h - 2*self.border_h) // (self.sprite_h + self.offset_h)
        
        # Construct the sheet (2d list of Surfaces, technically subsurfaces)
        self.sheet = []
        for y in range(self.h):
            self.sheet.append([])
            for x in range(self.w):
                rect = (self.border_w + x*(self.sprite_w + self.offset_w), self.border_h + y*(self.sprite_h + self.offset_h), \
                    self.sprite_w, self.sprite_h)
                self.sheet[y].append(image.subsurface(rect))
        
        # Construct animations
        for animation in self.animations:
            style = self.animations[animation][0]
            xs = self.animations[animation][1]
            frames = []
            if len(xs) == 2:
                frames.append((xs[0], xs[1]))
            elif len(xs) == 3:
                r = xs[0]
                for c in range(xs[1], xs[2]+1):
                    frames.append((r, c))
            elif len(xs) == 4:
                for r in range(xs[0], xs[2]+1):
                    for c in range(xs[1], xs[3]+1):
                        frames.append((r, c))
            self.animations[animation] = Animation([self.sheet[x[0]][x[1]] for x in frames], self.fps, style=style)
    
    
    def __getitem__(self, k):
        """Overload the [] operator.
        
        For SpriteSheet sheet:
            sheet[k=int] will return row i of the sheet itself, if it exists, None if else
            sheet[k=str] will return the animation named k, if it exists, None if else
        """
        try:
            if k < len(self.sheet):
                return self.sheet[k]
            else:
                return None
        except TypeError:
            try:
                return self.animations[k]
            except KeyError:
                return None


class TileSheet:
    """Create a tile sheet from an image and accompanying meta file."""
    
    def __init__(self, file_path, auto=True):
        """Construct a tile sheet from the image file file_path and meta file file_path.meta.
        
        auto: Auto-init, if set to false, the sprite sheet will have to be initialized by calling init().
        """
        self.file_path = file_path
        
        # Necessary variables from meta, will throw error if one of these do not exist
        self.tile_w, self.tile_h = None, None
        
        # Optional variables from meta
        self.offset_w, self.offset_h = 0, 0
        self.border_w, self.border_h = 0, 0
        self.color_key = None
        self.tiles = None
        
        if auto:
            self.init()
    
    def init(self):
        """The actual construction of the sprite sheet."""
        i, key = 0, ''
        try:
            # Load meta
            with open(self.file_path + '.meta') as meta:
                lines = meta.read().splitlines()
                for i, attribute in enumerate(lines):
                    # Add each attribute from meta into the SpriteSheet
                    tokens = attribute.strip().split(' ')
                    key = tokens[0]
                    values = tokens[1:]
                    # Switch on key
                    if key == '#' or key == '':
                        # Comment or blank line, nothing to see here
                        pass
                    elif key == 'echo' or key == '@':
                        # Echo to console, just for fun
                        print(' '.join(values))
                    elif key == 'sheet':
                        # Sheet setup
                        self.tile_w, self.tile_h = int(values[0]), int(values[1])
                        if len(values) >= 3:
                            self.offset_w, self.offset_h = int(values[2]), int(values[3])
                        if len(values) >= 5:
                            self.border_w, self.border_h = int(values[4]), int(values[5])
                    elif key == 'key' or key == 'colorkey' or key == 'bg':
                        # Color key
                        self.color_key = (int(values[0]), int(values[1]), int(values[2]))
                    elif key == 'tile':
                        # Make a tile
                        if self.tiles == None:
                            self.tiles = dict()
                        if len(values) == 3:
                            self.tiles[value[0]] = tuple(int(values[1]), int(values[2]))
                    else:
                        print('Error: Unrecognized key %s (line %d). Will try to continue, but there may be an issue with %s.meta.' % (key, i+1, self.file_path))
        except FileNotFoundError:
            print('Error: No %s.meta file found!' % (file_path))
            sys.exit(1)
        except IndexError:
            print('Error: Line %d (key %s) in %s.meta may have the wrong number of arguments.' % (i+1, key, self.file_path))
            sys.exit(1)
        
        # Ensure that all the necessary variables exist
        if not all([x is not None for x in [self.sprite_w, self.sprite_h]]):
            print('Error: TileSheet variable missing (maybe meta is incomplete?).')
            sys.exit(1)
            
        # Perform the actual initialization of the sprite sheet
        if key == None:
            image = pygame.image.load(self.file_path).convert_alpha()
        else:
            image = pygame.image.load(self.file_path).convert()
            image.set_colorkey(self.color_key)
        
        image_w, image_h = image.get_size()
        self.w = (image_w + self.offset_w - 2*self.border_w) // (self.tile_w + self.offset_w)
        self.h = (image_h + self.offset_h - 2*self.border_h) // (self.tile_h + self.offset_h)
        
        # Construct the sheet (2d list of Surfaces, technically subsurfaces)
        self.sheet = []
        for y in range(self.h):
            self.sheet.append([])
            for x in range(self.w):
                rect = (self.border_w + x*(self.sprite_w + self.offset_w), self.border_h + y*(self.sprite_h + self.offset_h), \
                    self.sprite_w, self.sprite_h)
                self.sheet[y].append(image.subsurface(rect))
        
        # Create all tiles
        for tile in tiles:
            pass
        

class Animation:
    """An animation based on a sprite sheet.
    
    Just for funvenience*, there are a few different ways of getting the animation's current frame. If anim is an
    Animation object:
        anim.get_frame(),
        anim.frame,
        anim[0],
        +anim
    All of the above return the animation's current frame. When indexing, anim[1] will return the next frame, anim[2]
    the frame after that, etc.
    
    *funvenience (n): A portmanteau of FUN and CONVENIENCE. A wickedly entertaining way to make life easier.
    """
    
    # Animation styles
    RESET = 'reset' # Jump to beginning at animation end
    PAUSE = 'pause' # Stop at last frame at animation end
    LOOP = 'loop'   # Continue jumping to beginning in a loop
    
    def __init__(self, frames, fps, style=LOOP, cb_complete=None, unit_per_s=1000):
        """Initialize an animation.
        
        frames: an iterable that holds each frame as a Surface
        fps: frames per second to play at
        style: the way that this animation will play, chosen from constants above
        cb_complete: callback function when animation is completed, should take this animation as an argument
        unit_per_s: time conversion as units/second, e.g. default is ms, so unit_time = 1000 milliseconds/second, seconds would be 1 second/second, etc.
        """
        self.frames = list(frames)
        self.fps = fps
        self.style = style
        self.cb_complete = cb_complete
        self.unit_per_s = unit_per_s
        
        self.t = 0
        self.frame_delay = unit_per_s / fps
        self.t_full = self.frame_delay * len(frames)
        self.frame = frames[0]
        self.start = frames[0]
        self.end = frames[-1]
        self.playing = False
        
    def play(self):
        """Run the animation. Must be called before update."""
        self.playing = True
    
    def pause(self):
        """Pause the animation. Will halt updates until play is called again, or self.playing is set manually."""
        self.playing = False
    
    def update(self, dt):
        """Update the animation frame. It is assumed that dt is measured in the chosen unit of time."""
        if not self.playing:
            return
        if self.style == Animation.RESET:
            self.t += dt
            if self.t > self.t_full:
                self.frame = self.start
                self.pause()
                self.on_complete()
            else:
                self.frame = self.frames[int(self.t // self.frame_delay)]
        elif self.style == Animation.PAUSE:
            self.t += dt
            if self.t > self.t_full:
                self.frame = self.end
                self.pause()
                self.on_complete()
            else:
                self.frame = self.frames[int(self.t // self.frame_delay)]
        elif self.style == Animation.LOOP:
            self.t += dt
            self.t %= self.t_full
            self.frame = self.frames[int(self.t // self.frame_delay)]
    
    def reset(self):
        """Reset the animation until play is called."""
        self.t = 0
        self.frame = self.start
        self.playing = False
    
    def on_complete(self):
        """Called when the animation completes."""
        if self.cb_complete is not None:
            self.cb_complete(self)
    
    def get_frame(self):
        """Return the animation's current frame, for true object-oriented fans."""
        return self.frame
    
    def __pos__(self):
        """Return the animation's curent frame, for true code-golfing fans."""
        return self.frame
    
    def __getitem__(self, k):
        """Return the kth current animation frame, for true weirdos."""
        if k == 0:
            return self.frame
        else:
            index = self.t // self.frame_delay
            index += k
            index %= len(self.frames)
            return self.frames[int(index)]


class Animated:
    """An entity that can have animations attached to it.
    
    Animated allows for easy switching between different animations.
    """
    
    def __init__(self, animations, current):
        self.animations = animations
        self.current = current
    
    def update(self, dt):
        self.current.update(dt)
        
    def switcher(self, to_switch):
        def switcher_(animation):
            animation.reset()
            self.current = to_switch
            to_switch.play()
        return switcher_
    
    def __pos__(self):
        return +self.current
    
    def __getitem_(self, k):
        return self.animations[k]


# Testing.
if __name__ == '__main__':
    pygame.display.init()
    screen = pygame.display.set_mode((100, 100))
    clock = pygame.time.Clock()
    fps = 48
    
    ss = SpriteSheet('sprites.png')
    a = Animated(ss.animations, ss['walk'])
    
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                sys.exit(0)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                a.boop()
        clock.tick(fps)
        screen.fill((0,0,0))
        dt = clock.get_time()
        a.update(dt)
        screen.blit(+a, (10, 10))
        pygame.display.flip()
        pygame.display.update()
