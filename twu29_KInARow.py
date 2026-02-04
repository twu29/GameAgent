'''
twu29_KInARow.py
Authors: Wu, Alley; Cheng, Katharina

An agent for playing "K-in-a-Row with Forbidden Squares" and related games.
'''

from agent_base import KAgent
from game_types import State, Game_Type

AUTHORS = 'Alley Wu and Katharina Cheng' 
UWNETIDS = ['twu29', 'qiaoyc2']

import time # need this to avoid losing a
 # game due to exceeding a time limit.
import math
import os, random
import google.generativeai as genai


class OurAgent(KAgent):  # Keep the class name "OurAgent" so a game master
    # knows how to instantiate your agent class.

    def __init__(self, twin=False):
        self.twin=twin
        self.nickname = 'Kim K'
        if twin: self.nickname = 'Bob R'
        self.long_name = 'Kim Kardashian'
        if twin: self.long_name = 'Bob Ross'
        self.persona = 'Kim Kardashian'
        if twin: self.persona = 'Bob Ross'
        self.voice_info = {'Chrome': 10, 'Firefox': 2, 'other': 0}
        self.playing = "don't know yet" # e.g., "X" or "O".
        self.alpha_beta_cutoffs_this_turn = -1
        self.num_static_evals_this_turn = -1
        self.zobrist_table_num_entries_this_turn = -1
        self.zobrist_table_num_hits_this_turn = -1
        self.current_game_type = None
        self.playing_mode = KAgent.DEMO
        self.return_stats = False

    def introduce(self):
        name_display = self.long_name
        intro = (
            f"Hey bestie, it's {name_display}, your glam, unbothered, and maybe a little dramatic K-in-a-Row queen. "
            "Created by Alley Wu (twu29) and Katharina Cheng (qiaoyc2), fueled by couture, chaos, and lines of code that may or may not behave. "
            "I won't promise flawless gameplay… but like, I will promise iconic energy. Let's make some moves that look good even when they're bad.\n"
        )

        if self.twin:
            intro = (
                f"Hello friend, I'm {name_display}. "
                "While my another friend brings the sparkle and the drama, I bring peace, patience, and a happy little strategy brush. "
                "Let’s paint this board with calm, clever moves and see what beautiful mistakes we discover together.\n"
            )

        return intro


    # Receive and acknowledge information about the game from
    # the game master:
    def prepare(
        self,
        game_type,
        what_side_to_play,
        opponent_nickname,
        expected_time_per_move = 0.1, # Time limits can be
                                      # changed mid-game by the game master.

        utterances_matter=True):      # If False, just return 'OK' for each utterance,
                                      # or something simple and quick to compute
                                      # and do not import any LLM or special APIs.
                                      # During the tournament, this will be False..

        self.current_game_type = game_type
        self.playing = what_side_to_play
        self.opponent_nickname = opponent_nickname
        self.time_limit = expected_time_per_move
        self.utterances_matter = utterances_matter
        self.return_stats = os.getenv("A4_RETURN_STATS", "0") == "1"

        print(f"Preparing {self.long_name} ({self.nickname})...")
        print(f"Side: {self.playing}, Opponent: {self.opponent_nickname}")
        print(f"Time per move: {self.time_limit}s")
        
        if utterances_matter:
            try:
                self.genai_model = genai.GenerativeModel("models/gemini-2.5-flash")
                print("Gemini model loaded successfully for utterances.")
            except Exception as e:
                print(f"Gemini load failed: {e}")
                print("Fallback to local utterances.")
                self.genai_model = None
        else:
            self.genai_model = None
            print("LLM disabled, using simple utterances.")

        # Reset stats
        self.alpha_beta_cutoffs_this_turn = -1
        self.num_static_evals_this_turn = -1
        self.zobrist_table_num_entries_this_turn = -1
        self.zobrist_table_num_hits_this_turn = -1

        print("Preparation complete.")
        return "OK"

    def generate_utterance(self, state, move, opponent_remark, eval_score=None):
        board_str = "\n".join(["".join(row) for row in state.board])

        # interpret the eval score into words
        if eval_score is not None:
            if eval_score > 50:
                game_status = "You're winning comfortably!"
            elif eval_score > 10:
                game_status = "You're slightly ahead."
            elif eval_score > -10:
                game_status = "It's pretty even right now."
            elif eval_score > -50:
                game_status = "You're falling behind!"
            else:
                game_status = "You're in big trouble!"
        else:
            game_status = "No score info available."

        if not self.twin:
            prompt = f"""
                You are {self.persona}, a glam, dramatic, slightly mean gamer named {self.long_name}.
                Think Kim Kardashian energy—confident, cutting, dramatic, iconic.

                You MAY use or remix her classic sayings, such as:
                - I'm doing amazing, sweetie.
                - This is so embarrassing.
                - Like, literally.
                - Don't be rude.
                But DO NOT repeat the same one every turn.

                You're playing K-in-a-Row (like Tic Tac Toe).

                Current board:
                {board_str}

                Game update: {game_status}

                You just played move {move}.
                Your opponent said: "{opponent_remark}".

                Respond with EXACTLY two sentences on ONE line (max 50 words total).
                Make it iconic, sassy, and lightly mean, like a reality TV clapback.
                Do NOT use quotation marks.
                Do NOT add line breaks.
                Avoid non-ASCII characters.
                """
        else:
            prompt = f"""
                You are {self.persona}, a calm, kind, grounded gamer named {self.long_name}.
                Think Bob Ross energy—warm, peaceful, gentle, encouraging.

                You MAY use or adapt his classic sayings, such as:
                - Happy little accidents.
                - We don't make mistakes.
                - Let's have some fun.
                But DO NOT repeat the same one every turn.

                You're playing K-in-a-Row (like Tic Tac Toe).

                Current board:
                {board_str}

                Game update: {game_status}

                You just played move {move}.
                Your opponent said: "{opponent_remark}".

                Respond with EXACTLY two gentle sentences on ONE line (max 50 words total).
                Keep it warm, steady, and positive.
                Do NOT use quotation marks.
                Do NOT add line breaks.
                Avoid non-ASCII characters.
                """
        try:
            if self.genai_model:
                response = self.genai_model.generate_content(prompt)
                return response.text.strip()
            else:
                # fallback if not configured
                raise RuntimeError("Gemini not available.")
        except Exception as e:
            print("Gemini utterance generation failed:", e)
            if not self.twin:
                fallback_lines = [
                    f"My move is {move}! Not saying it's genius... but it might be",
                    f"{move} - because chaos *is* strategy.",
                    f"GG-Bot dropping {move}. Don't tilt now",
                    f"Played {move}. If this fails, blame my twin",
                    f"{move}! A bold move from a bold bot.",
                ]
            else:
                fallback_lines = [
                    f"Played {move}. Staying patient - strategy over impulse.",
                    f"{move}. Calm and calculated.",
                    f"Taking {move}. No rush, just control.",
                    f"{move}. Sometimes the quiet move hits hardest.",
                    f"Placed at {move}. Let's keep it steady.",
                ]
            return random.choice(fallback_lines)
   
    # The core of your agent's ability should be implemented here:             
    def make_move(self, current_state, current_remark, time_limit=1000,
                  use_alpha_beta=True,
                  use_zobrist_hashing=False, max_ply=3,
                  special_static_eval_fn=None):
        print("make_move has been called")
        
        start_time = time.time()
        if time_limit is None:
            deadline = None
        else:
            safe_time = time_limit * 0.98 # leave 2% small safety buffer
            safe_time = max(0.0, safe_time) # make sure the number is not negative
            deadline = start_time + safe_time

        # print("code to compute a good move should go here.")

        # Clears all the counters from last turn
        if use_alpha_beta:
            self.alpha_beta_cutoffs_this_turn = 0
        else:
            self.alpha_beta_cutoffs_this_turn = -1

        self.num_static_evals_this_turn = 0
        self.zobrist_table_num_entries_this_turn = -1
        self.zobrist_table_num_hits_this_turn = -1

        best_move = None
        best_state = None
        if current_state.whose_move == 'X':
            best_value = -math.inf
        else:
            best_value = math.inf
            
        # Root-level alpha and beta for pruning
        root_alpha = -math.inf
        root_beta = math.inf

        move_list = []

        if special_static_eval_fn is None:
            #  ROOT-LEVEL CHILD ORDERING (one-ply static_eval)
            scored_moves = []
            for r, row in enumerate(current_state.board):
                for c, cell in enumerate(row):
                    if cell == ' ':
                        child = State(old=current_state)
                        child.board[r][c] = current_state.whose_move
                        child.change_turn()
                        score = self.static_eval(child)   # one-ply heuristic
                        scored_moves.append(((r, c), score, child))

            descending = (current_state.whose_move == 'X')  # Max wants higher first
            scored_moves.sort(key=lambda t: t[1], reverse=descending)

            move_list = [(move, child) for (move, _score, child) in scored_moves]
        else:
            #  NO ROOT ORDERING 
            for r, row in enumerate(current_state.board):
                for c, cell in enumerate(row):
                    if cell == ' ':
                        child = State(old=current_state)
                        child.board[r][c] = current_state.whose_move
                        child.change_turn()
                        move_list.append(((r, c), child))

        for (move, child) in move_list:
            if deadline is not None and time.time() >= deadline:
                print("Time's up!")
                break

            # Use shared alpha/beta across all root children
            if use_alpha_beta:
                value = self.minimax(
                    child,
                    depth_remaining=max_ply - 1,
                    pruning=True,
                    alpha=root_alpha,
                    beta=root_beta,
                    deadline=deadline,
                    order_children=True,
                    special_static_eval_fn=special_static_eval_fn
                )

                # update root alpha/beta for pruning at root
                if current_state.whose_move == 'X':
                    root_alpha = max(root_alpha, value)
                else:
                    root_beta = min(root_beta, value)
            else:
                value = self.minimax(
                    child,
                    depth_remaining=max_ply - 1,
                    pruning=False,
                    alpha=None,
                    beta=None,
                    deadline=deadline,
                    order_children=True,
                    special_static_eval_fn=special_static_eval_fn
                )

            if current_state.whose_move == 'X':
                if best_move is None or value > best_value:
                    best_value, best_move, best_state = value, move, child
            else:
                if best_move is None or value < best_value:
                    best_value, best_move, best_state = value, move, child

        
        # If no move was chosen (time ran out or no legal moves), pick a safe default
        if best_move is None:
            legal_moves = [(r, c)
                           for r, row in enumerate(current_state.board)
                           for c, cell in enumerate(row)
                           if cell == ' ']
            if not legal_moves:
                # No legal moves at all
                return [None, "No legal moves."]
         
            best_move = legal_moves[0]
            best_state = State(old=current_state)
            r, c = best_move
            best_state.board[r][c] = current_state.whose_move
            best_state.change_turn()

        new_remark = self.generate_utterance(
            current_state, best_move, current_remark, eval_score=best_value
        )

        inner = [best_move, best_state]
        if self.return_stats:
            inner += [
                self.alpha_beta_cutoffs_this_turn,
                self.num_static_evals_this_turn,
                self.zobrist_table_num_entries_this_turn,
                self.zobrist_table_num_hits_this_turn,
            ]
        return [inner, new_remark]

    # The main adversarial search function:
    def minimax(self,
            state,
            depth_remaining,
            pruning=False,
            alpha=None,
            beta=None,
            deadline=None,
            order_children=False,
            special_static_eval_fn=None):
        # print("Calling minimax. We need to implement its body.")

        default_score = 0 # Value of the passed-in state. Needs to be computed.

        # base case
        if depth_remaining == 0 or (deadline is not None and time.time() >= deadline):
            self.num_static_evals_this_turn += 1
            if special_static_eval_fn is not None:
                return special_static_eval_fn(state)
            return self.static_eval(state)

        # set up best value
        player = state.whose_move
        max_play = (player == 'X')

        # initialize best value
        if max_play:
            best_value = -math.inf
        else:
            best_value = math.inf

        # build children
        children = []
        board = state.board
        for r, row in enumerate(board):
            for c, cell in enumerate(row):
                if cell != ' ':
                    continue
                child = State(old=state)
                child.board[r][c] = player
                child.change_turn()
                if order_children:
                    score = self.static_eval(child)
                    children.append(((r, c), child, score))
                else:
                    children.append(((r, c), child, None))

        # order by heuristic if requested (Max high->low, Min low->high)
        if order_children and children:
            children.sort(key=lambda t: t[2], reverse=max_play)

        # recurse over children
        for (move, child, _score) in children:
            value = self.minimax(
                child,
                depth_remaining=depth_remaining - 1,
                pruning=pruning,
                alpha=alpha,
                beta=beta,
                deadline=deadline,
                order_children=order_children,
                special_static_eval_fn=special_static_eval_fn
            )

            if max_play:
                if value > best_value:
                    best_value = value
                if pruning:
                    if best_value > alpha:
                        alpha = best_value
            else:
                if value < best_value:
                    best_value = value
                if pruning:
                    if best_value < beta:
                        beta = best_value

            if pruning and alpha is not None and beta is not None and alpha >= beta:
                self.alpha_beta_cutoffs_this_turn += 1
                return best_value

        return best_value
 
    def static_eval(self, state, game_type=None):
        # print('calling static_eval. Its value needs to be computed!')

        if game_type is None:
            game_type = self.current_game_type

        board = state.board
        n = len(board)
        m = len(board[0])
        total = 0
        k = game_type.k

         # horizontal
        for r in range(n):
            for c in range(m - k + 1):
                line = [board[r][c + i] for i in range(k)]
                total += self._score_line(line)

        # vertical
        for c in range(m):
            for r in range(n - k + 1):
                line = [board[r + i][c] for i in range(k)]
                total += self._score_line(line)

        # top left to bottom right
        for r in range(n - k + 1):
            for c in range(m - k + 1):
                line = [board[r + i][c + i] for i in range(k)]
                total += self._score_line(line)

        # bottom left to top right
        for r in range(k - 1, n):
            for c in range(m - k + 1):
                line = [board[r - i][c + i] for i in range(k)]
                total += self._score_line(line)
        
        return float(total)

    # Helper function: to score a single line 
    def _score_line(self, cells):
        count_x = cells.count('X')
        count_o = cells.count('O')

        # blocked if both players appear
        if count_x > 0 and count_o > 0:
            return 0

        # all empty: no value
        if count_x == 0 and count_o == 0:
            return 0
    
        # if only Xs
        if count_o == 0 and count_x > 0:
            return 10 ** (count_x - 1)
        # if only Os
        if count_x == 0 and count_o > 0:
            return -(10 ** (count_o - 1))

def test_child_ordering_variants():
    from game_types import FIAR
    from time import time as now
    import math

    agent = OurAgent()
    # disable LLM side-effects + include stats in make_move return
    agent.prepare(FIAR, 'X', 'Opponent', utterances_matter=False)
    agent.return_stats = True
    s = FIAR.initial_state

    # No-AB
    agent.num_static_evals_this_turn = 0
    agent.alpha_beta_cutoffs_this_turn = 0
    t0 = now()
    _ = agent.minimax(s, depth_remaining=3, pruning=False, order_children=False)
    t1 = now()
    noab_evals = agent.num_static_evals_this_turn
    print(f"[NO-AB] evals={noab_evals}, time={t1-t0:.3f}s")

    # UNORDERED+AB (minimax directly)
    agent.num_static_evals_this_turn = 0
    agent.alpha_beta_cutoffs_this_turn = 0
    t2 = now()
    _ = agent.minimax(s, depth_remaining=3, pruning=True,
                      alpha=-math.inf, beta=math.inf,
                      order_children=False)
    t3 = now()
    unordered_evals = agent.num_static_evals_this_turn
    unordered_cuts  = agent.alpha_beta_cutoffs_this_turn
    print(f"[UNORDERED+AB] evals={unordered_evals}, cutoffs={unordered_cuts}, time={t3-t2:.3f}s")

    # ROOT-ORDER+AB (via make_move)
    t4 = now()
    inner, _ = agent.make_move(s, current_remark="", time_limit=None,
                               use_alpha_beta=True, max_ply=3)
    t5 = now()
    # Because return_stats=True, inner = [best_move, best_state, cutoffs, evals, z_entries, z_hits]
    _, _, root_cuts, root_evals, _, _ = inner
    print(f"[ROOT-ORDER+AB] evals={root_evals}, cutoffs={root_cuts}, time={t5-t4:.3f}s")

    # FULL-ORDER+AB (minimax-level ordering)
    agent.num_static_evals_this_turn = 0
    agent.alpha_beta_cutoffs_this_turn = 0
    t6 = now()
    _ = agent.minimax(s, depth_remaining=3, pruning=True,
                      alpha=-math.inf, beta=math.inf,
                      order_children=True)
    t7 = now()
    full_evals = agent.num_static_evals_this_turn
    full_cuts  = agent.alpha_beta_cutoffs_this_turn
    print(f"[FULL-ORDER+AB] evals={full_evals}, cutoffs={full_cuts}, time={t7-t6:.3f}s")

    # summary vs NO-AB
    def pct(saved, base): return (saved / base * 100.0) if base else 0.0

    saved_unordered = noab_evals - unordered_evals
    saved_root      = noab_evals - root_evals
    saved_full      = noab_evals - full_evals

    print(f"Saved by AB (unordered): {saved_unordered} ({pct(saved_unordered, noab_evals):.1f}% fewer)")
    print(f"Saved by AB (root-ordered): {saved_root} ({pct(saved_root, noab_evals):.1f}% fewer)")
    print(f"Saved by AB (full-ordered): {saved_full} ({pct(saved_full, noab_evals):.1f}% fewer)")


    
#if __name__ == '__main__':
    #test_child_ordering_variants()

# OPTIONAL THINGS TO KEEP TRACK OF:

#  WHO_MY_OPPONENT_PLAYS = other(WHO_I_PLAY)
#  MY_PAST_UTTERANCES = []
#  OPPONENT_PAST_UTTERANCES = []
#  UTTERANCE_COUNT = 0
#  REPEAT_COUNT = 0 or a table of these if you are reusing different utterances
