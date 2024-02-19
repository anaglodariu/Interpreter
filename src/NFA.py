from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable
# import deque for the epsilon closure function because it is faster than a list
from collections import deque

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs


@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def eps_helper(self, queue: deque[STATE], eps_closure: set[STATE]) -> None:
        # if the queue is empty, recursion ends and the eps_closure set is returned
        if queue == deque([]):
            return None
        # pop the first element from the queue
        current_state = queue.popleft()
        # get the next states on the EPSILON character from the transition function
        next_states = self.d.get((current_state, EPSILON), set())
        # add next states set to the end of the queue
        for next_state in next_states:
            # if the next state is not already in the eps_closure set
            # add it to the queue
            if next_state not in eps_closure:
                queue.append(next_state)
                # add the new state to the eps_closure set
                eps_closure.add(next_state)
        # recursively call the helper function with the updated queue 
        # and eps_closure set
        self.eps_helper(queue, eps_closure)

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        # compute the epsilon closure of a state (you will need this for subset construction)
        # see the EPSILON definition at the top of this file

        # eps closure contains the state itself in the beginning
        eps_closure = {state}
        queue = deque([state])
        # the helper function will create the eps_closure set recursively
        # the queue is what tells the helper function when to stop the recursion
        self.eps_helper(queue, eps_closure)
    
        return eps_closure
    
    # helper function for subset construction
    def subset_helper(self, 
                      queue: deque[frozenset[STATE]], 
                      dfa_K: set[frozenset[STATE]], 
                      dfa_d: dict[tuple[frozenset[STATE], str], frozenset[STATE]], 
                      dfa_F: set[frozenset[STATE]]) -> None:
        # if the queue is empty, then the recursion ends
        # it means that there are no more states to add to the DFA
        if queue == deque([]):
            return None

        # pop the first state from the queue
        current_state = queue.popleft()

        # if there is at least one final state from the NFA into the new current set of states of the DFA
        # then the current set of states of the DFA is a final state
        for states in current_state:
            if states in self.F:
                dfa_F.add(current_state)
                break
        
        # for each character in the alphabet of the NFA
        for character in self.S:
            next_states = set()
            aux = set()

            # for each state in the current set of states of the DFA
            for states in current_state:
                # get the next set of states for each 'states' on 'character' from the transition function of the NFA
                next_states = next_states.union(self.d.get((states, character), set()))
                # save the result in aux
                aux = next_states
            
            # for each state in the next states set, calculate the epsilon closure
            for states in aux:
                next_states = next_states.union(self.epsilon_closure(states))
            
            # the union of all the set of states is the set of next states for the current state on 'character'
            all_next_states = frozenset(next_states)
            
            # in the case all_next_states == frozenset(), then the transition function of the NFA is not defined
            # but, because a DFA must have a transition function for each state and character,
            # the frozenset() will become a sink state
            dfa_d[(current_state, character)] = all_next_states

            # if the next states set is not already in the set of states of the DFA
            # then add the new set of states to the queue
            if all_next_states not in dfa_K:
                queue.append(all_next_states)
                # add the the new set of states to the set of states of the DFA
                dfa_K.add(all_next_states)

        self.subset_helper(queue, dfa_K, dfa_d, dfa_F)

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        # convert this nfa to a dfa using the subset construction algorithm

        # initialize all the fields of the DFA
        # the alphabet of the DFA is the same as the alphabet of the NFA
        dfa_S = self.S
        dfa_F = set()
        dfa_K = set()
        dfa_d = dict()
        queue = deque()

        # the start state of the DFA is the epsilon closure of the start state of the NFA
        dfa_q0 = frozenset(self.epsilon_closure(self.q0))
        # add it to the set of states of the DFA
        dfa_K.add(dfa_q0)

        # add the start state to the queue
        queue.append(dfa_q0)

        # call the recursive helper function
        self.subset_helper(queue, dfa_K, dfa_d, dfa_F)
        
        return DFA(dfa_S, dfa_K, dfa_q0, dfa_d, dfa_F)

    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        # optional, but may be useful for the second stage of the project. Works similarly to 'remap_states'
        # from the DFA class. See the comments there for more details.
        
        # go through all the states and apply f to them
        other_K = {f(state) for state in self.K}

        # apply f to initial state
        other_q0 = f(self.q0)

        #apply f to final states
        other_F = {f(state) for state in self.F}

        # for each (state, char) key in the transition function of the NFA
        # apply f to the state and all the next states on the character 'char'
        other_d = {(f(state), char): {f(next_state) for next_state in self.d[(state, char)]} for (state, char) in self.d}
        return NFA(self.S, other_K, other_q0, other_d, other_F)

