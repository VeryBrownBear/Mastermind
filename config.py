import pygame
import pygame.font
pygame.font.init()

length = 800
width = 450
screen = pygame.display.set_mode((width, length))
font = pygame.font.SysFont("comicsansms", 30)
cursor = pygame.Surface((40, 40))
total_time = 0
