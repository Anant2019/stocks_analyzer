def solve_n_queens(n):
    board = [['.' for _ in range(n)] for _ in range(n)]
    results = []
    steps = [] # To store backtracking trace

    def is_safe(row, col):
        for i in range(row):
            if board[i][col] == 'Q': return False
        for i, j in zip(range(row-1, -1, -1), range(col-1, -1, -1)):
            if board[i][j] == 'Q': return False
        for i, j in zip(range(row-1, -1, -1), range(col+1, n)):
            if board[i][j] == 'Q': return False
        return True

    def backtrack(row):
        steps.append({
            "description": f"Exploring row {row}",
            "board": [row[:] for row in board],
            "is_backtracking": False
        })

        if row == n:
            results.append(["".join(r) for r in board])
            return

        for col in range(n):
            if is_safe(row, col):
                board[row][col] = 'Q'
                backtrack(row + 1)
                board[row][col] = '.' # Backtrack
                
                steps.append({
                    "description": f"Backtracking from row {row}, col {col}",
                    "board": [row[:] for row in board],
                    "is_backtracking": True
                })

    backtrack(0)
    return results, steps
