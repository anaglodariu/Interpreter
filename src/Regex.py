from .NFA import NFA
from dataclasses import dataclass
from collections import deque
import string
EPSILON = ''

class Regex:
    def __init__(self, regex: str):
        self.regex = deque(regex)
    
    def thompson(self) -> NFA[int]:
        raise NotImplementedError('the thompson method of the Regex class should never be called')

    # for parsing [a-z], [A-Z], [0-9]
    # [a-z] is equivalent to a|b|c|...|z
    # so we apply the union operation on all the characters
    def parse_syntactic_sugar(self, sugar : str) -> 'Regex':
        i = 0
        union = Union(Character(sugar[i]), Character(sugar[i+1]))
        i += 2
        while i < len(sugar):
            # union the characters
            union = Union(union, Character(sugar[i]))
            i += 1
        return union

    def parse_round_brackets(self) -> 'Regex':
        self.regex.popleft() # pop the '('
        # parse the regex inside the round brackets recursively
        parsed_regex = self.parse_union()
        self.regex.popleft() # pop the ')'
        return parsed_regex

    def parse_square_brackets(self) -> 'Regex':
        self.regex.popleft() # pop the '['
        # create a set of characters
        char_start = self.regex.popleft()
        #self.regex.popleft() # pop the '-'
        #self.regex.popleft() # pop the end character
        #self.regex.popleft() # pop the ']'
        for i in range(3):
            self.regex.popleft()
        
        if char_start.isalpha():
            if char_start.islower():
                set_char = string.ascii_lowercase
            else:
                set_char = string.ascii_uppercase
        elif char_start.isdigit():
            set_char = "0123456789"

        return self.parse_syntactic_sugar(set_char)

    def parse_concat_parts(self):
        # if the first character is a '('
        if self.regex[0] == '(':
            return self.parse_round_brackets()
        elif self.regex[0] == '[':
            return self.parse_square_brackets()
        # if the character is \
        elif self.regex[0] == '\\':
            self.regex.popleft()
            return Character(self.regex.popleft())
        else:
            return Character(self.regex.popleft())
            
    # operations *, +, ? have the highest priority
    def parse_operations(self, op_on_regex) -> 'Regex':
        if self.regex == deque([]):
            return op_on_regex
        # if the first character is a '*'
        elif self.regex[0] == '*':
            self.regex.popleft() # pop the '*'
            return Star(op_on_regex)
        # if the first character is a '+'
        elif self.regex[0] == '+':
            self.regex.popleft() # pop the '+'
            # return the concatenation of the regex and
            # the star of the regex, because the regex
            # has to appear at least once
            return Concat(op_on_regex, Star(op_on_regex))
        # if the first character is a '?'
        elif self.regex[0] == '?':
            self.regex.popleft() # pop the '?'
            # return the union of the regex and epsilon regex because
            # the regex can appear once or not at all
            return Union(op_on_regex, Epsilon())
        return op_on_regex

    def parse_concat(self) -> 'Regex':
        left_part = self.parse_concat_parts()
        left_part = self.parse_operations(left_part)
        while self.regex != deque([]) and self.regex[0] not in {'|', ')'}:
            right_part = self.parse_concat_parts()
            right_part = self.parse_operations(right_part)
            left_part = Concat(left_part, right_part)
        
        return left_part
        
    # union has the lowest priority
    # <left part> | <right part>
    def parse_union(self) -> 'Regex':
        # parse the right part of the regex recursively
        left_part = self.parse_concat()
        # until we reach a union separator or the end of the regex
        while self.regex != deque([]) and self.regex[0] == '|':
            self.regex.popleft() # pop the '|'
            # parse the left part of the regex recursively
            right_part = self.parse_concat()
            # create a union of the left and right parts
            left_part = Union(left_part, right_part)
        return left_part

def eliminate_spaces(regex: str) -> str:
    # eliminate spaces from the regex
    regex = regex.replace('\\ ', '\\s').replace(' ', '').replace('\\s', '\\ ')
    return regex

@dataclass
class Epsilon(Regex):

    def thompson(self) -> NFA[int]:
        return NFA({}, {0}, 0, {}, {0})

@dataclass
class Star(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        nfa = self.regex.thompson()

        # a new initial state {0} needs to be added
        # all the states in nfa will be incremented by 1
        nfa = NFA.remap_states(nfa, lambda x: x + 1)

        old_initial_state = nfa.q0
        old_final_state = nfa.F.pop()
        
        # set the new initial state to be {0}
        nfa.q0 = 0

        # add the new initial state {0}
        nfa.K.add(nfa.q0)

        # add epsilon transition from the old final state of the nfa to the old initial state of the nfa
        # add epsilon transition from the old final state of the nfa to a new final state {nr_states_nfa}
        nr_states_nfa = len(nfa.K)
        nfa.d[(old_final_state, EPSILON)] = {old_initial_state, nr_states_nfa}

        # the new final state {nr_states_nfa} needs to be added
        nfa.K.add(nr_states_nfa)
        nfa.F.add(nr_states_nfa)

        # add epsilon transition from the new initial state {0} to the old initial state of the nfa
        # add epsilon transition from the new initial state {0} to the new final state
        nfa.d[(nfa.q0, EPSILON)] = {old_initial_state, nr_states_nfa}

        return nfa
    

@dataclass
class Union(Regex):
    regex1: Regex
    regex2: Regex

    def thompson(self) -> NFA[int]:
        nfa1 = self.regex1.thompson()
        nfa2 = self.regex2.thompson()

        old_initial_state_nfa1 = nfa1.q0
        old_final_state_nfa1 = nfa1.F.pop()

        # if the first nfa was already a reunion of two nfa's, we don't need to add a new initial state and
        # a new final state
        # if there an epsilon transition from the old initial state of the first nfa to the old final state of the first nfa
        isunion = nfa1.d.get((old_initial_state_nfa1, EPSILON), set())
        if isunion != set() and old_final_state_nfa1 not in isunion:
            nfa2 = NFA.remap_states(nfa2, lambda x: x + len(nfa1.K))

            old_initial_state_nfa2 = nfa2.q0

            old_final_state_nfa2 = nfa2.F.pop()

            nfa1.F.add(old_final_state_nfa1) # the old final state remains final
            # we add on top to the transition function of the first nfa an epsilon transition from the old initial state
            # to the old initial state of the second nfa
            old_value_d = nfa1.d.get((old_initial_state_nfa1, EPSILON), set())
            old_value_d.add(old_initial_state_nfa2)
            nfa1.d[(old_initial_state_nfa1, EPSILON)] = old_value_d

            # add an epsilon transition from old final state of the second nfa to the old final state of
            # the first nfa
            nfa1.d[(old_final_state_nfa2, EPSILON)] = {old_final_state_nfa1}

            # merge the alphabet of the two nfa's
            nfa1.S.update(nfa2.S)

            # merge the set of states of the two nfa's
            nfa1.K.update(nfa2.K)

            # merge the transition functions of the two nfa's
            nfa1.d.update(nfa2.d)

            return nfa1

        nfa1.F.add(old_final_state_nfa1)
        
        nfa1 = NFA.remap_states(nfa1, lambda x: x + 1)
        nfa2 = NFA.remap_states(nfa2, lambda x: x + len(nfa1.K) + 1)

        old_initial_state_nfa1 = nfa1.q0
        old_initial_state_nfa2 = nfa2.q0

        old_final_state_nfa1 = nfa1.F.pop()
        old_final_state_nfa2 = nfa2.F.pop()
        
        # save the new nfa into nfa1
        # merge the alphabet of the two nfa's
        nfa1.S.update(nfa2.S)

        # merge the set of states of the two nfa's
        nfa1.K.update(nfa2.K)

        # merge the transition functions of the two nfa's
        nfa1.d.update(nfa2.d)

        # add a new initial state {0} and new final state {nr_states_nfa1 + nr_states_nfa2 + 1}
        nfa1.q0 = 0
        nfa1.K.add(nfa1.q0)
        new_final_state = len(nfa1.K)
        nfa1.K.add(new_final_state)
        nfa1.F.add(new_final_state)

        # add epsilon transitions from the new initial state {0} to the old initial states 
        # of the two nfa's
        nfa1.d[(nfa1.q0, EPSILON)] = {old_initial_state_nfa1, old_initial_state_nfa2}

        # add epsilon transitions from the old final states of the two nfa's to the new final state
        nfa1.d[(old_final_state_nfa1, EPSILON)] = {new_final_state}
        nfa1.d[(old_final_state_nfa2, EPSILON)] = {new_final_state}

        return nfa1

    
@dataclass
class Concat(Regex):
    regex1: Regex
    regex2: Regex

    def thompson(self) -> NFA[int]:
        nfa_left = self.regex1.thompson()
        nfa_right = self.regex2.thompson()

        nr_states_nfa_left = len(nfa_left.K)
        nfa_right = NFA.remap_states(nfa_right, lambda x: x + nr_states_nfa_left)

        # we merge the transition functions of the two nfa's
        nfa_left.d.update(nfa_right.d)
        
        # we merge the alphabet of the two nfa's
        nfa_left.S.update(nfa_right.S)

        # we merge the set of states of the two nfa's
        nfa_left.K.update(nfa_right.K)

        # add a new epsilon transition from the final state 
        # of the left nfa to the start state of the right nfa
        # also the final state of the left nfa is no longer final
        # and the initial state of the right nfa in no longer initial
        nfa_left.d[(nfa_left.F.pop(), EPSILON)] = {nfa_right.q0}

        # we merge the set of final states of the two nfa's
        nfa_left.F.update(nfa_right.F)
        # the initial state after concatenation is the initial state of the left nfa
        # the final state after concatenation is the final state of the right nfa
        return nfa_left
        

@dataclass
class Character(Regex):
    character: str

    def thompson(self) -> NFA[int]:
        # this function gets a Character object and returns an NFA
        return NFA({self.character}, {0, 1}, 0, {(0, self.character): {1}}, {1})


def parse_regex(regex: str) -> Regex:
    # create a Regex object by parsing the string
    regex = eliminate_spaces(regex)
    parsed_regex = Regex(regex)
    return parsed_regex.parse_union()
