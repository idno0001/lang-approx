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

    def get_init_string(self):
        """
            Returns the hypothetical preceding characters for the start of a 
            new message. If possible (i.e. when self.chainLength > 1) we assume 
            that we are at the start of a sentence. In the case of characters, 
            this (roughly!) corresponds to the last 2 characters being ". ".
        """
        if self.chainMode == ChainMode.LETTERS:
            if self.chainLength == 1:
                return " "
            else:
                return "  "
        else:
            return [" "]
    
    def get_empty_string(self):
        if self.chainMode == ChainMode.LETTERS:
            return ""
        elif self.chainLength == ChainMode.WORDS:
            return []

    def tidy_sentence(self, l):
        """
            Suppresses mulitple spaces but adds a trailing space unless the 
            line is blank.
        """
        tidiedSentence = string.strip(l.decode("utf8"))
        return tidiedSentence + " "

    def wordify_line(self, l):
        return re.findall(r"[\w']+|[.,!?;] |--", l)

    def get_blank_line(self):
        if self.chainMode == ChainMode.LETTERS:
            return " "
        elif self.chainMode == ChainMode.WORDS:
            return [" "]

    def is_blank(self, l):
        return l == self.get_blank_line()
    
    def build_markov_chain(self, inFile):
        lastChars = self.get_init_string()
        nextChar = self.get_empty_string()
        currentChain = self.mc
        lastLine = self.get_blank_line()
        with open(inFile) as f:
            for line in f:
                sLine = self.tidy_sentence(line)
                if self.chainMode == ChainMode.WORDS:
                    sLine = self.wordify_line(sLine)
                if not self.is_blank(lastLine) or not self.is_blank(sLine):
                    for i in xrange(len(sLine)):
                        if len(lastChars) < self.chainLength:
                            """ At the start of the input text. """
                            lastChars += sLine[i]
                        else:
                            currentChain = self.mc
                            for c in lastChars:
                                currentChain = currentChain[c]
                            nextChar = sLine[i]
                            currentChain[nextChar] += 1
                            lastChars = lastChars[1:] + nextChar
                lastLine = sLine

    def dump(self, s=None):
        mc = self.mc
        if s:
            for x in s:
                mc = mc[x]
        print json.dumps(mc, sort_keys=True, indent=2)

    def get_rand_list(self, precedingChars, levels=None, mc=None):
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
        # if len(precedingChars) > levels:
        if precedingChars:
            # Take the next character in the preceding chain.
            for c in precedingChars:
                mc = mc[c]
            nextChars = self.get_rand_list("",
                                           levels - len(precedingChars),
                                           mc)
            # if precedingChars[-1] == " ":
            #     # Avoid double spaces.
            #     nextChars = [c for c in nextChars if c != " "]
            randList += nextChars
        elif levels >= 1 and not precedingChars:
            # No preceding characters: random choice of subsequent levels.
            for x in mc:
                nextChars = self.get_rand_list(precedingChars,
                                               levels - 1,
                                               mc[x])
                nextChars = [x + s for s in nextChars]
                randList += nextChars
        else:
            # No preceding characters and at the final level.
            return [x for x in mc for y in xrange(mc[x])]
        return randList

    def at_word_boundary(self, lastString):
        if self.chainMode == ChainMode.LETTERS:
            return lastString[:1] == " "
        elif self.chainMode == ChainMode.WORDS:
            lw = lastString[-1]
            return lw[-1] == " "
       
    def at_end_of_sentence(self, lastString):
        if self.chainMode == ChainMode.LETTERS:
            if self.chainLength >= 2:
                return lastString[-2:] == "  "
            elif self.chainMode == 1:
                return lastString[:1] == " "
        elif self.chainMode == ChainMode.WORDS:
           return lastString[-1] == ". "

    def get_random_message(self, msgLength=1, mode=None):
        if mode is None:
            mode = OutputMode.SENTENCES

        # We're at the start of a new sentence.
        lastString = self.get_init_string()
        msg = self.get_empty_string()
        stopCounter = 0
        while stopCounter < msgLength:
            nextString = random.choice(self.get_rand_list(lastString))
            msg += nextString
            lastString = lastString[1:] + nextString
            if (mode == OutputMode.LETTERS
                    or (mode == OutputMode.WORDS
                        and self.at_word_boundary(lastString))
                    or (mode == OutputMode.SENTENCES
                        and self.at_end_of_sentence(lastString))):
                stopCounter += 1
        return msg.rstrip()
    
    def print_random_message(self, length=5, mode=None):
        print self.get_random_message(length, mode)
            

def main(argv=None):
    if argv is None:
        argv = sys.argv
	
    # Build the Markov chain
    mc = LanguageGenerator(argv[1], 7, ChainMode.LETTERS)
    mc.print_random_message(5, OutputMode.SENTENCES)
    
if __name__ == "__main__":
    sys.exit(main())


