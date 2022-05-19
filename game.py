import pygame
pygame.init()

import math
import random
import distinctipy
import itertools
import config
import time

class Game:
    def __init__(self, code_length: int, number_of_colors: int, allow_duplicates: bool, number_of_guesses: int, human_playing: bool, algorithm: int):
        # INITIALIZED GAME VARIABLES
        self.code = []
        self.code_length = code_length
        self.number_of_colors = number_of_colors
        self.allow_duplicates = allow_duplicates
        self.number_of_guesses = number_of_guesses
        self.human_playing = human_playing

        # DISPLAY
        self.colors = []

        self.length = config.length
        self.width = config.width
        self.thickness = 2
        self.rows_scale = self.length / (number_of_guesses + 1)
        self.columns_scale = self.width / (code_length + 1)
        self.feedback_columns_scale = self.columns_scale / self.code_length
        self.color_box_scale = (self.columns_scale * code_length) / self.number_of_colors

        # GAME LOGIC
        self.game_over = False
        self.clicked = False
        self.selected_color = (255, 255, 255)

        self.current_line = number_of_guesses - 1
        self.current_input = [0] * code_length
        self.exact_positions = 0
        self.wrong_positions = 0
        self.guesses = []

        self.algorithm = algorithm

        # GENETIC ALGORITHM
        self.previous_generation = []
        self.current_generation = []
        self.population_size = 500
        self.max_generations = 1000
        self.stall_generations = 25
        self.crossover_prob = 0.5
        self.mutation_prob = 0.05
        self.permutation_prob = 0.05
        self.inversion_prob = 0.02
        self.exact_positions_weight = 2
        self.wrong_positions_weight = 3
        self.eligible_children = []

        # KNUTH
        self.possible_codes = []

        self.timing = [0, 1]


    # Check the input with the code
    # Returns a tuple (exact, wrong)
    def check_input(self, input: list, code: list) -> tuple:
        exact_positions = 0
        wrong_positions = 0
        input_list = []
        code_list = []
        for input_element, code_element in zip(input, code):
            if input_element == code_element:
                exact_positions += 1
            else:
                input_list.append(input_element)
                code_list.append(code_element)

        for input_element in input_list:
            if input_element in code_list:
                wrong_positions += 1
                code_list.remove(input_element)

        return (exact_positions, wrong_positions)

    def knuth(self):
        previous_guess = self.guesses[-1]
        good_guesses = []
        for code in self.possible_codes:
            code_score = self.check_input(previous_guess[0], code)
            if code_score == previous_guess[1]:
                good_guesses.append(code)
        self.possible_codes = good_guesses
        guess = random.choice(self.possible_codes)
        return guess
        
    # Fitness evaluation function
    # A guess consists of a (guessed code, feedback code got)
    # Compare with every previous guess as if they were the secret code
    # Returns a tuple (fitness score, eligiblity)
    def evaluate_fitness(self, input: list) -> tuple:
        total_exact_positions_diff = 0
        total_wrong_positions_diff = 0
        for guess in self.guesses:
            input_feedback = self.check_input(input, guess[0])
            total_exact_positions_diff += abs(input_feedback[0] - guess[1][0])
            total_wrong_positions_diff += abs(input_feedback[1] - guess[1][1])
        fitness_score = self.exact_positions_weight * total_exact_positions_diff + self.wrong_positions_weight * total_wrong_positions_diff
        eligible = total_exact_positions_diff == 0 and total_wrong_positions_diff == 0
        if eligible: self.eligible_children.append((input, fitness_score))
        return (fitness_score, eligible)

    # Crossover function
    # A randomly designated "crossover" point which takes the information left of the first parent and
    # right of the second parent to create a child that has some information from both parents
    def crossover(self, parent1: list, parent2: list) -> list:
        crossover_point = random.randint(0, self.code_length - 1)
        child1 = parent1[0: crossover_point] + parent2[crossover_point: self.code_length]
        child2 = parent2[0: crossover_point] + parent1[crossover_point: self.code_length]
        return [child1, child2]

    # Mutate function
    # Randomly change one of the colors of code to a random color
    def mutate(self, child: list) -> list:
        child[random.randint(0, self.code_length - 2)] = random.choice(self.colors)
        return child

    # Permutation function
    # Colors of two random positions are swapped
    def permutation(self, child: list) -> list:
        random_position1 = random.randint(0, self.code_length - 2)
        random_color1 = child[random_position1]
        random_position2 = random.randint(0, self.code_length - 2)
        random_color2 = child[random_position2]
        child[random_position1] = random_color2
        child[random_position2] = random_color1
        return child
    
    # Inversion function
    # Revereses a sequence of colors between two random positions in a code
    def inversion(self, input: list) -> list:
        random_position1 = random.randint(0, self.code_length - 2)
        random_position2 = random.randint(0, self.code_length - 2)
        start = min(random_position1, random_position2)
        end = max(random_position1, random_position2)
        for i in range(len(input[start: end])):
            input[i] = random.choice(self.colors)
        return input

    # Randomly generate a popuation with distinct codes
    def generate_previous_generation(self):
        while len(self.previous_generation) < self.population_size:
            code = [random.choice(self.colors) for i in range(self.code_length)]
            if code not in self.previous_generation:
                self.previous_generation.append((code, self.evaluate_fitness(code)))

    # Genetic algorithm
    # An algorithm that uses the evolutionary concepts of natural selection and genetics to generate a guess that is similar to the rest of the guesses played
    # Each call to this function will be called an iteration. Populations generated within an iteration will be called a generation
    # Before the first iteration, a random guess is made to provide information that the algorithm can generate generations off of
    def natural_selection(self) -> list:
        gen = 0
        stuck = 0
        self.eligible_children = []
        # Before an iteration, generate a new initial population of a constant size with randomly generated distinct codes
        # This is to give the algorithm a vast amount of genes, which is the information in a code,
        # to explore the game decision tree after taking in the information given by the feedback boxes
        while gen < self.max_generations:
            self.current_generation = []
            # Perform a reset of the generation if the iteration has been stuck for more generations than allowed by
            # Replacing the previous generation with a new population
            if stuck > self.stall_generations:
                print(f"Reset on gen {gen}")
                self.previous_generation = []
                self.generate_previous_generation()
                stuck = 0
            # Populate the current generation with the children of parents from the previous generation
            # Each child that inherited information from the two parents has a chance for additional information to be manipulated
            # This is to increase diversity in the gene pool and decrease the chances that the population gets stuck
            while len(self.current_generation) < self.population_size:
                children = []
                # 50% chance of crossover performed on two random codes of the current population
                # Crossover chooses a random crossover point and creates a child with information left of the crossover point of parent1
                # and information right of the crossover point of parent2 and another child with the remanining information
                if random.random() < self.crossover_prob:
                    # MAKE SELECTING PARENTS DEPEND ON SCORE
                    parent1 = random.choice(self.previous_generation)[0]
                    parent2 = random.choice(self.previous_generation)[0]
                    children = self.crossover(parent1, parent2)
                    for child in children:
                        # 3% chance of mutation in a child
                        # Mutation randomly changes one piece of information to a random color
                        if random.random() < self.mutation_prob:
                            child = self.mutate(child)
                        # 3& chance for permutation to swap the position of two pieces of information in a child
                        if random.random() < self.permutation_prob:
                            child = self.permutation(child)
                        # 2% chance of inversion to generate a random sequence of colors between two random points in a child
                        if random.random() < self.inversion_prob:
                            child = self.inversion(child)
                        # After child has been made, evaluate the fitness of the child
                        # Fitness is the score given to a child to numerically describe how similar a child is to the guesses played on the board
                        # Fitness is evaluated by doing the following:
                        #   For every guess that have been played on the board
                        #   Find the number of exact_positions that the child would get if the guess was the secret code (ChildE), then the wrong_positions (ChildW)
                        #   Find the differences between ChildE and GuessE (being the number of exact positions the guess got against the actual secret code)
                        #   and ChildW and GuessW (being the number of wrong positions the guess got against the actual secret code)
                        # If the total sum of these differences is 0, then the code is eligible
                        # If the population is unable to make any eligible children then it is stuck
                        # The fitness score is determined by the sum of the weight of the exact_positions times ChildE and the weight of the wrong_positions times ChildW
                        if child not in self.current_generation:
                            self.current_generation.append((child, self.evaluate_fitness(child)))
                # If a child is not made, take one from the previous generation to live on to the current generation
                else:
                    child = random.choice(self.previous_generation)[0]
                    while child in self.current_generation:
                        child = random.choice(self.previous_generation)[0]
                    self.current_generation.append((child, self.evaluate_fitness(child)))

            # If there are no eligible children then go to next generation
            if not self.eligible_children:
                print(f"Skipped gen {gen}")
                self.previous_generation = self.current_generation
                gen += 1
                stuck += 1
            # Return the first instance a generation is able to create eligible children
            else:
                return self.eligible_children

    # Update current line upon pressing yes button (for human playing)
    def update_display(self, input: list):
        self.current_input = input
        self.exact_positions, self.wrong_positions = self.check_input(input, self.code)
        self.guesses.append((input, (self.exact_positions, self.wrong_positions)))
        for i in range(len(input)):
            pygame.draw.rect(config.screen, input[i], (i * self.columns_scale + self.thickness, self.current_line * self.rows_scale + self.thickness, self.columns_scale - self.thickness, self.rows_scale - self.thickness))
        self.update_feedback_box()
        self.current_line -= 1

    # Creates a list of n visually distinct colors
    def generate_colors(self):
        colors = distinctipy.get_colors(self.number_of_colors)
        for color in colors:
            new_color = tuple(int(i * j) for i, j in zip(color, (255, 255, 255)))
            self.colors.append(new_color)

    # Randomly creates a code based on what was initially given
    def generate_code(self):
        if self.code_length > self.number_of_colors:
            self.allow_duplicates = True
        while len(self.code) < self.code_length:
            random_color = random.choice(self.colors)
            while not self.allow_duplicates and random_color in self.code:
                random_color = random.choice(self.colors)
            self.code.append(random_color)
    
    # Binds the cursor sprite to a black square
    def update_cursor(self):
        config.cursor.fill(self.selected_color, config.cursor.get_rect().inflate((-self.thickness, -self.thickness)))
        pygame.mouse.set_cursor((20, 20), config.cursor)

    # Initialize game display
    def initialize_display(self):
        config.screen.fill((255, 255, 255))
        
        self.update_cursor()

        # Draw horizontal lines (rows)
        for i in range(self.number_of_guesses + 1):
            pygame.draw.line(config.screen, (0, 0, 0), (0, i * self.rows_scale), (self.width, i * self.rows_scale), self.thickness)

        # Draw vertical lines (columns)
        for i in range(self.code_length + 1):
            pygame.draw.line(config.screen, (0, 0, 0), (i * self.columns_scale, 0), (i * self.columns_scale, self.length - self.rows_scale), self.thickness)

        # Draw color selection buttons
        for i in range(len(self.colors)):
            pygame.draw.rect(config.screen, self.colors[i], (i * self.color_box_scale + self.thickness, self.length - self.rows_scale + self.thickness, self.color_box_scale - self.thickness, self.rows_scale))
            pygame.draw.line(config.screen, (0, 0, 0), (i * self.color_box_scale, self.length - self.rows_scale), (i * self.color_box_scale, self.length), self.thickness)

        # Draw feedback box lines
        for i in range(self.code_length + 1):
            pygame.draw.line(config.screen, (0, 0, 0), (self.code_length * self.columns_scale + i * self.feedback_columns_scale, 0), (self.code_length * self.columns_scale + i * self.feedback_columns_scale, self.length), self.thickness)

        # Draw yes button (to confirm guess)
        pygame.draw.rect(config.screen, (0, 0, 0), (self.code_length * self.columns_scale + self.thickness, self.number_of_guesses * self.rows_scale + self.thickness, self.columns_scale, self.rows_scale))
        text = config.font.render("YES", True, (0, 255, 0), (0, 0, 0))
        textRect = text.get_rect()
        textRect.center = (self.code_length * self.columns_scale + self.thickness + self.columns_scale / 2, self.number_of_guesses * self.rows_scale + self.thickness + self.rows_scale / 2)
        config.screen.blit(text, textRect)

        # Update display
        pygame.display.flip()

    # Updates the feedback box on the current line 
    def update_feedback_box(self):
        # Draws red colored boxes for the number of exact positions
        for i in range(self.exact_positions):
            pygame.draw.rect(config.screen, (255, 0, 0), (self.code_length * self.columns_scale + i * self.feedback_columns_scale + self.thickness, (self.current_line) * self.rows_scale + self.thickness, self.feedback_columns_scale - self.thickness, self.rows_scale - self.thickness))
        # Draws gray colored boxes for the number of wrong positions
        for i in range(self.exact_positions, self.exact_positions + self.wrong_positions):
            pygame.draw.rect(config.screen, (150, 150, 150), (self.code_length * self.columns_scale + i * self.feedback_columns_scale + self.thickness, (self.current_line) * self.rows_scale + self.thickness, self.feedback_columns_scale - self.thickness, self.rows_scale - self.thickness))
        pygame.display.flip()
        if self.exact_positions == self.code_length:
            self.game_over = True
            
    def play(self):
        self.generate_colors()
        self.generate_code()
        self.initialize_display()
        self.possible_codes = [tuple(x) for x in itertools.product(self.colors, repeat=self.code_length)]
        print(self.code)
        if not self.human_playing:
            self.update_display([random.choice(self.colors) for i in range(self.code_length)])
            self.generate_previous_generation()
        while not self.game_over:
            if self.current_line == -1:
                break
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                    config.global_game_over = True
                if event.type == pygame.MOUSEBUTTONDOWN and self.clicked == False:
                    self.clicked = True
                if event.type == pygame.MOUSEBUTTONUP and self.clicked == True:
                    self.clicked = False
                    pos = pygame.mouse.get_pos()
                    if pos[0] <= self.width - self.columns_scale - self.thickness:
                        # SELECT COLOR  
                        if pos[1] >= self.length - self.rows_scale + self.thickness:
                            self.selected_color = self.colors[math.floor(pos[0] / self.color_box_scale)]
                            self.update_cursor()
                        # INPUTTING COLORS ON CURRENT LINE
                        if pos[1] > self.current_line * self.rows_scale and pos[1] < (self.current_line + 1) * self.rows_scale:
                            if self.selected_color != (255, 255, 255):
                                pygame.draw.rect(config.screen, self.selected_color, (math.floor(pos[0] / self.columns_scale) * self.columns_scale + self.thickness, math.floor(pos[1] / self.rows_scale) * self.rows_scale + self.thickness, self.columns_scale - self.thickness, self.rows_scale - self.thickness))
                                pygame.display.flip()
                                self.current_input[math.floor(pos[0] / self.columns_scale)] = self.selected_color
                    if self.exact_positions != self.code_length:
                        # IF PRESS YES BUTTON TO CHECK LINE
                        if pos[1] >= self.length - self.rows_scale + self.thickness:
                            if not self.human_playing:
                                if self.algorithm == 0:
                                    start_time = time.time()
                                    ai = sorted(self.natural_selection(), key = lambda i: i[1])[0][0]
                                    end_time = time.time() - start_time
                                    self.timing[0] += end_time
                                    self.timing[1] += 1
                                    print(ai)
                                    self.update_display(ai)
                                if self.algorithm == 1:
                                    start_time = time.time()
                                    code = self.knuth()
                                    end_time = time.time() - start_time
                                    self.timing[0] += end_time
                                    self.timing[1] += 1
                                    print(code)
                                    self.update_display(code)
                            else:
                                print(self.current_input)
                                if 0 not in self.current_input:
                                    self.exact_positions, self.wrong_positions = self.check_input(self.current_input, self.code)
                                    self.update_feedback_box()
                                    self.current_line -= 1
                                    self.current_input = [0] * self.code_length
        print(self.timing)
        print(len(self.guesses))
        time.sleep(2)
        return self.timing
