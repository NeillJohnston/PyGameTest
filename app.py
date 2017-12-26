import pygame, sys
from pygame.locals import *


# The main app, holder of elements
class App:
    def __init__(self, width, height):
        self.surface = pygame.display.set_mode((width, height))
        self.focused = self
        self.elements = []
        self.running = True

    # Add an element
    def add_element(self, element):
        self.elements.append(element)

    # Focus an element
    def focus(self, element):
        self.focused.on_unfocus()
        self.focused = element
        element.on_focus()

    def on_focus(self):
        self.focused = self

    def on_unfocus(self):
        pass

    def on_event(self, event):
        pass

    # Run the app
    def run(self):
        while self.running:
            self.surface.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)
                self.focused.on_event(event)
            for element in self.elements:
                element.on_render()
            pygame.display.update()

        pygame.quit()


# An element that can receive focus and such
class Element:
    # Parent is an App
    def __init__(self, parent):
        self.focused = False
        self.parent = parent

    def on_focus(self):
        self.focused = True

    def on_unfocus(self):
        self.focused = False
        self.parent.on_focus()

    # Called when the element is focused and an event occurs
    def on_event(self, event):
        pass

    # Called when it's render time (should call self.parent.surface)
    def on_render(self):
        pass


# An invisible keyboard receiver, stores in a buffer and sent on enter
class InputBuffer(Element):
    # Keys that may be typed
    LEGAL_KEYS = 'abcdefghijklmnopqrstuvwxyz' +\
                 'ABCDEFGIHJKLMNOPQRSTUVWXYZ' +\
                 '1234567890' +\
                 '!@#$%^&*()[]{}<>-_=+,./?;:\'\"|\\`~ '
    # Keys that shouldn't add to the index in the buffer
    ILLEGAL_KEYS = (K_LSHIFT, K_RSHIFT, K_LCTRL, K_RCTRL, K_LALT, K_RALT)

    def __init__(self, parent, send):
        super().__init__(parent)

        self.send = send
        self.buffer = ''
        self.index = 0

    # Receive key events, if focused
    def on_event(self, event):
        super().on_event(event)

        if hasattr(event, 'key') and event.type == KEYDOWN and self.focused:
            if event.key == K_RETURN:
                self.on_send()
            elif event.key == K_ESCAPE:
                self.on_unfocus()

            elif event.key == K_BACKSPACE and len(self.buffer) > 0 and self.index > 0:
                # If backspace is pressed, try to delete the current key
                self.buffer = self.buffer[:self.index-1] + self.buffer[self.index:]
                self.index -= 1
            elif event.key == K_LEFT:
                # Allow leftward movement within the buffer
                self.index = max(0, self.index - 1)
            elif event.key == K_RIGHT:
                # Allow rightward movement within the buffer
                self.index = min(len(self.buffer), self.index + 1)

            elif event.unicode in self.LEGAL_KEYS and event.key not in self.ILLEGAL_KEYS:
                # Only add a key if it is within the legal keys
                self.buffer = self.buffer[:self.index] + event.unicode + self.buffer[self.index:]
                self.index += 1

    # Send the current buffer, lose focus
    def on_send(self):
        self.send(self.buffer)
        self.on_unfocus()

    def on_focus(self):
        super().on_focus()

    # On unfocus, clear the buffer as well
    def on_unfocus(self):
        super().on_unfocus()
        self.buffer = ''
        self.index = 0

    # Set the buffer externally
    def set_buffer(self, buffer):
        self.buffer = buffer
        self.index = len(self.buffer)


# A visible wrapper around an InputBuffer, activates when focused
class InputLine(InputBuffer):
    # Default cue is a colon, default text color is white
    def __init__(self, parent, x, y, height, send, cue=":", color_text=(255,255,255)):
        super().__init__(parent, send)

        pygame.font.init()
        self.x = x
        self.y = y
        self.height = height
        self.cue = cue
        self.font = pygame.font.SysFont('Courier New, Courier, Arial', height)
        self.color_text = color_text

    # Render the InputLine
    def on_render(self):
        if self.focused:
            self.parent.surface.blit(self.font.render(self.cue + self.buffer, True, self.color_text), (self.x, self.y))
            self.parent.surface.blit(self.font.render(''.join([' '] * (self.index + 1)) + '_', True, self.color_text), (self.x, self.y))
