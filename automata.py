# -*- coding: utf-8 -*-

from collections import defaultdict
from functools import wraps
from jinja2 import Environment, FileSystemLoader

EPSILON = '€'
OR      = ','
SYMBOLS = (')', '(', OR)


class SymbolNotInAlphabetError(Exception):

    def __init__(self, symbol, alphabet):
        message = "The symbol %s doesn't belong to the alphabet %s" % \
            (symbol, alphabet)
        Exception.__init__(self, message)


def check_alphabet(f):
    @wraps(f)
    def _f(self, *args, **kwargs):
        symbol = args[-1]
        if symbol not in self.alphabet:
            raise SymbolNotInAlphabetError(symbol, self.alphabet)
        return f(self, *args, **kwargs)
    return _f


def balanced_parenthesis(txt):
    count = 0
    for c in txt:
        if c == '(': count += 1
        if c == ')': count -= 1
        if count < 0: return False
    return count == 0

class Automata:

    def __init__(self, alphabet):
        self.transition = defaultdict(set)
        self.states = set()
        self.final_states = set()
        self.initial_state = None
        self.alphabet = set(alphabet)

    def set_initial(self, state):
        "Sets the initial state of the automata"
        assert isinstance(state, int)
        self.initial_state = state
        self.states.add(state)

    def add_final(self, state):
        "Add a state and make it final or set a state to be final"
        assert isinstance(state, int)
        self.final_states.add(state)
        self.states.add(state)

    def add_finals(self, states):
        "Makes every state in states final"
        for state in states:
            self.add_final(state)

    @check_alphabet
    def add_transition(self, s1, s2, symbol):
        "Adds a transition from s1 to s2 under symbol"
        self.states = self.states.union({s1, s2})
        self.transition[s1, symbol].add(s2)

    def add_transitions(self, transitions):
        """ Adds all transitions. transitions = {s1: (s2, a) ... }"""
        for s1, a in transitions:
            self.add_transition(s1, transitions[s1, a], a)

    def get_transition(self, state, symbol):
        """ Returns the state reached after applying symbol on state.
            Method used by NFA, DFA and other child classes. """
        raise NotImplemented

    def is_final(self, state):
        "Checks wether an state is final"
        return state in self.final_states

    def is_initial(self, state):
        "Checks wether an state is initial"
        return state == self.initial_state

    def get_transition_html(self):
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('transition_table.html')
        return template.render( alphabet = sorted(self.alphabet - {EPSILON}),
                                states   = sorted(self.states),
                                transition = self.get_transition)


class DFA(Automata):

    @check_alphabet
    def get_transition(self, state, symbol):
        "Returns the transition D(set_state_or_state, symbol)"
        # state = [s0, s1, s2, ...] or s0
        if isinstance(state, int):
            return self.transition[state, symbol]
        return reduce(set.union, [self.transition[s, symbol] for s in state])


class NFA(Automata):

    def __init__(self, alphabet):
        Automata.__init__(self, alphabet)
        self.alphabet.add(EPSILON)

    @check_alphabet
    def single_transition(self, state, symbol):
        "Returns the extended transition D(state, symbol)"
        assert isinstance(state, int) and state in self.states
        eclosure = self.epsilon_closure(state)
        r = [map(self.epsilon_closure, self.transition[s, symbol])
             for s in eclosure]
        r = sum(r, list())
        if len(r) == 0:
            return set()
        return reduce(set.union, r)

    def get_transition(self, state, symbol):
        "Returns the extended transition D(set_state_or_state, symbol)"
        # state = [s0, s1, s2, ...] or s0
        if isinstance(state, int):
            return self.single_transition(state, symbol)
        if len(state) == 1:
            return self.single_transition(list(state)[0], symbol)
        r = [self.single_transition(s, symbol) for s in state]
        if len(r) == 0:
            return set()
        return reduce(set.union, r)

    def epsilon_closure(self, state, result=set()):
        "Returns the Epsilon-closure or Lambda-closure of state."
        assert isinstance(state, int) and state in self.states
        result = result.union(self.transition[state, EPSILON] | {state})
        for s in result:
            for s2 in self.transition[s, EPSILON]:
                if s2 not in result:
                    result = self.epsilon_closure(s2, result)
        return result



class RegularExpression:

    def __init__(self, regex_str):
        if not balanced_parenthesis(regex_str):
            raise Exception("Parenthesis not balanced.")
        self.regex = '(' + regex_str + ')'
        self.nfa = None
        self.nfa = self.get_nfa()

    def get_nfa(self):
        if self.nfa: return self.nfa
        alphabet = set(c for c in self.regex if c not in SYMBOLS)
        nfa = NFA(alphabet)
        nfa.set_initial(0)
        nfa.add_final(len(self.regex))
        stack = list()

        for i in xrange(len(self.regex)):
            if self.regex[i] in alphabet:
                nfa.add_transition(i, i + 1, self.regex[i])
            elif self.regex[i] == '(':
                nfa.add_transition(i, i + 1, EPSILON)
                stack.append(i)
            elif self.regex[i] == ')':
                nfa.add_transition(i, i + 1, EPSILON)
                ind = stack.pop()
                tmplist = list()
                # Adds a transition between every or and the closing parenthesis
                while self.regex[ind] == OR:
                    tmplist.append(ind)
                    nfa.add_transition(ind, i, EPSILON)
                    ind = stack.pop()
                # Adds a transition between the opening parenthesis and every or
                for n in tmplist:
                    nfa.add_transition(ind, n + 1, EPSILON)                    
            elif self.regex[i] == OR:
                stack.append(i)
                
        return nfa

    def __str__(self):
        return self.regex

    def matches(self, text):
        state = self.nfa.initial_state
        for i, letter in enumerate(text):
            try:
                state = self.nfa.get_transition(state, letter)
            except SymbolNotInAlphabetError:
                return (False, i)
        result = any(map(lambda s: s in state, (f for f in self.nfa.final_states)))
        return (result, len(text))

    def search(self, text):
        i = 0
        result = list()
        while i < len(text):
            state = self.nfa.epsilon_closure(self.nfa.initial_state)
            offset = 0
            while True:
                try:
                    state = self.nfa.get_transition(state, text[i + offset])
                    if any(map(lambda s: s in state, (f for f in self.nfa.final_states))):
                        result.append((i, i+offset, text[i: i + offset + 1]))
                        i += offset + 1
                        break
                    offset += 1
                except (SymbolNotInAlphabetError, IndexError) as e:
                    i += 1
                    break
        return result


# Show examples from class
if __name__ == '__main__':
    r = RegularExpression("abcd")
    print r.search("This is a text with abcd inside two times abcd")