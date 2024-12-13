import pygame
import numpy as np

class GPU:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.memory_size = width * height * 3
        self.vram = [0] * self.memory_size
        
        self.hsync = 0.0
        self.vsync = 0.0
        self.r_signal = 0.0
        self.g_signal = 0.0
        self.b_signal = 0.0
        self.current_x = 0
        self.current_y = 0
        
        self.surface = pygame.Surface((width, height))

    def load_program(self, program):
        """Load and execute a program into the GPU"""
        self.PC = 0
        self.program = program
        self.instructions = {
            0x00: self.nop,     # No operation
            0x01: self.setx,    # Set X coordinate
            0x02: self.sety,    # Set Y coordinate
            0x03: self.setc,    # Set RGB color
            0x04: self.plot,    # Plot pixel at (X,Y)
            0x05: self.clear,   # Clear screen
            0x06: self.line,    # Draw line
            0x07: self.rect,    # Draw rectangle
            0xFF: self.halt     # Halt GPU
        }

        self.current_x = 0
        self.current_y = 0
        self.current_r = 255
        self.current_g = 255
        self.current_b = 255
        self.running = True

        while self.running and self.PC < len(program):
            instruction = program[self.PC]
            if instruction in self.instructions:
                self.instructions[instruction]()
            else:
                raise ValueError(f"Unknown GPU instruction: {hex(instruction)}")
            
    def nop(self):
        """No operation"""
        self.PC += 1
    
    def setx(self):
        """Set X coordinate"""
        self.current_x = self.program[self.PC + 1] % self.width
        self.PC += 2
    
    def sety(self):
        """Set Y coordinate"""
        self.current_y = self.program[self.PC + 1] % self.height
        self.PC += 2
    
    def setc(self):
        """Set RGB color"""
        self.current_r = self.program[self.PC + 1] & 0xFF
        self.current_g = self.program[self.PC + 2] & 0xFF
        self.current_b = self.program[self.PC + 3] & 0xFF
        self.PC += 4
    
    def plot(self):
        """Plot pixel at current (X,Y)"""
        self.write_pixel(self.current_x, self.current_y, self.current_r, self.current_g, self.current_b)
        self.PC += 1
    
    def clear(self):
        """Clear VRAM"""
        self.vram = [0] * (self.width * self.height) * 3

    def line(self):
        """Draw line"""
        self.PC += 1
    
    def rect(self):
        """Draw rectangle"""
        self.PC += 1
    
    def halt(self):
        """Halt"""
        self.PC += 1
        self.running = False

    def write_pixel(self, x, y, r, g, b):
        """Write a pixel to VRAM"""
        if 0 <= x < self.width and 0 <= y < self.height:
            base_index = (y * self.width + x) * 3
            self.vram[base_index] = r & 0xFF
            self.vram[base_index + 1] = g & 0xFF
            self.vram[base_index + 2] = b & 0xFF

    def read_pixel(self, x, y):
        """Read a pixel from VRAM"""
        if 0 <= x < self.width and 0 <= y < self.height:
            base_index = (y * self.width + x) * 3
            return (
                self.vram[base_index],
                self.vram[base_index + 1],
                self.vram[base_index + 2]
            )
        return (0, 0, 0)

    def clear_screen(self, r=0, g=0, b=0):
        """Clear the screen with a specific color"""
        for i in range(0, self.memory_size, 3):
            self.vram[i] = r & 0xFF
            self.vram[i + 1] = g & 0xFF
            self.vram[i + 2] = b & 0xFF

    def simulate_vga_signals(self):
        """Simulate VGA signal generation"""
        x = self.current_x
        y = self.current_y

        self.hsync = 1.0 if x < self.width else 0.0
        self.vsync = 1.0 if y < self.height else 0.0

        if 0 <= x < self.width and 0 <= y < self.height:
            pixel = self.read_pixel(x, y)
            self.r_signal = pixel[0] / 255.0
            self.g_signal = pixel[1] / 255.0
            self.b_signal = pixel[2] / 255.0
        else:
            self.r_signal = 0.0
            self.g_signal = 0.0
            self.b_signal = 0.0

        self.current_x += 1
        if self.current_x >= self.width:
            self.current_x = 0
            self.current_y += 1
            if self.current_y >= self.height:
                self.current_y = 0

    def get_pygame_surface(self):
        """Convert VRAM content to a Pygame surface"""
        pixels = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for y in range(self.height):
            for x in range(self.width):
                pixel = self.read_pixel(x, y)
                pixels[y, x] = pixel

        pygame_surface = pygame.surfarray.make_surface(pixels)
        return pygame_surface

    def draw_rectangle(self, x, y, width, height, r, g, b):
        """Draw a filled rectangle"""
        for dy in range(height):
            for dx in range(width):
                self.write_pixel(x + dx, y + dy, r, g, b)

    def draw_line(self, x1, y1, x2, y2, r, g, b):
        """Draw a line using Bresenham's algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        if dx > dy:
            err = dx / 2.0
            while x != x2:
                self.write_pixel(x, y, r, g, b)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y2:
                self.write_pixel(x, y, r, g, b)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        
        self.write_pixel(x, y, r, g, b)