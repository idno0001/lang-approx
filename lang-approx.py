#!/usr/bin/env python
import fileinput
import random
import string
import sys
import json

from collections import defaultdict

def autovivify(levels=1, final=dict):
    return (defaultdict(final) if levels < 2 else
            defaultdict(lambda: autovivify(levels - 1, final)))

def remove_punctutation(l):
    """ Remove all punctuation and suppress multiple spaces. """
    return string.rstrip(" ".join(
        (l.decode("utf8")).translate(string.maketrans(string.punctuation,
        " " * len(string.punctuation))).upper().split()
        )) + " "

def add_trailing_space(l):
    """ Suppresses mulitple spaces but adds a trailing space. """
    return string.rstrip(" ".join(l.decode("utf8").split())) + " "
    
class LanguageGenerator:
    def __init__(self, inFile, chainLength):
        self.chainLength = chainLength
        self.mc = autovivify(chainLength, int)
        self.build_markov_chain(inFile)

    def build_markov_chain(self, inFile):
        lastChars = ". "
        nextChar = ""
        currentChain = self.mc
        with open(inFile) as f:
            for line in f:
                sLine = add_trailing_space(line)
                for i in xrange(len(sLine)):
                    if len(lastChars) < self.chainLength - 1:
                        """ At the start of the input text. """
                        lastChars += sLine[i]
                    else:
                        currentChain = self.mc
                        for c in lastChars:
                            currentChain = currentChain[c]
                        nextChar = sLine[i]
                        currentChain[nextChar] += 1
                        lastChars = lastChars[1:] + nextChar

    def dump(self):
        print json.dumps(self.mc, sort_keys=True, indent=2)

    def get_rand_list(self, precedingChars, levels=None, mc=None):
        """
            If levels == 1, return a list of the possible next character.
            If levels > 1, do the same for the next possible strings
            (with length given by levels).
            Both lists are weighted according to the probabilities that the
            elements occur.
        """
        if mc is None:
            mc = self.mc
        if levels is None:
            levels = self.chainLength
        randList = []
        
        # The following should raise an exception.
        # if len(precedingChars) > levels - 1:
        if precedingChars == "" and levels > 1:
            # No preceding characters: random choice of subsequent levels.
            for x in mc:
                nextChars = self.get_rand_list(precedingChars,
                                               levels - 1,
                                               mc[x])
                nextChars = [x + s for s in nextChars]
                randList += nextChars
        elif precedingChars != "":
            # Take the next character in the preceding chain.
            for c in precedingChars:
                mc = mc[c]
            nextChars = self.get_rand_list("",
                                           levels - len(precedingChars),
                                           mc)
            if precedingChars[-1] == " ":
                # Avoid double spaces.
                nextChars = [c for c in nextChars if c != " "]
            randList += nextChars
        else:
            # No preceding characters and at the final level.
            return [x for x in mc for y in xrange(mc[x])]
        # What if randList is empty?
        return randList

    def say_something(self, msgLength=100):
        msg = ""
        lastChars = ". "  # We're at the start of a new sentence.
        for c in xrange(msgLength):
            nextChar = random.choice(self.get_rand_list(lastChars))
            msg += nextChar
            lastChars = "".join((lastChars[1:], nextChar))
        return msg
    
    def print_something(self, msgLength=100):
        print self.say_something(msgLength)

def main(argv=None):
    if argv is None:
        argv = sys.argv
	
    # Build the Markov chain
    mc = LanguageGenerator(argv[1], 7)
    mc.print_something(500)
    
if __name__ == "__main__":
    sys.exit(main())


