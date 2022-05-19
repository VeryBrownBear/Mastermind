from game import Game

# If the code length is larger than the number of colors then allow_duplicates has to be true
# If it is less than or equal to then allow_duplicates can be either
# CODE LENGTH, NUMBER OF COLORS, DUPLICATES?, NUMBER OF GUESSES, HUMAN_PLAYING?
game = Game(5, 8, True, 10, False)
game.play()