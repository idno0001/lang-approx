#!/usr/bin/env python
import fileinput
import random
import string
import sys
import json

from collections import defaultdict

CHAIN_LENGTH = 7

def dump(mc):
    print json.dumps(mc, sort_keys=True, indent=2)

def autovivify(levels=1, final=dict):
    return (defaultdict(final) if levels < 2 else
            defaultdict(lambda: autovivify(levels - 1, final)))

def sanitise_line(l):
    """ Remove all punctuation and suppress multiple spaces. """
    return string.rstrip(" ".join((l).translate(string.maketrans(string.punctuation,
        " " * len(string.punctuation))).upper().split())) + " "

def build_markov_chain(mc, levels=1):
    lastChars = " "
    nextChar = ""
    currentChain = mc
    for line in fileinput.input():
        sLine = sanitise_line(line)
        for i in xrange(len(sLine)):
            if len(lastChars) < levels - 1:
                """ At the start of the input text. """
                lastChars += sLine[i]
            else:
                currentChain = mc
                for c in lastChars:
                    currentChain = currentChain[c]
                nextChar = sLine[i]
                currentChain[nextChar] += 1
                lastChars = lastChars[1:] + nextChar
    return mc

def get_rand_list(mc, precedingChars, levels=1):
    """
        If levels == 1, return a list of the possible next character.
        If levels > 1, do the same for the next possible strings
        (with length given by levels).
        Both lists are weighted according to the probabilities that the
        elements occur.
    """
    randList = []
    # The following should raise an exception.
    # if len(precedingChars) > levels - 1:
    if precedingChars == "" and levels > 1:
        # No preceding characters: random choice of subsequent levels.
        for x in mc:
            nextChars = get_rand_list(mc[x], precedingChars, levels - 1)
            nextChars = [x + s for s in nextChars]
            randList += nextChars
            # randList += get_rand_list(mc[x], precedingChars, levels - 1)
    elif precedingChars != "":
        # Take the next character in the preceding chain.
        # randList += get_rand_list(mc[precedingChars[0]], precedingChars[1:], levels - 1)
        for c in precedingChars:
            mc = mc[c]
        nextChars = get_rand_list(mc, "", levels - len(precedingChars))
        if precedingChars[-1] == " ":
            nextChars = [c for c in nextChars if c != " "] # Avoid double spaces.
        randList += nextChars
    else:
        # No preceding characters and at the final level.
        return [x for x in mc for y in xrange(mc[x])]
    # What if randList is empty?
    return randList

# What if levels == 1?
def get_next_char(mc, precedingChars, levels=1):
    if len(precedingChars) == levels - 1:
        # We have already built up the first few characters of the message.
        # frequencies = mc
        # for c in precedingChars:
        #     frequencies = frequencies[c]
        # return random.choice([x for x in frequencies for y in xrange(frequencies[x])])
        return random.choice(get_rand_list(mc, precedingChars, levels))
    else:
        # Not enough preceding characters: we are at the start of a message.
        return random.choice(get_rand_list(mc, precedingChars, levels))

def say_something(mc, levels=1, msgLength=100):
    msg = ""
    lastChars = " "
    for c in xrange(msgLength):
        if msg == "":
            """
                Choose the first (levels - 1) characters completely at random.
                Start with a space to guarantee word boundary.
            """
            nextChar = get_next_char(mc, lastChars, CHAIN_LENGTH)
            msg += nextChar
        else:
            """
                Choose the next character depending on the previous
                (levels - 1) characters.
            """
            nextChar = get_next_char(mc, lastChars, CHAIN_LENGTH)
            msg += nextChar
        lastChars = "".join((lastChars[1:], nextChar))
    return msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
	
    # The Markov chain.
    mc = autovivify(CHAIN_LENGTH, int)
    
    # Build the Markov chain
    mc = build_markov_chain(mc, CHAIN_LENGTH)
    
    print say_something(mc, CHAIN_LENGTH, 500)
        

if __name__ == "__main__":
    sys.exit(main())


