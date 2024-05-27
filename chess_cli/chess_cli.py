import chess
import chess.engine
import rich_click as click
from rich.console import Console
from rich.traceback import install
from rich.table import Table
from rich.align import Align
import random

# Install rich traceback handler
install()

console = Console()


def ask_stockfish_color():
    while True:
        color = (
            console.input(
                "[bold cyan]Do you want Stockfish to play as white or black? (w/b): [/]"
            )
            .strip()
            .lower()
        )
        if color in ["w", "b"]:
            return color
        console.print(
            "[bold red]Invalid input. Please enter 'w' for white or 'b' for black.[/]"
        )


def ask_flip_board():
    while True:
        flip = (
            console.input("[bold cyan]Do you want to flip the board? (y/n): [/]")
            .strip()
            .lower()
        )
        if flip in ["y", "n"]:
            return flip == "y"
        console.print(
            "[bold red]Invalid input. Please enter 'y' for yes or 'n' for no.[/]"
        )


def get_player_move(board):
    while True:
        move = console.input(
            "[bold cyan]Enter your move (optionally followed by Stockfish's override move, separated by a comma, or 'undo' to undo the last move): [/] "
        ).strip()
        if move.lower() == "undo":
            return ["undo"]
        moves = move.split(",")
        valid_moves = []
        for m in moves:
            try:
                chess_move = chess.Move.from_uci(m.strip())
                if chess_move in board.legal_moves:
                    valid_moves.append(chess_move)
                else:
                    raise ValueError
            except:
                console.print("[bold red]Invalid move. Please try again.[/]")
                break
        else:
            return valid_moves


def initialize_engine(path_to_engine):
    return chess.engine.SimpleEngine.popen_uci(path_to_engine)


def print_board(board, last_move=None, flip=False):
    table = Table(title="Chess Board")
    ranks = range(7, -1, -1) if not flip else range(8)
    files = range(8) if not flip else range(7, -1, -1)
    for rank in ranks:
        row = []
        for file in files:
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            symbol = piece.symbol() if piece else "."
            if last_move and square in (last_move.from_square, last_move.to_square):
                row.append(f"[bold cyan]{symbol}[/]")
            else:
                row.append(symbol)
        table.add_row(*row)
    console.print(Align.center(table))


def choose_suboptimal_move(engine, board, time_limit, depth_limit, accuracy):
    # Get the best move
    result = engine.play(board, chess.engine.Limit(time=time_limit, depth=depth_limit))
    best_move = result.move

    if random.random() < (1 - accuracy / 100):
        # Get a list of legal moves sorted by their evaluation
        info = engine.analyse(
            board, chess.engine.Limit(time=time_limit, depth=depth_limit), multipv=10
        )
        moves = [entry["pv"][0] for entry in info]

        # Select a suboptimal move
        if len(moves) > 1:
            # Choose from the worse half of the moves (less accurate)
            suboptimal_move = random.choice(moves[len(moves) // 2 :])
            return suboptimal_move

    return best_move


@click.command()
@click.option(
    "--engine-path",
    default="/opt/homebrew/bin/stockfish",
    help="Path to your chess engine executable.",
)
@click.option(
    "--time-limit",
    default=5.0,
    help="Time limit for Stockfish to calculate each move (in seconds).",
)
@click.option(
    "--depth-limit",
    default=20,
    type=int,
    help="Depth limit for Stockfish to calculate each move.",
)
@click.option(
    "--accuracy",
    default=100,
    type=int,
    help="Accuracy of Stockfish's moves (0-100%).",
)
def main(engine_path, time_limit, depth_limit, accuracy):
    engine = initialize_engine(engine_path)

    stockfish_color = ask_stockfish_color()
    flip_board = ask_flip_board()
    board = chess.Board()
    move_stack = []

    if stockfish_color == "w":
        console.print("[bold yellow]Stockfish is playing as white.[/]")
        # Stockfish makes the first move if it plays as white
        stockfish_move = choose_suboptimal_move(
            engine, board, time_limit, depth_limit, accuracy
        )
        board.push(stockfish_move)
        move_stack.append(stockfish_move)
        print_board(board, stockfish_move, flip=flip_board)
        console.print(Align.center(f"[bold cyan]Engine played: {stockfish_move}[/]"))
    else:
        console.print("[bold yellow]Stockfish is playing as black.[/]")

    while not board.is_game_over():
        # Input player's move, optionally followed by Stockfish's override move
        moves = get_player_move(board)
        if moves[0] == "undo":
            if len(move_stack) >= 2:
                board.pop()
                board.pop()
                move_stack.pop()
                move_stack.pop()
                print_board(board, flip=flip_board)
                console.print("[bold red]Last move undone.[/]")
            else:
                console.print("[bold red]Cannot undo, not enough moves to undo.[/]")
            continue

        # Apply the player's move
        board.push(moves[0])
        move_stack.append(moves[0])
        print_board(board, moves[0], flip=flip_board)

        if board.is_game_over():
            break

        # Stockfish generates a move
        stockfish_move = choose_suboptimal_move(
            engine, board, time_limit, depth_limit, accuracy
        )

        if len(moves) > 1:
            # If there's an override move, use it instead of Stockfish's move
            stockfish_move = moves[1]
            console.print(
                Align.center(f"[bold red]Move overridden: {stockfish_move}[/]")
            )

        # Apply Stockfish's move
        board.push(stockfish_move)
        move_stack.append(stockfish_move)
        print_board(board, stockfish_move, flip=flip_board)
        console.print(Align.center(f"[bold cyan]Engine played: {stockfish_move}[/]"))

    console.print(Align.center("[bold red]Game over.[/]"))
    console.print(Align.center(f"[bold blue]{board.result()}[/]"))
    engine.quit()


if __name__ == "__main__":
    main()
