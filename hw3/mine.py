import random
from itertools import combinations

# game control module
class Minesweeper():
    
    def __init__(self, difficulty):
        self.difficulty = difficulty
        if difficulty == 'easy':
            self.height = 9
            self.width = 9
            mines = 10
        elif self.difficulty == 'medium':
            self.height = 16
            self.width = 16
            mines = 25
        elif self.difficulty == 'hard':
            self.height = 16
            self.width = 30
            mines = 99
        
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

        # 1) If there is a single-lateral clause in KB
        # all safe cells
        if new_clause.count == 0:
            for cell in new_clause_safe_cells:
                self.mark_safe(cell)
        # single mine cell
        elif new_clause.count == 1 and len(new_clause.cells) == 1:
            self.mark_mine(list(new_clause.cells)[0])
        # 2) Otherwise
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
        # Stores a duplicate of safe moves in order not to modify the value
        possible_safe_moves = self.safes.copy()

        # Removes moves made from possible_safe_moves
        possible_safe_moves -= self.moves_made

        if len(possible_safe_moves) == 0:
            return None

        # Removes an arbitrary safe move from the possible_safe_moves set
        safe_move = possible_safe_moves.pop() 
        return safe_move

def generate_clauses_from_hint(cell, hint):
    row, col = cell
    n = hint
    m = row * col
    
    if n == m:
        return [((i, j), {((i, j), True): True}) for i in range(row) for j in range(col)]
    elif n == 0:
        return [((i, j), {((i, j), False): True}) for i in range(row) for j in range(col)]
    else:
        clauses = []
        unmarked_cells = [(i, j) for i in range(row) for j in range(col)]
        for pos_literals in combinations(unmarked_cells, m - n):
            clause = {}
            for cell in unmarked_cells:
                clause[(cell, True)] = cell in pos_literals
            clauses.append((pos_literals, clause))
        for neg_literals in combinations(unmarked_cells, n):
            clause = {}
            for cell in unmarked_cells:
                clause[(cell, False)] = cell in neg_literals
            clauses.append((neg_literals, clause))
        return clauses

def subsumes(clause1, clause2):
    if set(clause1[0]).issubset(set(clause2[0])):
        if all(clause2[1][cell] == value for cell, value in clause1[1].items()):
            return True
    return False

def match_clauses(clause1, clause2, kb):
    # Check for duplication or subsumption
    subsumed = False
    for other in kb:
        if subsumes(clause1, other):
            subsumed = True
            break
        elif subsumes(clause2, other):
            kb.remove(other)
        elif subsumes(other, clause1):
            return kb
        elif subsumes(other, clause2):
            kb.remove(clause2)
    if subsumed:
        return kb
    
    # Check for complementary literals
    complementary_pairs = get_complementary(clause1, clause2)
    if not complementary_pairs:
        kb.append(clause1)
        kb.append(clause2)
    elif len(complementary_pairs) == 1:
        new_clause = resolve(clause1, clause2, complementary_pairs[0])
        insert_clause(new_clause, kb)
    else:
        kb.append(clause1)
        kb.append(clause2)
    return kb

def insert_clause(clause, kb, single_literals):
    # Check for subsumption
    for other in kb:
        if subsumes(other[0], clause[0]):
            return

    # Check for duplication and add single literals
    new_single_literals = set(clause[0]) - set([l for c in kb for l in c[0]])
    if not new_single_literals:
        return
    single_literals |= new_single_literals

    # Add new clause to knowledge base
    kb.append(clause)

    # Perform unit propagation
    newly_derived = set(new_single_literals)
    while newly_derived:
        l = newly_derived.pop()
        for c in kb:
            if l in c[0]:
                c[0].remove(l)
                if len(c[0]) == 0:
                    return False
                elif len(c[0]) == 1:
                    newly_derived.add(c[0][0])
    return True

def unit_propagate(kb, single_literals):
    new_single_literals = []
    for clause in kb:
        if len(clause[0]) == 1:
            literal = clause[0][0]
            if literal in single_literals:
                continue
            single_literals.add(literal)
            new_single_literals.append(literal)
    for clause in kb:
        if len(clause[0]) > 1:
            new_cells = {cell: value for cell, value in clause[1].items() if cell[0] != new_single_literals[-1][0] or cell[1] != new_single_literals[-1][1]}
            if new_cells != clause[1]:
                new_literals = [l for l in clause[0] if l != new_single_literals[-1]]
                if len(new_literals) == 0:
                    return None
                kb.append((new_literals, new_cells))
    return single_literals

def get_complementary(clause1, clause2):
    literals1 = set(clause1[1].keys())
    literals2 = set(clause2[1].keys())
    complementary_literals = literals1.intersection([negate(l) for l in literals2])
    complementary_pairs = [(l, negate(l)) for l in complementary_literals]
    return complementary_pairs

def resolve(clause1, clause2, complementary_pair):
    new_literals = set(clause1[0]).union(set(clause2[0]))
    new_clause = {}
    for cell, value in clause1[1].items():
        if cell[0] != complementary_pair[0] or cell[1] != complementary_pair[1]:
            new_clause[cell] = value
    for cell, value in clause2[1].items():
        if cell[0] != complementary_pair[0] or cell[1] != complementary_pair[1]:
            new_clause[cell] = value
    return (list(new_literals), new_clause)

def negate(literal):
    return (literal[0], not literal[1])