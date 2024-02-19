from src.NFA import NFA
from src.Regex import parse_regex
EPSILON = ''

class Lexer:
    # function that merges 2 nfas into one
    def merge_nfas(self, nfa1: NFA, nfa2: NFA) -> None:
        # merge the alphabet of the 2 nfas
        nfa1.S = nfa1.S.union(nfa2.S)
        # merge the set of states of the 2 nfas
        nfa1.K = nfa1.K.union(nfa2.K)
        # merge the transition functions of the 2 nfas
        nfa1.d.update(nfa2.d)
        # merge the final states of the 2 nfas
        nfa1.F = nfa1.F.union(nfa2.F)
        # add to the transition function the epsilon transition 
        # from the initial state in nf1 to the initial state in nfa2
        nfa1.d[(0, EPSILON)].add(nfa2.q0)



    def __init__(self, spec: list[tuple[str, str]]) -> None:
        # initialisation should convert the specification to a dfa which will be used in the lex method
        # the specification is a list of pairs (TOKEN_NAME:REGEX)

        # for remapping states so they don't have the same name
        offset_of_states = 0

        # create a new nfa by merging all the nfas of the regex from the specification
        # the new nfa will have the initial state 0
        new_nfa = NFA(set(), set(), 0, dict(), set())
        new_nfa.d[(0, EPSILON)] = set()

        # turn each regex from spec into an nfa
        for token, regex in spec:
            # create nfa from regex
            nfa = parse_regex(regex).thompson()
            
            # remap states to avoid name conflicts
            nfa = nfa.remap_states(lambda x: x + offset_of_states + 1)

            # remap only the final states so that the name of the token is also included
            # this way we know which token was accepted
            nfa = nfa.remap_states(lambda x: (token, x) if x in nfa.F else x)
            
            # merge nfa into the new nfa
            self.merge_nfas(new_nfa, nfa)

            offset_of_states += len(nfa.K)

        # convert new nfa to dfa
        self.dfa = new_nfa.subset_construction()

        # put the token names in order in a list for finding the first maximal match later
        self.token_order = [token for token, _ in spec]

    # function for error 1
    # when we have an invalid character and lexer can't accept more characters
    def error1(self, index: int, line: int) -> list[tuple[str, str]]:
        return [("", "No viable alternative at character " + str(index) + ", line " + str(line))]
    
    # determine the line and column of the error
    def create_error1(self, word_list: list[str], word: str, i: int) -> list[tuple[str, str]]:
        char_count = len(word)
        lines_in_total = word.count('\n')
        lines_left = word_list[i:].count('\n')
        pos_last_newline = self.find_nth(word, '\n', lines_in_total - lines_left) if lines_in_total != lines_left else -1
        char_count_left = len(word_list[i:])
        index = char_count - char_count_left - pos_last_newline - 1 if pos_last_newline != -1 else char_count - char_count_left
        return self.error1(index, lines_in_total - lines_left)

    # function for error 2
    # when we get to the end of the word but the lexer can still accept more characters
    def error_eof(self, line: int) -> None:
        return [("", "No viable alternative at character EOF, line " + str(line))]

    # function that finds a certain occurence of newline in a string
    def find_nth(self, string: str, char: str, n: int) -> int:
        start = string.find(char)
        n -= 1
        while start >= 0 and n > 0:
            start = string.find(char, start + len(char))
            n -= 1
        return start
        
    def lex(self, word: str) -> list[tuple[str, str]] | None:
        # this method splits the lexer into tokens based on the specification and the rules described in the lecture
        # the result is a list of tokens in the form (TOKEN_NAME:MATCHED_STRING)
        
        # make the word a list of characters
        word_list = list(word)

        # initialize the next state with the initial state
        next_state = self.dfa.q0

        # the last time a token was accepted
        last_time_it_accepted = 0

        i = 0
        token_list = []
        possible_pair = ()
        was_in_final_state = False
        # number of total \n in the word
        lines_in_total = word.count('\n')

        while i < len(word_list):
            # get next state on the current character
            next_state = self.dfa.d.get((next_state, word_list[i]), None)

            # if the next state is None, it means the character is not in the spec
            if next_state is None:
                print('sth')
                print(word_list[i])
                return self.create_error1(word_list, word, i)
            
            # if the next state is final, we save the token name and the matched string
            # but we continue to check if there is a longer match
            if next_state in self.dfa.F:
                was_in_final_state = True

                # filter only the tuples in the frozenset so we get the
                # final states of the nfas
                tokens = list(filter(lambda x: isinstance(x, tuple), next_state))
                
                # get the token with the lowest index in spec
                min_token = min(tokens, key=lambda x: self.token_order.index(x[0]))

                # save the last time a token was accepted
                last_time_it_accepted = i
                i += 1
                # we got into a final state, so we save the token name and the matched string
                possible_pair = (min_token[0], ''.join(word_list[:i]))

                # if we get to the end of the word and we are in a final state
                # we add the tuple to the list
                if i == len(word_list):
                    token_list.append(possible_pair)
                    break
            
            # if the next state is the sink state
            elif next_state == frozenset():
                # if we had not been in a final state before, we return an error
                # because no token was accepted
                if not was_in_final_state:
                    #print(word_list[i])
                    return self.create_error1(word_list, word, i)
                
                # reset the flag
                was_in_final_state = False

                # reset the next state to the initial state
                next_state = self.dfa.q0

                # reset the word list to the index of the last time a token was accepted
                word_list = word_list[last_time_it_accepted + 1:]

                i = 0

                # if we had been in a final state, we add the token accepted to the list
                if possible_pair:
                    token_list.append(possible_pair)
                    possible_pair = ()
            # if the next state is not final or the sink state, we continue
            else:
                i += 1
                # if we get to the end of the world and we are not in a final state
                # we return an error
                if i == len(word_list):
                    return self.error_eof(lines_in_total)
        
        return token_list
