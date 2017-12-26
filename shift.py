import pygame, math, sys
from pygame.locals import *


class Smooth:
    """Holds various smoothing functions for easy access."""
    
    # Normal functions, no math required - just plug and play
    
    linear = lambda t: t
    sqrt = lambda t: math.sqrt(t)
    sin = lambda t: math.sin(t * (math.pi / 2))
    sigmoid = lambda t: 1.036 / (1 + math.e ** (4 - 8*t)) - 0.018
    arctan = lambda t: 1/(2*math.atan(4)) * math.atan(8*t - 4) + 0.5
    circle = lambda t: math.sqrt(2*t - t**2)
    bounce = lambda t: -math.sin(2*math.pi*t) / 2 + t
    
    # Generalized function, some math required - plug, test, repeat, and play
    
    def polynomial(cs=(0,0,1)):
        """Polynomial function based on coefficients of t.
        
        cs: list of coefficients of t. The contribution of cs[i] to f is cs[i]*x^i.
        """
        return lambda t: sum(c*t**i for i, c in enumerate(cs))
        
    def inv_polynomial(cs=(0,0,1)):
        """Polynomial function based on inverse coefficients of t.
        
        cs: list of coefficients of t. The contribution of cs[i] to f is cs[i]*x^(1/i).
        """
        return lambda t: cs[0] + sum(c*t**(1/(1+i)) for i, c in enumerate(cs[1:]))
        
    def g_arctan(k=6):
        """Generalized version of the arctan smoothing function. Author's note: personal favorite.
        
        k: smoothing constant. 6 is a good approximation of the sigmoid function.
        """
        a = 1/(2*math.atan(k/2))
        return lambda t: a * math.atan(k*(t-0.5)) + 0.5
    
    def g_bounce(k):
        """Generalized version of the bounce function.
        
        k: bounce amplitude (kinda), f(t) -> t as k -> infinity, f(t) -> wild as k -> 0.
        """
        return lambda t: -math.sin(2*math.pi*t) / k + t


class Vari:
    """A variable holder that can manage animations.
    
    Functionality exists to treat a vari like a dict, by using vari[index].
    Subclasses should implement static variables to use as indices in the vari, i.e. a Rectangle subclass of Vari may
    have its height stored in rect[Rectangle.h]. This is to prevent the use of magic numbers/strings in code. It's
    inconvenient but for a good cause, I swear.
    
    Of course, I can't really tell you what to do now can I? I'm just a docstring.
    """
    def __init__(self, surface):
        self.surface = surface
        self.vars = dict()
        self.anims = set()
        
    def __getitem__(self, key):
        return self.vars[key]
    
    def __setitem__(self, key, value):
        self.vars[key] = value
    
    def add_anim(self, anim):
        """Add an animation to the set of playing animations."""
        self.anims.add(anim)
        
    def update(self, dt):
        spent = set()
        for anim in self.anims:
            if not anim.update(dt):
                spent |= {anim}
        self.anims -= spent
    
    def render(self):
        """Render the Vari. To be implemented in subclasses."""
        pass
    
    def make_vari(self, var_names, var_values):
        """Create the background dict for the Vari's values.
        
        Subclasses should call this at the end of __init__.
        """
        for i, var in enumerate(var_names):
            self.vars[var] = var_values[i]


class Anim:
    """Works with Varis to animate features."""
    
    STRAIGHT = 'straight'   # Animation jumps to 0 when looping
    REVERSE = 'reverse'     # Animation plays in reverse when looping
    
    def __init__(self, vari, v, q, t_play, f, loop=STRAIGHT, repeat=0, delay_start=0, delay_end=0):
        # Contained vari, variable to modify, end point, time required to play the animation forward once
        self.vari = vari
        self.v = v
        self.q = q
        self.t_play = t_play
        self.f = f
        
        # Type of loop, number of times to repeat, delay before animation plays, delay after animation ends
        self.loop = loop
        self.repeat = repeat
        self.delay_start = delay_start
        self.delay_end = delay_end
        
        # Time, end time, animation function, boolean if playing forward, boolean if currently playing.
        self.t = 0
        self.t_end = delay_start + t_play + delay_end
        self.f_anim = lerp(vari[v], q, delay_start, delay_start+t_play, f)
        self.play_forward = True
        self.playing = True
    
    def update(self, dt):
        """Update the animation values based on the change in time dt."""
        if not self.playing:
            return False
        if self.loop == Anim.STRAIGHT:
            self.t += dt
            if self.t > self.t_end:
                self.repeat -= 1
                if self.repeat < 0:
                    # Break at the end of the animation
                    self.vari[self.v] = self.f_anim(self.t_end)
                    self.playing = False
                    return False
                else:
                    self.t %= self.t_end
        elif self.loop == Anim.REVERSE:
            self.t += dt if self.play_forward else -dt
            if self.t > self.t_end or self.t < 0:
                # A single forward or backward play of a reversing animation counts as one-half of a repetition
                self.repeat -= 0.5
                if self.repeat < 0 and self.play_forward:
                    # Break at the end of the animation
                    self.vari[self.v] = self.f_anim(self.t_end)
                    self.playing = False
                    return False
                elif self.repeat < 0 and not self.play_forward:
                    # Break at the start of the animation
                    self.vari[self.v] = self.f_anim(0)
                    self.playing = False
                    return False
                elif self.play_forward:
                    self.t = self.t_end - (self.t - self.t_end)
                elif not self.play_forward:
                    self.t = -self.t
                self.play_forward = not self.play_forward
        self.vari[self.v] = self.f_anim(self.t)
        return True
        

def SeqAnim(Anim):
    """Multiple animations on the same vari feature, in sequence."""
    
    STRAIGHT = 'straight'   # Cuts to beginning at the end of sequence
    REVERSE = 'reverse'     # Reverses to beginning at the end of sequence
    
    def __init__(self, vari, v, qs, t_plays, fs, loop=STRAIGHT, repeat=0, delay_start=0, delay_end=0):
        pass
    

class Circle(Vari):
    """A circle with center C and radius R. Rendered with color COLOR and width WIDTH (0=filled)."""
    C = 'x'
    R = 'r'
    COLOR = 'color'
    WIDTH = 'width'
    
    def __init__(self, surface, x, y, r, color, width):
        """Init circle."""
        super().__init__(surface)
        self.make_vari([Circle.C, Circle.R, Circle.COLOR, Circle.WIDTH], [(x, y), r, color, width])
    
    def render(self):
        """Render the circle to self.surface."""
        pygame.draw.circle(surface, self[Circle.COLOR], (int(self[Circle.C][0]), int(self[Circle.C][1])),\
                           int(self[Circle.R]), self[Circle.WIDTH])


def interpolate(p, q, t, f):
    """Find the interpolated vector between p and q at position t of smoothing function f.
    
    p, q: n-dimensional vectors or single numbers
    t: proportion of time passed for interpolation, i.e. a number within [0, 1]
    f: a function such that f(0) = 0, f(1) = 1
    """
    try:
        iter(p), iter(q)
    except TypeError:
        return p + f(t) * (q-p)
    return tuple([p[i] + f(t) * (q[i]-p[i]) for i in range(len(p))])


def lerp(p, q, t_min, t_max, f):
    """Get a function f(t) that returns the interpolation between p and q at time t
    
    Unlike inter, the function returned by lerp is usable for any value of t between t_min and t_max.
    The function ensures that t is within [t_min, t_max].
    
    p, q: n-dimensional vectors or single numbers
    t_min, t_max: starting/ending time for interpolation
    f: a function such that f(0) = 0, f(1) = 1
    """
    return lambda t: interpolate(p, q, (max(t_min, min(t_max, t))-t_min) / (t_max-t_min), f)


# Test
if __name__ == '__main__':
    surface = pygame.display.set_mode((500, 500))
    clock = pygame.time.Clock()
    clock.get_time()
    
    # Colooooors
    black = (0, 0, 0)
    white = (255, 255, 255)
    blay = (180, 180, 185)
    
    shape = Circle(surface, 250, 250, 50, (0,0,0), 2)
    
    while True:
        surface.fill(blay)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == K_SPACE:
                if len(shape.anims) == 0:
                    anim = Anim()
                    shape.add_anim(anim)
        
        # Draw
        clock.tick(60)
        dt = clock.get_time()
        shape.update(dt)
        shape.render()
        
        pygame.display.update()
        
