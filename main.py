from game import Game
import config

trial_number = 0
max_trials = 25
total_time = 0
total_guesses = 0
while trial_number < max_trials or config.global_game_over:
# CODE LENGTH, NUMBER OF COLORS, DUPLICATES?, NUMBER OF GUESSES, HUMAN_PLAYING?, ALGORITHM (0 for GENETIC, 1 FOR KNUTH)
    game = Game(4, 6, True, 10, False, 1)
    timing = game.play()
    total_time += timing[0]
    total_guesses += timing[1]
    trial_number += 1
print(total_time / max_trials)
print(total_guesses / max_trials)
