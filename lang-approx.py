#!/usr/bin/env python
import fileinput
import random
import re
import string
import sys
import json

from collections import defaultdict

class ChainMode:
    LETTERS = 0
    WORDS = 1

class OutputMode:
    LETTERS = 0
    WORDS = 1
    SENTENCES = 2

def autovivify(levels=1, final=dict):
    return (defaultdict(final) if levels < 2 else
            defaultdict(lambda: autovivify(levels - 1, final)))

def remove_punctutation(l):
    """ Remove all punctuation and suppress multiple spaces. """
    return string.strip(" ".join(
        (l.decode("utf8")).translate(string.maketrans(string.punctuation,
        " " * len(string.punctuation))).upper().split()
        )) + " "

class LanguageGenerator:
    def __init__(self, inFile, chainLength, chainMode):
        self.chainLength = chainLength
        self.chainMode = chainMode
        self.mc = autovivify(chainLength + 1, int)
        self.build_markov_chain(inFile)

    def get_restart_msg_string(self):
        if self.chainLength == 1:
            return " "
        else:
            return "  "

    def get_init_string(self):
        """
            Returns the hypothetical preceding characters for the start of a 
            new message. If possible (i.e. when self.chainLength > 1) we assume 
            that we are at the start of a sentence. In the case of characters, 
            this (roughly!) corresponds to the last 2 characters being ". ".
        """
        if self.chainMode == ChainMode.LETTERS:
            return self.get_restart_msg_string()
        else:
            return [" "]

    def get_empty_string(self):
        if self.chainMode == ChainMode.LETTERS:
            return ""
        elif self.chainMode == ChainMode.WORDS:
            return []

    def wordify_line(self, l):
        return re.findall(r"[^ ]+ | ", l)

    def tidy_sentence(self, l):
        """
            Suppresses mulitple spaces but adds a trailing space to delimit 
            words.
        """
        tidiedSentence = string.strip(l) + " "
        if self.chainMode == ChainMode.LETTERS:
            return tidiedSentence
        elif self.chainMode == ChainMode.WORDS:
            return self.wordify_line(tidiedSentence)

    def get_blank_line(self):
        if self.chainMode == ChainMode.LETTERS:
            return " "
        elif self.chainMode == ChainMode.WORDS:
            return [" "]

    def is_blank(self, l):
        return l == self.get_blank_line()

    def joined_strings(self, prevString, currentString):
        """
            Join strings together in the appropriate way (depending on 
            self.chainMode.
        """
        if self.chainMode == ChainMode.LETTERS:
            return prevString + currentString
        elif self.chainMode == ChainMode.WORDS:
            return prevString + [currentString]

    def build_markov_chain(self, inFile):
        lastString = self.get_init_string()
        nextString = self.get_empty_string()
        currentChain = self.mc
        lastLine = self.get_blank_line()
        with open(inFile) as f:
            for line in f:
                sLine = self.tidy_sentence(line)
                if not self.is_blank(lastLine) or not self.is_blank(sLine):
                    for i in xrange(len(sLine)):
                        if len(lastString) < self.chainLength:
                            """ At the start of the input text. """
                            lastString = self.joined_strings(lastString,
                                                             sLine[i])
                        else:
                            currentChain = self.mc
                            for c in lastString:
                                currentChain = currentChain[c]
                            nextString = sLine[i]
                            currentChain[nextString] += 1
                            lastString = self.joined_strings(lastString[1:],
                                                             nextString)
                lastLine = sLine

    def dump(self, s=None):
        mc = self.mc
        if s:
            for x in s:
                mc = mc[x]
        print json.dumps(mc, sort_keys=True, indent=2)

    def join_freq_list(self, x, nextLot):
        """
            Prepend x to nextLot in the appropriate way, where nextLot is the 
            set of all possible strings following x (weighted according to its 
            empirical frequency).
        """
        if self.chainMode == ChainMode.LETTERS:
            return [x + s for s in nextLot]
        elif self.chainMode == ChainMode.WORDS:
            return [[x] + s for s in nextLot]

    def get_possibilities(self, mc):
        """
            Returns a list of the possible subsequent characters/strings at the 
            end of a given sequence in the Markov chain.  mc should be the 
            Markov chain at the final step.
        """
        if self.chainMode == ChainMode.LETTERS:
            return [s for s in mc for t in xrange(mc[s])]
        elif self.chainMode == ChainMode.WORDS:
            return [[s] for s in mc for t in xrange(mc[s])]

    def get_rand_list(self, prevString, levels=None, mc=None):
        """
            If levels == 0, return a list of the possible next character.
            If levels >= 1, do the same for the next possible strings
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
        # if len(prevString) > levels:
        if prevString:
            # Take the next character in the preceding chain.
            for c in prevString:
                mc = mc[c]
            nextStrings = self.get_rand_list(self.get_empty_string(),
                                           levels - len(prevString),
                                           mc)
            randList += nextStrings
        elif levels >= 1 and not prevString:
            # No preceding characters: random choice of subsequent levels.
            for x in mc:
                
                nextStrings = self.join_freq_list(x,
                        self.get_rand_list(prevString,
                                           levels - 1,
                                           mc[x]))
                randList += nextStrings
        else:
            # No preceding characters and at the final level.
            return self.get_possibilities(mc)
        return randList

    def at_word_boundary(self, lastString):
        if self.chainMode == ChainMode.LETTERS:
            return lastString[:1] == " "
        elif self.chainMode == ChainMode.WORDS:
            return True
       
    def at_end_of_sentence(self, lastString):
        if self.chainMode == ChainMode.LETTERS:
            if self.chainLength >= 2:
                return lastString[-2:] == "  "
            elif self.chainMode == 1:
                return lastString[:1] == " "
        elif self.chainMode == ChainMode.WORDS:
            return lastString[:1] == " "

    def list_to_string(self, l):
        if self.chainMode == ChainMode.LETTERS:
            return l
        elif self.chainMode == ChainMode.WORDS:
            return "".join(l).rstrip()


    def get_random_message(self, msgLength=1, mode=OutputMode.SENTENCES):
        # We're at the start of a new sentence.
        lastString = self.get_init_string()
        msg = self.get_empty_string()
        stopCounter = 0
        while stopCounter < msgLength:
            randList = self.get_rand_list(lastString)
            
            nextString = random.choice(randList)
            msg += nextString
            lastString = lastString[1:] + nextString
                
            if (mode == OutputMode.LETTERS
                    or (mode != OutputMode.SENTENCES
                        and self.chainMode == ChainMode.WORDS)
                    or (mode == OutputMode.WORDS
                        and self.at_word_boundary(lastString))
                    or (mode == OutputMode.SENTENCES
                        and self.at_end_of_sentence(lastString))):
                stopCounter += 1
        return self.list_to_string(msg)
    
    def print_random_message(self, length=5, mode=None):
        print self.get_random_message(length, mode)
            

def main(argv=None):
    if argv is None:
        argv = sys.argv
	
    # Build the Markov chain
    mc = LanguageGenerator(argv[1], 3, ChainMode.WORDS)
    mc.print_random_message(500, OutputMode.WORDS)
    
if __name__ == "__main__":
    sys.exit(main())


