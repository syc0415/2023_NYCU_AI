
import itertools
import random

# game control module
class Minesweeper():
    
    def __init__(self, difficulty):
        self.difficulty = difficulty
        if difficulty == 'easy':
            self.height = 9
            self.width = 9
            mines = 8
        elif self.difficulty == 'medium':
            self.height = 16
            self.width = 16
            mines = 25
        elif self.difficulty == 'hard':
            self.height = 16
            self.width = 30
            mines = 48
        
        self.mines = set()
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(self.height)
            j = random.randrange(self.width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def get_hint(self, cell):
        row, col = cell
        if (row, col) in self.mines:
            return -1
        else:
            count = 0
            for i in range(max(0, row - 1), min(row + 2, self.height)):
                for j in range(max(0, col - 1), min(col + 2, self.width)):
                    if (i, j) in self.mines:
                        count += 1
            return count
        
    def get_initial_safe_cells(self):
        safe_cells = set()
        # safes = int((self.height * self.width) ** 0.5 + 0.5)
        safes = int((self.height * self.width) / 10)
        while len(safe_cells) < safes:
            i = random.randrange(self.height)
            j = random.randrange(self.width)
            if (i, j) not in self.mines and (i, j) not in safe_cells:
                safe_cells.add((i, j))
        return safe_cells
    
    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]


class Clause():
    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        # Any time the number of cells is equal to the count (and count of mines is != 0), we know that all of that clause's cells must be mines.
        if len(self.cells) == self.count:
            if self.count != 0:
                return self.cells  
        return set()

    def known_safes(self):
        # Each time we have a clause whose count is 0, we know that all the surrounding cells are safe
        if self.count == 0:
            return self.cells  
        else:
            return set()

    def mark_mine(self, cell):
        # If a cell known to be a mine is in the clause, remove it and decrement the clause mine count by one as there is now one less mine in the clause
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        # If a cell known to be safe is in the clause, remove it without decrementing the mine count
        if cell in self.cells:
            self.cells.remove(cell)

# player module
class MinesweeperAI():
    
    def __init__(self, game):
        self.game = game
        self.height = self.game.height
        self.width = self.game.width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = self.game.get_initial_safe_cells()

        # KB (knowledge base)
        self.knowledge = []

    def mark_mine(self, cell):
        self.mines.add(cell)
        for clause in self.knowledge:     
            clause.mark_mine(cell)

    def mark_safe(self, cell):
        self.safes.add(cell)
        for clause in self.knowledge:
            clause.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new clause to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new clauses to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        # 1) 2) 
        self.moves_made.add(cell)
        self.mark_safe(cell)
        
        row, col = cell
        neighboring_cells = set()
        for i in range(max(0, row - 1), min(row + 2, self.game.height)):
            for j in range(max(0, col - 1), min(col + 2, self.game.width)):
                # Ignore the cell itself
                if (i, j) != (row, col):
                    if (i, j) not in self.moves_made:
                        if (i, j) in self.mines:
                            count -= 1 
                            continue 
                        if (i, j) in self.safes:
                            continue                   
                        neighboring_cells.add((i, j))

        # add a new clause to the AI's knowledge base 
        new_clause = Clause(neighboring_cells, count)
        new_clause_safe_cells = new_clause.cells 

        # all safe cells
        if new_clause.count == 0:
            for cell in new_clause_safe_cells:
                self.mark_safe(cell)
        # single mine cell
        elif new_clause.count == 1 and len(new_clause.cells) == 1:
            self.mark_mine(list(new_clause.cells)[0])
        # 3) 
        else:
            self.knowledge.append(new_clause)
            
        self.make_inference()

    def make_inference(self):
        # 4) 
        safes = set()
        mines = set()
        # Get set of safe spaces and mines from KB
        for clause in self.knowledge:
            safes = safes.union(clause.known_safes())
            mines = mines.union(clause.known_mines())
        # Mark
        if safes:
            for safe in safes:
                self.mark_safe(safe)
        if mines:
            for mine in mines:
                self.mark_mine(mine)
        
        # 5)
        for i, clause1 in enumerate(self.knowledge):
            for j, clause2 in enumerate(self.knowledge):
                if i != j:
                    if clause1.cells.issubset(clause2.cells):
                        new_clause_cells = clause2.cells - clause1.cells
                        new_clause_count = clause2.count - clause1.count
                        new_clause = Clause(new_clause_cells, new_clause_count)
                        if new_clause not in self.knowledge:
                            self.knowledge.append(new_clause)


    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.
        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        # Stores a duplicate of safe moves in order not to modify the value
        possible_safe_moves = self.safes.copy()

        # Removes moves made from possible_safe_moves
        possible_safe_moves -= self.moves_made

        if len(possible_safe_moves) == 0:
            return None

        # Removes an arbitrary safe move from the possible_safe_moves set
        safe_move = possible_safe_moves.pop() 
        return safe_move