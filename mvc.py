import pygame
from pygame import locals


class App:
    def __init__(self):
        self.running = True
        self.display = None
        self.width = 800
        self.height = 500

    def on_init(self):
        pygame.init()
        self.surface = pygame.display.set_mode((self.width, self.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.running = True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

    def on_tick(self):
        pass

    def on_render(self):
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self.running = False

        while(self.running):
            for event in pygame.event.get():
                self.on_event(event)
            self.on_tick()
            self.on_render()
        self.on_cleanup()


# Test
if __name__ == "__main__":
    app = App()
    app.on_execute()
