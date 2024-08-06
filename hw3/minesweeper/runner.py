import pygame
import sys
import time

from minesweeper import Minesweeper, MinesweeperAI

DIFFICULTY = 'medium'
AI_START = False
RESET = False
w = 0
l = 0
s = 0

if DIFFICULTY == 'easy':
    HEIGHT = 9
    WIDTH = 9
elif DIFFICULTY == 'medium':
    HEIGHT = 16
    WIDTH = 16
elif DIFFICULTY == 'hard':
    HEIGHT = 16
    WIDTH = 30

# Colors
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
WHITE = (255, 255, 255)

# Create game
pygame.init()
size = width, height = 600, 400
screen = pygame.display.set_mode(size)

# Fonts
OPEN_SANS = "assets/fonts/OpenSans-Regular.ttf"
smallFont = pygame.font.Font(OPEN_SANS, 20)
mediumFont = pygame.font.Font(OPEN_SANS, 28)
largeFont = pygame.font.Font(OPEN_SANS, 40)

# Compute board size
BOARD_PADDING = 20
board_width = ((2 / 3) * width) - (BOARD_PADDING * 2)
board_height = height - (BOARD_PADDING * 2)
cell_size = int(min(board_width / WIDTH, board_height / HEIGHT))
board_origin = (BOARD_PADDING, BOARD_PADDING)

# Add images
flag = pygame.image.load("assets/images/flag.png")
flag = pygame.transform.scale(flag, (cell_size, cell_size))
mine = pygame.image.load("assets/images/mine.png")
mine = pygame.transform.scale(mine, (cell_size, cell_size))

# Create game and AI agent
game = Minesweeper(difficulty=DIFFICULTY)
ai = MinesweeperAI(game)

# Keep track of revealed cells, flagged cells, and if a mine was hit
revealed = set()
flags = set()
lost = False

# Show instructions initially
instructions = True
                
while True:
    if (w + l + s) >= 50:
        print(DIFFICULTY)
        print('win', w)
        print('lose', l)
        print('stuck', s)
        break
        
    # Check if game quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    screen.fill(BLACK)

    # Draw board
    cells = []
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):

            # Draw rectangle for cell
            rect = pygame.Rect(
                board_origin[0] + j * cell_size,
                board_origin[1] + i * cell_size,
                cell_size, cell_size
            )
            pygame.draw.rect(screen, GRAY, rect)
            pygame.draw.rect(screen, WHITE, rect, 3)

            # Add a mine, flag, or number if needed
            if game.is_mine((i, j)) and lost:
                screen.blit(mine, rect)
            elif (i, j) in flags:
                screen.blit(flag, rect)
            elif (i, j) in revealed:
                neighbors = smallFont.render(
                    str(game.get_hint((i, j))),
                    True, BLACK
                )
                neighborsTextRect = neighbors.get_rect()
                neighborsTextRect.center = rect.center
                screen.blit(neighbors, neighborsTextRect)

            row.append(rect)
        cells.append(row)

    # AI Move button
    aiButton = pygame.Rect(
        (2 / 3) * width + BOARD_PADDING, (1 / 3) * height - 50,
        (width / 3) - BOARD_PADDING * 2, 50
    )
    buttonText = mediumFont.render("AI Move", True, BLACK)
    buttonRect = buttonText.get_rect()
    buttonRect.center = aiButton.center
    pygame.draw.rect(screen, WHITE, aiButton)
    screen.blit(buttonText, buttonRect)

    # Reset button
    resetButton = pygame.Rect(
        (2 / 3) * width + BOARD_PADDING, (1 / 3) * height + 20,
        (width / 3) - BOARD_PADDING * 2, 50
    )
    buttonText = mediumFont.render("Reset", True, BLACK)
    buttonRect = buttonText.get_rect()
    buttonRect.center = resetButton.center
    pygame.draw.rect(screen, WHITE, resetButton)
    screen.blit(buttonText, buttonRect)

    # Display text
    if lost:
        text = "Lost"
        l += 1
    elif game.mines == flags:
        text = "Won"
        w += 1
    elif flags != game.mines and len(flags) != 0:
        text = "Stuck"
        s += 1
    else:
        text = ""
        
    
    text = mediumFont.render(text, True, WHITE)
    textRect = text.get_rect()
    textRect.center = ((5 / 6) * width, (2 / 3) * height)
    screen.blit(text, textRect)
    
    if RESET:
        # time.sleep(0.5)
        game = Minesweeper(DIFFICULTY)
        ai = MinesweeperAI(game)
        revealed = set()
        flags = set()
        lost = False
        RESET = False
        continue

    move = None
    if not AI_START:
        left, _, right = pygame.mouse.get_pressed()
        if left == 1:
            mouse = pygame.mouse.get_pos()
            # If AI button clicked, make an AI move
            if aiButton.collidepoint(mouse):
                AI_START = True
            # Reset game state
            if resetButton.collidepoint(mouse):
                game = Minesweeper(DIFFICULTY)
                ai = MinesweeperAI(game)
                revealed = set()
                flags = set()
                lost = False
                continue
    else:    
        if not lost:
            move = ai.make_safe_move()
            if move is None:
                flags = ai.mines.copy()
                # AI_START = False
                RESET = True
        else:
            # AI_START = False
            RESET = True
        # Make move and update AI knowledge
        if move:
            if game.is_mine(move):
                lost = True
                RESET = True
                # AI_START = False
            else:
                nearby = game.get_hint(move)
                revealed.add(move)
                ai.add_knowledge(move, nearby)

    pygame.display.flip()