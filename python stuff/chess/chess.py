import abc, typing, enum, copy, pprint

class Color(enum.Enum):
    WHITE = 0
    BLACK = 1

class Position:
    def __init__(self: typing.Self, x: typing.Union[int, str], y: int):
        if isinstance(x, str):
            x = ord(x) - ord('a') + 1
        self.x = x
        self.y = y
    
    def __str__(self: typing.Self):
        return f'{self.alphax}{self.y}'
    
    def __repr__(self: typing.Self):
        return f'{self.__class__.__name__}({self.x}, {self.y})'
    
    @property
    def alphax(self: typing.Self):
        return chr(self.x + ord('a') - 1)
    
    def __add__(self: typing.Self, other: typing.Tuple[int, int]):
        return Position(self.x+other[0], self.y+other[1])
    
    def __sub__(self: typing.Self, other: typing.Tuple[int, int]):
        return Position(self.x-other[0], self.y-other[1])
    
    def __eq__(self: typing.Self, other: typing.Any):
        if isinstance(other, Position):
            return self.x == other.x and self.y == other.y
        return False
    
    def __copy__(self: typing.Self):
        return Position(self.x, self.y)

class Board:

    size = (8, 8)

    def __init__(self: typing.Self, show_numbers: bool=False):
        self.board = [[NullPiece(Position(x+1,y+1)) for x in range(self.size[0])] for y in range(self.size[1])]
        self.show_numbers = show_numbers

    def __getitem__(self: typing.Self, pos: Position):
        if pos.x < 0 or pos.x >= 9 or pos.y < 0 or pos.y >= 9:
            raise OutOfBounds(pos)
        return self.board[pos.y-1][pos.x-1]

    def __setitem__(self: typing.Self, pos: Position, value: typing.Type):
        if pos.x < 0 or pos.x > 8 or pos.y < 0 or pos.y > 8:
            raise OutOfBounds(pos)
        value.position = pos
        self.board[pos.y-1][pos.x-1] = value

    def has_piece_type(self: typing.Self, piece_class: typing.Any, color: Color):
        for row in self.board:
            for piece in row:
                if isinstance(piece, piece_class) and piece.color == color:
                    return True
        return False

    def __str__(self: typing.Self):
        output = ''
        if self.show_numbers:
            output += '  '
            for i in self.board[0]:
                output += f'{i.position.alphax} '
            output += '\n'
        for row in self.board:
            if self.show_numbers:
                output += f'{row[0].position.y} '
            for piece in row:
                output += f'{piece} '
            output += '\n'
        
        return output
    
    def __repr__(self: typing.Self):
        return f'{self.__class__.__name__}({pprint.pformat(self.board)})'

    def __copy__(self: typing.Self):
        new_board = self.__class__()
        new_board.board = copy.deepcopy(self.board)
        return new_board

class Piece(abc.ABC):

    def __init__(self: typing.Self, color: Color, position: Position):
        self.color = color
        self.position = position
        self.moved = False
        self.last_move = None
    
    @property
    @abc.abstractmethod
    def icon(self: typing.Self):
        pass
    
    def __str__(self: typing.Self) -> str:
        return self.icon
    
    @abc.abstractmethod
    def get_moves(self: typing.Self, board: Board, pos: Position):
        pass

    def __repr__(self: typing.Self) -> str:
        return f"{self.icon} ({self.__class__.__name__}) at {self.position!r}"
    
    def __copy__(self: typing.Self):
        new_piece = self.__class__(self.color, self.position)
        new_piece.moved = self.moved
        return new_piece
    
    def __eq__(self: typing.Self, other: typing.Any):
        return self.position == other.position and self.color == other.color and isinstance(other, self.__class__)

    
class Move:
    def __init__(self: typing.Self, from_pos: Position, to_pos: Position, piece: Piece, taken: Piece=None, promotion: Piece=None, related: typing.List[Piece]=[]):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece
        self.taken = taken
        self.promotion = promotion
        self.related = related
    
    def __str__(self: typing.Self):
        return f'{self.piece} {self.from_pos} -> {str(self.taken)+" " if self.taken else ""}{self.to_pos}'
    
    def __repr__(self: typing.Self):
        return f'{self.piece} {self.from_pos!r} -> {repr(self.taken)+" " if self.taken else ""}{self.to_pos!r}'
    
    def freeze(self: typing.Self):
        self.from_pos = copy.copy(self.from_pos)
        self.to_pos = copy.copy(self.to_pos)
        self.piece = copy.copy(self.piece)
        self.taken = copy.copy(self.taken)
        self.promotion = copy.copy(self.promotion)
    
    def __copy__(self: typing.Self):
        return self.__class__(self.from_pos, self.to_pos, self.piece, self.taken, self.promotion)
    
    def frozen(self: typing.Self):
        move = copy.copy(self)
        move.freeze()
        return move

class NullPiece(Piece):
    def __init__(self: typing.Self, position: Position):
        super().__init__(None, position)
    
    @property
    def icon(self: typing.Self):
        return ' '
    
    def get_moves(self: typing.Self, board: Board):
        return []
    
    def __bool__(self: typing.Self):
        return False

class Pawn(Piece):
    @property
    def icon(self: typing.Self):
        if self.color == Color.WHITE:
            return '♙'
        return '♟'
    
    def get_moves(self: typing.Self, board: Board):
        moves = []
        direction = 1 if self.color == Color.WHITE else -1
        if not board[self.position + (0, direction)]:
            moves.append(Move(self.position, self.position + (0, direction), self))
            if not self.moved and not board[self.position + (0, direction*2)]:
                moves.append(Move(self.position, self.position + (0, direction*2), self))
        for x in (-1, 1):
            pos = self.position + (x, direction)
            if pos.x <= 0 or pos.x > 8 or pos.y <= 0 or pos.y > 8:
                continue
            piece = board[pos]
            if piece.position != pos:
                continue
            if piece and piece.color != self.color:
                moves.append(Move(self.position, pos, self, piece))
        if direction == 1 and self.position.y == 7 or direction == -1 and self.position.y == 2:
            promotions = [Queen(self.color, self.position), Rook(self.color, self.position), Bishop(self.color, self.position), Knight(self.color, self.position)]
            for move in filter(lambda m: m.to_pos.y == self.position.y + direction, moves):
                for promotion in promotions:
                    move.promotion = promotion
        for x in (-1, 1):
            try:
                if isinstance(board[self.position + (x, -1*direction)], Pawn) and board[self.position + (x, -1*direction)].last_move and board[self.position + (x, -1*direction)].last_move.to_pos == self.position + (x, direction*2):
                    moves.append(Move(self.position, self.position + (x, 0), self, board[self.position + (x, -1*direction)]))
                    print("en passant")
            except OutOfBounds:
                pass
        return moves
    
class Rook(Piece):
    @property
    def icon(self: typing.Self):
        if self.color == Color.WHITE:
            return '♖'
        return '♜'
    
    def get_moves(self: typing.Self, board: Board):
        moves = []
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for i in range(max(board.size) + 2):
                pos = self.position + (direction[0]*i, direction[1]*i)
                if pos.x <= 0 or pos.x > 8 or pos.y <= 0 or pos.y > 8:
                    continue
                if board[pos]:
                    if board[pos].position != pos:
                        continue
                    if board[pos].color != self.color:
                        moves.append(Move(self.position, pos, self, board[pos]))
                    if board[pos] == self:
                        continue
                    break
                moves.append(Move(self.position, pos, self))
        return moves
    
class Knight(Piece):
    @property
    def icon(self: typing.Self):
        if self.color == Color.WHITE:
            return '♘'
        return '♞'
    
    def get_moves(self: typing.Self, board: Board):
        moves = []
        for direction in ((1, 2), (2, 1), (-1, 2), (2, -1), (-1, -2), (-2, -1), (1, -2), (-2, 1)):
            pos = self.position + direction
            if pos.x <= 0 or pos.x > 8 or pos.y <= 0 or pos.y > 8:
                continue
            if board[pos]:
                if board[pos].position != pos:
                    continue
                if board[pos].color != self.color:
                    moves.append(Move(self.position, pos, self, board[pos]))
                if board[pos] == self:
                    continue
                break
            moves.append(Move(self.position, pos, self))
        return moves
    
class Bishop(Piece):
    @property
    def icon(self: typing.Self):
        if self.color == Color.WHITE:
            return '♗'
        return '♝'
    
    def get_moves(self: typing.Self, board: Board):
        moves = []
        for direction in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            for i in range(max(board.size) + 2):
                pos = self.position + (direction[0]*i, direction[1]*i)
                if pos.x <= 0 or pos.x > 8 or pos.y <= 0 or pos.y > 8:
                    continue
                if board[pos]:
                    if board[pos].position != pos:
                        continue
                    if board[pos].color != self.color:
                        moves.append(Move(self.position, pos, self, board[pos]))
                        if board[pos] == self:
                            continue
                    break
                moves.append(Move(self.position, pos, self))
        return moves
    
class Queen(Piece):
    @property
    def icon(self: typing.Self):
        if self.color == Color.WHITE:
            return '♕'
        return '♛'
    
    def get_moves(self: typing.Self, board: Board):
        moves = []
        for direction in ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
            for i in range(max(board.size) + 2):
                pos = self.position + (direction[0]*i, direction[1]*i)
                if pos.x <= 0 or pos.x > 8 or pos.y <= 0 or pos.y > 8:
                    continue
                if board[pos]:
                    if board[pos].position != pos:
                        continue
                    if board[pos].color != self.color:
                        moves.append(Move(self.position, pos, self, board[pos]))
                    if board[pos] == self:
                        continue
                    break
                moves.append(Move(self.position, pos, self))
        return moves
    
class King(Piece):
    @property
    def icon(self: typing.Self):
        if self.color == Color.WHITE:
            return '♔'
        return '♚'
    
    def get_moves(self: typing.Self, board: Board):
        moves = []
        for direction in ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
            pos = self.position + direction
            if pos.x < 0 or pos.x > 8 or pos.y <= 0 or pos.y > 8:
                continue
            if board[pos]:
                if board[pos].position != pos:
                    continue
                if board[pos].color != self.color:
                    moves.append(Move(self.position, pos, self, board[pos]))
                if board[pos] == self:
                    continue
                break
            moves.append(Move(self.position, pos, self))

        # Castling
        if not self.moved:
            if not board[self.position + (1, 0)] and not board[self.position + (2, 0)] and isinstance(board[self.position + (3, 0)], Rook) and not board[self.position + (3, 0)].moved:
                moves.append(Move(self.position, self.position + (3, 0), self, related=[board[self.position + (3, 0)]]))
            if not board[self.position + (-1, 0)] and not board[self.position + (-2, 0)] and not board[self.position + (-3, 0)] and isinstance(board[self.position + (-4, 0)], Rook) and not board[self.position + (-4, 0)].moved:
                moves.append(Move(self.position, self.position + (-3, 0), self, related=[board[self.position + (-4, 0)]]))

        # TODO: check
        return moves
    
    def is_check(self: typing.Self, board: Board):
        for y in range(8):
            for x in range(8):
                if piece := board[Position(x, y)]:
                    if piece.color != self.color:
                        for move in piece.get_moves(board):
                            if move.taken == self:
                                return True
        return False

class InvalidMove(Exception):
    def __init__(self: typing.Self, move: Move, msg: str,*args: typing.Any, **kwargs: typing.Any):
        self.move = move
        super().__init__(f'{move}, {msg}', *args, **kwargs)

class OutOfBounds(Exception):
    def __init__(self: typing.Self, pos: Position, *args: typing.Any, **kwargs: typing.Any):
        self.pos = pos
        super().__init__(f'The position "{pos!r}" is out of bounds.', *args, **kwargs)

class Chess:
    
    def __init__(self: typing.Self):
        self.board = Board(True)
        self.board[Position('a', 1)] = Rook(Color.WHITE, Position('a', 1))
        self.board[Position('b', 1)] = Knight(Color.WHITE, Position('b', 1))
        self.board[Position('c', 1)] = Bishop(Color.WHITE, Position('c', 1))
        self.board[Position('d', 1)] = Queen(Color.WHITE, Position('d', 1))
        self.board[Position('e', 1)] = King(Color.WHITE, Position('e', 1))
        self.board[Position('f', 1)] = Bishop(Color.WHITE, Position('f', 1))
        self.board[Position('g', 1)] = Knight(Color.WHITE, Position('g', 1))
        self.board[Position('h', 1)] = Rook(Color.WHITE, Position('h', 1))
        for i in range(1,9):
            self.board[Position(i, 2)] = Pawn(Color.WHITE, Position(i, 2))
        self.board[Position('a', 8)] = Rook(Color.BLACK, Position('a', 8))
        self.board[Position('b', 8)] = Knight(Color.BLACK, Position('b', 8))
        self.board[Position('c', 8)] = Bishop(Color.BLACK, Position('c', 8))
        self.board[Position('d', 8)] = Queen(Color.BLACK, Position('d', 8))
        self.board[Position('e', 8)] = King(Color.BLACK, Position('e', 8))
        self.board[Position('f', 8)] = Bishop(Color.BLACK, Position('f', 8))
        self.board[Position('g', 8)] = Knight(Color.BLACK, Position('g', 8))
        self.board[Position('h', 8)] = Rook(Color.BLACK, Position('h', 8))
        for i in range(1,9):
            self.board[Position(i, 7)] = Pawn(Color.BLACK, Position(i, 7))
        self.turn = Color.WHITE
    
    def get_moves(self: typing.Self):
        moves = []
        for y in range(8):
            for x in range(8):
                if piece := self.board[Position(x, y)]:
                    if piece.color == self.turn:
                        moves.extend(piece.get_moves(self.board))
        return moves
    
    def poll_state(self: typing.Self):
        if not self.board.has_piece_type(King, Color.WHITE):
            return ("win", Color.BLACK)
        if not self.board.has_piece_type(King, Color.BLACK):
            return ("win", Color.WHITE)
        return ("playing", None)

    def make_move(self: typing.Self, move: Move):
        move = move.frozen()
        if not (err := self.validate_move(move))[0]:
            raise InvalidMove(repr(move), err[1])
        if move.taken:
            self.board[move.taken.position] = NullPiece(move.taken.position)
        self.board[move.to_pos] = move.piece
        self.board[move.from_pos] = NullPiece(move.from_pos)
        if move.promotion:
            self.board[move.to_pos] = move.promotion
        move.piece.moved = True
        move.piece.last_move = move.frozen()
        if isinstance(move.piece, King) and not move.piece.moved and move.related:
            if move.to_pos.x == 3:
                self.board[Position(1, move.to_pos.y)] = self.board[Position(4, move.to_pos.y)]
                self.board[Position(4, move.to_pos.y)] = NullPiece(Position(4, move.to_pos.y))
            if move.to_pos.x == 7:
                self.board[Position(8, move.to_pos.y)] = self.board[Position(6, move.to_pos.y)]
                self.board[Position(6, move.to_pos.y)] = NullPiece(Position(6, move.to_pos.y))
        self.pass_turn()

    def pass_turn(self: typing.Self):
        self.turn = Color.WHITE if self.turn == Color.BLACK else Color.BLACK

    def validate_move(self: typing.Self, move: Move):
        if move.piece.color != self.turn:
            return False, "wrong color"
        if move.taken and move.taken.color == move.piece.color:
            return False, "cannot take own piece"
        if (self.board[move.to_pos] and not move.taken) and not (move.related and move.related[0].position == move.to_pos):
            return False, "piece already at destination"
        if move.promotion and not isinstance(move.promotion, (Queen, Rook, Bishop, Knight)):
            return False, "invalid promotion"
        if move.piece.position != move.from_pos:
            return False, "piece position does not match move"
        if move.taken and move.to_pos != move.taken.position:
            return False, "taken piece position does not match move"
        return True, None

    def __str__(self: typing.Self):
        return str(self.board)
    
    def __repr__(self: typing.Self):
        return f'{self.__class__.__name__}({self.board!r})'
    
    def __copy__(self: typing.Self):
        new_game = self.__class__()
        new_game.board = copy.copy(self.board)
        new_game.turn = self.turn
        return new_game
        
import random

class Bot(abc.ABC):
    def __init__(self: typing.Self, color: Color):
        self.color = color

    @abc.abstractmethod
    def get_next_move(self: typing.Self, game: Chess):
        pass

    def run(self: typing.Self, other: typing.Any, rounds: int):
        import time, os
        z = 0
        
        wins = (0, 0)

        fps = 10
        delta = 0

        for i in range(rounds):
            game = Chess()
            x=0
            while True:
                if game.poll_state()[0] == "win":
                    wins = (wins[0]+1, wins[1]) if game.poll_state()[1] == self.color else (wins[0], wins[1]+1)
                    break
                start = time.time()
                try:
                    moves = game.get_moves()
                    x += 1
                    if not moves:
                        game.pass_turn()
                        continue
                    if game.turn == self.color:
                        game.make_move(self.get_next_move(game))
                    else:
                        game.make_move(other.get_next_move(game))
                    os.system('clear')
                    print("Round", str(i+1)+"/50", "| Moves:", x)
                    print("Wins:", wins)
                    print()
                    print(game)
                    print(f"FPS: {fps:.2f} | Delta: {delta:.2f}", end="\n")
                    time.sleep(max(delta,0))
                except Exception as err:
                    import traceback
                    traceback.print_exc()
                    return err
                end = time.time()
                fps = 1/(end-start)
                delta = (0.1 - 1/fps)
            z += x

        print("Average Moves:", z/rounds)
    
class RandomBot(Bot):
    def get_next_move(self: typing.Self, game: Chess):
        return random.choice(game.get_moves())



if __name__ == '__main__':
    RandomBot(Color.WHITE).run(RandomBot(Color.BLACK), 50)
        
        