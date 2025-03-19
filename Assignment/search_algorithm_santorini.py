import copy
import tkinter as tk
from tkinter import messagebox, simpledialog
import random

# Set search depth - adjust based on performance needs
MAX_DEPTH = 4


class SantoriniBoard:
    def __init__(self):
        # 5x5 grid with [height, worker_owner] in each cell
        # height: 0-4 (0=ground, 4=dome/unplayable)
        # worker_owner: 0=none, 1=player1, 2=player2
        self.grid = [[[0, 0] for _ in range(5)] for _ in range(5)]
        self.last_move = None
        # Each player has 2 workers positioned initially
        self.place_initial_workers()

    def place_initial_workers(self):
        # Player 1 workers (could be randomized or predetermined)
        self.grid[1][1][1] = 1
        self.grid[3][3][1] = 1
        # Player 2 workers
        self.grid[1][3][1] = 2
        self.grid[3][1][1] = 2

    def copy(self):
        # Create a deep copy of the board
        new_board = SantoriniBoard()
        new_board.grid = copy.deepcopy(self.grid)
        new_board.last_move = self.last_move
        return new_board

    def display(self):
        # Display the board in a human-readable format
        print("\n  0 1 2 3 4")
        print(" +---------+")
        for y in range(5):
            print(f"{y}|", end="")
            for x in range(5):
                height = self.grid[y][x][0]
                owner = self.grid[y][x][1]

                # Display format: height + owner symbol
                if owner == 0:
                    if height == 4:  # Dome
                        print("D ", end="")
                    else:
                        print(f"{height} ", end="")
                else:
                    worker_symbol = "A" if owner == 1 else "B"
                    print(f"{height}{worker_symbol}", end=" ")
            print("|")
        print(" +---------+")
        print("Legend: [height][worker] (A=Player1, B=Player2, D=Dome)")

    def get_possible_moves(self, player):
        moves = []
        # Find all worker positions for this player
        worker_positions = []
        for y in range(5):
            for x in range(5):
                if self.grid[y][x][1] == player:
                    worker_positions.append((x, y))

        # For each worker, find all possible move+build combinations
        for wx, wy in worker_positions:
            current_height = self.grid[wy][wx][0]
            # Check all adjacent cells for movement
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue  # Skip current position

                    nx, ny = wx + dx, wy + dy
                    # Check if within bounds and no worker and can climb (height difference ≤ 1)
                    if (0 <= nx < 5 and 0 <= ny < 5 and
                            self.grid[ny][nx][1] == 0 and
                            self.grid[ny][nx][0] < 4 and
                            self.grid[ny][nx][0] <= current_height + 1):

                        # Now check all adjacent cells to new position for building
                        for bx in [-1, 0, 1]:
                            for by in [-1, 0, 1]:
                                if bx == 0 and by == 0:
                                    continue  # Skip current position

                                bnx, bny = nx + bx, ny + by
                                # Check if within bounds and no worker and not a complete dome
                                if (0 <= bnx < 5 and 0 <= bny < 5 and
                                        (bnx != wx or bny != wy) and  # Can't build where we came from
                                        self.grid[bny][bnx][1] == 0 and
                                        self.grid[bny][bnx][0] < 4):
                                    moves.append((wx, wy, nx, ny, bnx, bny))

        return moves

    def apply_move(self, move, player):
        wx, wy, nx, ny, bx, by = move
        # Create a copy of the board
        new_board = self.copy()

        # Move worker
        new_board.grid[ny][nx][1] = player
        new_board.grid[wy][wx][1] = 0

        # Build at the target location
        new_board.grid[by][bx][0] += 1

        # Store the last move
        new_board.last_move = move

        return new_board

    def is_win(self, move=None):
        # If move is provided, check if that move won
        if move:
            _, _, nx, ny, _, _ = move
            # If a worker moved to level 3, it's a win
            return self.grid[ny][nx][0] == 3

        # If no move provided, check if any worker is at level 3
        for y in range(5):
            for x in range(5):
                if self.grid[y][x][1] > 0 and self.grid[y][x][0] == 3:
                    return True
        return False

    def winning_player(self):
        # Return the player who won (1 or 2) or 0 if no winner
        for y in range(5):
            for x in range(5):
                if self.grid[y][x][1] > 0 and self.grid[y][x][0] == 3:
                    return self.grid[y][x][1]
        return 0

    def is_draw(self):
        # Check if there are no valid moves for either player
        return len(self.get_possible_moves(1)) == 0 and len(self.get_possible_moves(2)) == 0

    def evaluate(self, player):
        score = 0
        opponent = 3 - player

        # Mobility advantage
        player_moves = len(self.get_possible_moves(player))
        opponent_moves = len(self.get_possible_moves(opponent))
        score += (player_moves - opponent_moves) * 5  # Encourage more mobility

        for y in range(5):
            for x in range(5):
                height = self.grid[y][x][0]
                owner = self.grid[y][x][1]

                if owner == player:
                    # **Reward height advantage**
                    score += height * 10

                    # **Bonus for being on level 2 (near a win)**
                    if height == 2:
                        score += 30

                        # **Prefer center positions (better control)**
                    if 1 <= x <= 3 and 1 <= y <= 3:
                        score += 3

                        # **Bonus for blocking opponent**
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 5 and 0 <= ny < 5 and self.grid[ny][nx][1] == opponent:
                                score += 5  # Small bonus for being near opponent (blocker)

                elif owner == opponent:
                    # **Punish opponent's height advantage**
                    score -= height * 10

                    # **Penalize opponent level 2 placement**
                    if height == 2:
                        score -= 30

                        # **Check if the player is winning or losing**
        winner = self.winning_player()
        if winner == player:
            return 1000  # Win
        elif winner == opponent:
            return -1000  # Loss

        return score


class SantoriniSearchNode:
    def __init__(self, board, player, depth=0, last_move=None):
        self.board = board
        self.player = player  # Current player's turn
        self.depth = depth
        self.last_move = last_move
        self.children = []
        self.value = None

        # Check immediate win condition from previous move
        winner = self.board.winning_player()
        if winner > 0:
            # If it's player 1's win and we're expecting a max node (depth % 2 == 0) or
            # it's player 2's win and we're expecting a min node (depth % 2 == 1)
            self.value = 1000 if (winner == 1 and depth % 2 == 0) or (winner == 2 and depth % 2 == 1) else -1000
            return

        # Limit search depth
        if depth >= self.get_dynamic_depth():
            self.value = self.board.evaluate(1)  # Evaluate from Player 1's perspective
            return

        # Generate children
        self.generate_children()

    def get_dynamic_depth(self):
        """Dynamically adjust depth based on the number of available moves."""
        num_moves = len(self.board.get_possible_moves(self.player))
        if num_moves > 15:
            return 2  # Reduce depth in early game (many moves)
        elif num_moves > 8:
            return 3  # Mid-game
        else:
            return 4  # End-game (fewer moves, can search deeper)

    def generate_children(self):
        moves = self.board.get_possible_moves(self.player)

        # **Sort moves by evaluation to prioritize good moves**
        moves.sort(key=lambda move: self.board.apply_move(move, self.player).evaluate(self.player), reverse=True)

        for move in moves:
            new_board = self.board.apply_move(move, self.player)
            next_player = 3 - self.player  # Switch players (1 -> 2, 2 -> 1)
            child = SantoriniSearchNode(new_board, next_player, self.depth + 1, move)
            self.children.append(child)

    def minimax_value(self, alpha=-float('inf'), beta=float('inf')):
        if self.value is not None:
            return self.value

        if not self.children:  # No moves possible
            self.value = -1000 if self.depth % 2 == 0 else 1000
            return self.value

        if self.depth % 2 == 0:  # Maximizing player (Player 1)
            best_val = -float('inf')
            for child in self.children:
                val = child.minimax_value(alpha, beta)
                best_val = max(best_val, val)
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break
            self.value = best_val
        else:  # Minimizing player (Player 2)
            best_val = float('inf')
            for child in self.children:
                val = child.minimax_value(alpha, beta)
                best_val = min(best_val, val)
                beta = min(beta, best_val)
                if beta <= alpha:
                    break
            self.value = best_val

        return self.value

    def best_move(self):
        # Calculate minimax value for all children
        self.minimax_value()

        if not self.children:
            return None

        # Player 1 wants to maximize, Player 2 wants to minimize
        if self.depth % 2 == 0:  # Maximizing (Player 1's turn)
            best_val = max(child.value for child in self.children)
            best_children = [c for c in self.children if c.value == best_val]
        else:  # Minimizing (Player 2's turn)
            best_val = min(child.value for child in self.children)
            best_children = [c for c in self.children if c.value == best_val]

        # In case of multiple equally good moves, choose one randomly
        best_child = random.choice(best_children)
        return best_child.last_move


class SantoriniGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Santorini Game")
        self.root.resizable(False, False)

        # Game state
        self.board = SantoriniBoard()
        self.current_player = 1
        self.human_player = 1  # Default
        self.ai_player = 2  # Default

        # Game phase tracking
        self.phase = "select_worker"  # Phases: select_worker, select_move, select_build
        self.selected_worker = None
        self.selected_move = None

        # UI components
        self.setup_ui()

        # Ask player choice
        self.ask_player_choice()

    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack()

        # Game info frame
        info_frame = tk.Frame(main_frame)
        info_frame.pack(pady=(0, 10))

        self.status_label = tk.Label(info_frame, text="Game starting...", font=("Arial", 12))
        self.status_label.pack()

        self.turn_label = tk.Label(info_frame, text="Player 1's turn", font=("Arial", 10))
        self.turn_label.pack()

        # Board canvas
        self.canvas = tk.Canvas(main_frame, width=500, height=500, bg="#D2B48C")
        self.canvas.pack()

        # Bind click event
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Button-3>", self.handle_click)  # Bind right-click for deselection

        # Controls frame
        controls_frame = tk.Frame(main_frame, pady=10)
        controls_frame.pack()

        restart_button = tk.Button(controls_frame, text="Restart Game", command=self.restart_game)
        restart_button.pack(side=tk.LEFT, padx=5)

        quit_button = tk.Button(controls_frame, text="Quit", command=self.root.destroy)
        quit_button.pack(side=tk.LEFT, padx=5)

        # Instructions
        instructions = tk.Label(
            main_frame,
            text="How to play: Select a worker, then select where to move, then select where to build.\n"
                 "Win by moving to level 3. You can only move up one level at a time.",
            justify=tk.LEFT,
            font=("Arial", 9)
        )
        instructions.pack(pady=10)

        # Draw the initial board
        self.draw_board()

    def ask_player_choice(self):
        player_choice = simpledialog.askinteger(
            "Player Selection",
            "Do you want to play as Player 1 or Player 2?\n(Enter 1 or 2)",
            minvalue=1, maxvalue=2, initialvalue=1
        )

        if player_choice is None:  # Dialog was closed
            player_choice = 1  # Default to Player 1

        self.human_player = player_choice
        self.ai_player = 3 - player_choice

        self.update_status(f"You are playing as Player {self.human_player}")

        # Start game - AI goes first if player selected 2
        if self.human_player == 2:
            self.ai_turn()

    def draw_board(self):
        self.canvas.delete("all")

        # Draw grid lines
        cell_size = 100
        for i in range(6):
            self.canvas.create_line(0, i * cell_size, 500, i * cell_size)
            self.canvas.create_line(i * cell_size, 0, i * cell_size, 500)

        # Draw cells
        for y in range(5):
            for x in range(5):
                cell_x = x * cell_size
                cell_y = y * cell_size
                height = self.board.grid[y][x][0]
                owner = self.board.grid[y][x][1]

                # Draw buildings
                if height > 0:
                    colors = ["#E0E0E0", "#C0C0C0", "#A0A0A0", "#808080", "#000080"]
                    for h in range(height):
                        level_size = 85 - (h * 5)
                        level_offset = (100 - level_size) / 2
                        self.canvas.create_rectangle(
                            cell_x + level_offset, cell_y + level_offset,
                            cell_x + level_offset + level_size, cell_y + level_offset + level_size,
                            fill=colors[min(h, 4)],
                            outline="black"
                        )

                    if height == 4:
                        self.canvas.create_oval(
                            cell_x + 15, cell_y + 15,
                            cell_x + 85, cell_y + 85,
                            fill="#000080", outline="black"
                        )

                # Draw worker
                if owner > 0:
                    colors = ["", "#FF0000", "#0000FF"]
                    worker_offset = min(height * 5, 20)
                    self.canvas.create_oval(
                        cell_x + 30, cell_y + 30 - worker_offset,
                        cell_x + 70, cell_y + 70 - worker_offset,
                        fill=colors[owner],
                        outline="black",
                        width=2
                    )

        # Highlight selected worker
        if self.selected_worker:
            wx, wy = self.selected_worker
            self.canvas.create_rectangle(
                wx * cell_size, wy * cell_size,
                (wx + 1) * cell_size, (wy + 1) * cell_size,
                outline="green", width=3
            )

        # Highlight selected move location
        if self.selected_move:
            mx, my = self.selected_move
            self.canvas.create_rectangle(
                mx * cell_size, my * cell_size,
                (mx + 1) * cell_size, (my + 1) * cell_size,
                outline="yellow", width=3
            )

    def handle_deselect_worker(self):
        """Handles right-click deselection of a worker."""
        if self.selected_worker:
            print("Right-click detected: Deselecting worker...")  # Debugging output
            self.selected_worker = None
            self.phase = "select_worker"
            self.update_status("Worker deselected. Select a worker.")
            self.draw_board()

    def handle_click(self, event):
        """Handles left-click for selection and right-click for deselection."""
        if self.current_player != self.human_player:
            return  # Not the human's turn

        # Convert click to grid coordinates
        cell_size = 100
        x = event.x // cell_size
        y = event.y // cell_size

        # Check if coordinates are valid
        if not (0 <= x < 5 and 0 <= y < 5):
            return

        if event.num == 3:  # Right-click detected
            self.handle_deselect_worker()
            return

        print(f"Click detected at ({x}, {y}), current phase: {self.phase}")  # Debugging output

        if self.phase == "select_worker":
            self.handle_worker_selection(x, y)
        elif self.phase == "select_move":
            self.handle_move_selection(x, y)
        elif self.phase == "select_build":
            self.handle_build_selection(x, y)

    def handle_worker_selection(self, x, y):
        """Handles selecting or deselecting a worker."""
        print(f"Clicked on: ({x}, {y})")  # Debugging output

        if self.selected_worker == (x, y):
            print("Deselecting worker...")  # Debugging output
            self.selected_worker = None
            self.phase = "select_worker"
            self.update_status("Worker deselected. Select a worker.")
            self.draw_board()
            return

        # Check if the clicked cell contains a worker owned by the player
        if self.board.grid[y][x][1] != self.human_player:
            self.update_status("Please select one of your own workers.")
            return

        print("Selecting worker...")  # Debugging output
        self.selected_worker = (x, y)
        self.phase = "select_move"
        self.update_status("Select where to move your worker.")
        self.draw_board()

    def handle_move_selection(self, x, y):
        wx, wy = self.selected_worker

        # Check if the move is valid
        if self.board.grid[y][x][1] != 0:  # Space occupied
            self.update_status("That space is occupied. Please select an empty space.")
            return

        if self.board.grid[y][x][0] >= 4:  # Dome
            self.update_status("That space has a dome. You can't move there.")
            return

        if self.board.grid[y][x][0] > self.board.grid[wy][wx][0] + 1:  # Too high
            self.update_status("That space is too high to climb. You can only move up one level.")
            return

        if abs(x - wx) > 1 or abs(y - wy) > 1:  # Not adjacent
            self.update_status("You can only move to adjacent spaces.")
            return

        # **NEW FIX: Check if worker has at least one valid build spot after moving**
        temp_board = self.board.copy()  # Create a copy
        temp_board.grid[wy][wx][1] = 0  # Remove worker from old position
        temp_board.grid[y][x][1] = self.human_player  # Place worker at new position

        valid_builds = [
            (bx, by)
            for bx in range(max(0, x - 1), min(5, x + 2))
            for by in range(max(0, y - 1), min(5, y + 2))
            if (bx, by) != (x, y) and temp_board.grid[by][bx][1] == 0 and temp_board.grid[by][bx][0] < 4
        ]

        if not valid_builds:
            self.update_status("This move would trap you! Choose a different move.")
            return

        # **Proceed with the move if valid**
        self.selected_move = (x, y)
        self.phase = "select_build"
        self.update_status("Select where to build.")
        self.draw_board()

    def handle_build_selection(self, x, y):
        wx, wy = self.selected_worker  # Worker start position
        mx, my = self.selected_move  # Worker new position

        # **FIX: Prevent building on the same space where the worker just moved**
        if (x, y) == (mx, my):
            self.update_status("You can't build on the space where your worker just moved!")
            return

        # Check if the build is valid
        if self.board.grid[y][x][1] != 0:
            self.update_status("That space is occupied. Please select an empty space.")
            return

        if self.board.grid[y][x][0] >= 4:
            self.update_status("That space already has a dome. You can't build there.")
            return

        if abs(x - mx) > 1 or abs(y - my) > 1:
            self.update_status("You can only build on spaces adjacent to your worker's new position.")
            return

        if x == wx and y == wy:
            self.update_status("You can't build on the space you moved from.")
            return

        # **NEW: Check if no valid build moves exist (game over)**
        remaining_builds = [
            (bx, by)
            for bx in range(max(0, mx - 1), min(5, mx + 2))
            for by in range(max(0, my - 1), min(5, my + 2))
            if self.board.grid[by][bx][1] == 0 and self.board.grid[by][bx][0] < 4
        ]

        if not remaining_builds:
            messagebox.showinfo("Game Over", f"Player {self.current_player} is trapped and loses!")
            self.restart_game()
            return

        # Apply the move
        move = (wx, wy, mx, my, x, y)
        self.board = self.board.apply_move(move, self.human_player)

        # Check for win
        if self.board.winning_player() == self.human_player:
            self.draw_board()
            messagebox.showinfo("Game Over", "You win!")
            self.restart_game()
            return

        # Check for draw
        if self.board.is_draw():
            self.draw_board()
            messagebox.showinfo("Game Over", "The game is a draw! No more moves possible.")
            self.restart_game()
            return

        # Reset selection and switch to AI's turn
        self.selected_worker = None
        self.selected_move = None
        self.phase = "select_worker"
        self.current_player = self.ai_player

        self.draw_board()
        self.update_turn_label()

        # Delay to make AI's turn more visible
        self.root.after(500, self.ai_turn)

    def check_for_game_over(self):
        """Check if the current player has any valid moves. If not, they lose."""
        possible_moves = self.board.get_possible_moves(self.current_player)

        if not possible_moves:
            winner = 3 - self.current_player  # Opponent wins
            messagebox.showinfo("Game Over", f"Player {winner} wins! No valid moves left.")
            self.restart_game()
            return True  # Game ended

        return False  # Game continues

    def ai_turn(self):
        if self.check_for_game_over():
            return  # AI loses if no moves available

        self.update_status("AI is thinking...")
        self.root.update()

        search = SantoriniSearchNode(self.board, self.ai_player)
        move = search.best_move()

        if move:
            self.board = self.board.apply_move(move, self.ai_player)

            if self.board.winning_player() == self.ai_player:
                self.draw_board()
                messagebox.showinfo("Game Over", "AI wins!")
                self.restart_game()
                return

        self.current_player = self.human_player
        self.update_turn_label()
        self.update_status("Your turn. Select a worker.")
        self.draw_board()

    def update_status(self, message):
        self.status_label.config(text=message)

    def update_turn_label(self):
        player_name = "Your" if self.current_player == self.human_player else "AI's"
        self.turn_label.config(text=f"{player_name} turn (Player {self.current_player})")

    def restart_game(self):
        # Reset game state
        self.board = SantoriniBoard()
        self.current_player = 1
        self.phase = "select_worker"
        self.selected_worker = None
        self.selected_move = None

        # Ask player choice again
        self.ask_player_choice()

        # Update UI
        self.update_status("Game restarted")
        self.update_turn_label()
        self.draw_board()


def main():
    root = tk.Tk()
    app = SantoriniGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()