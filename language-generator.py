#!/usr/bin/env python
import fileinput
import json
import argparse
import random
import re
import string
import sys

from collections import defaultdict

LOWER_NUM_WORDS = 20
UPPER_NUM_WORDS = 500
LOWER_NUM_SENTENCES = 3
UPPER_NUM_SENTENCES = 10
LOWER_NUM_PARAGRAPHS = 3
UPPER_NUM_PARAGRAPHS = 8

class ChainMode:
    CHARS = 0
    WORDS = 1

class OutputMode:
    CHARS = 0
    WORDS = 1
    SENTENCES = 2

def autovivify(levels=1, final=dict):
    return (defaultdict(final) if levels < 2 else
            defaultdict(lambda: autovivify(levels - 1, final)))

class SentenceError(Exception):
    def __init__(self):
        pass
    
    def __str__(self):
        return "SentenceError: No sentences in source text."

class LanguageGenerator:
    def __init__(self, inFile, chainLength, chainMode):
        self.chainLength = chainLength
        self.chainMode = chainMode
        self.mc = autovivify(chainLength + 1, int)
        
        # Assume that there is no sentence structure in inFile (for now).
        self.noSentences = True
        
        # Construct the conditional probabilities.
        self.build_markov_chain(inFile)
        inFile.close()

    def get_restart_msg_string(self):
        """ Return a `sentence boundary', which is understood to be a
        double space.  When the chain length is 1 we take this to be a
        single space because we cannot check that the previous 2
        characters are spaces.
        """
        if self.chainLength == 1:
            return " "
        else:
            return "  "

    def get_init_string(self):
        """ Returns the hypothetical preceding characters for the start
        of a new message.  If possible (i.e. when self.chainLength > 1)
        we assume that we are at the start of a sentence.  In the case
        of characters, this (roughly!) corresponds to the last 2
        characters being ". ".
        """
        if self.chainMode == ChainMode.CHARS:
            return self.get_restart_msg_string()
        else:
            return [" "]

    def get_empty_string(self):
        """ Return an empty string in the correct form. """
        if self.chainMode == ChainMode.CHARS:
            return ""
        elif self.chainMode == ChainMode.WORDS:
            return []

    def wordify_line(self, l):
        """ Split a line into non-whitespace characters followed by a
        single space.  Also consider orphaned single spaces, which will
        denote a sentence boundary.
        """
        return re.findall(r"[^ ]+ | ", l)

    def tidy_sentence(self, l):
        """ Remove surrounding white space from l and then add a
        trailing space to help delimit words on different lines.
        """
        tidiedSentence = string.strip(l) + " "
        if self.chainMode == ChainMode.CHARS:
            return tidiedSentence
        elif self.chainMode == ChainMode.WORDS:
            return self.wordify_line(tidiedSentence)

    def get_blank(self):
        """ Return a blank character in the correct form. """
        if self.chainMode == ChainMode.CHARS:
            return " "
        elif self.chainMode == ChainMode.WORDS:
            return [" "]

    def is_blank(self, l):
        """ Determine if l is a blank character. """
        return l == self.get_blank()

    def joined_strings(self, prevString, currentString):
        """ Join strings together in the appropriate way (depending on 
        self.chainMode).
        """
        if self.chainMode == ChainMode.CHARS:
            return prevString + currentString
        elif self.chainMode == ChainMode.WORDS:
            return prevString + [currentString]

    def build_markov_chain(self, inFile):
        """ Compute the conditional probabilities. """
        lastString = self.get_init_string()
        nextString = self.get_empty_string()
        currentChain = self.mc
        lastLine = self.get_blank()
        for line in inFile:
            sLine = self.tidy_sentence(line)
            # Ignore paragraph breaks.
            if not self.is_blank(lastLine) or not self.is_blank(sLine):
                for i in xrange(len(sLine)):
                    # At the start of the input: build up the string of 
                    # preceding characters.
                    if len(lastString) < self.chainLength:
                        lastString = self.joined_strings(lastString,
                                                         sLine[i])
                    # Not at the start: we know the preceding characters.
                    else:
                        currentChain = self.mc
                        for c in lastString:
                            currentChain = currentChain[c]
                        nextString = sLine[i]
                        currentChain[nextString] += 1
                        lastString = self.joined_strings(lastString[1:],
                                                         nextString)
                    if (self.noSentences
                            and self.at_end_of_sentence(lastString)):
                        self.noSentences = False
            lastLine = sLine

    def dump(self, s=None):
        """ Print the frequency of chains of letters.  If a string s is
        supplied, print the frequency of chains from that part of the
        chain.
        """
        mc = self.mc
        if s:
            for x in s:
                mc = mc[x]
        print json.dumps(mc, sort_keys=True, indent=2)

    def join_freq_list(self, x, nextLot):
        """ Prepend x to nextLot in the appropriate way, where nextLot
        is the set of all possible strings following x (weighted
        according to its empirical frequency).
        """
        if self.chainMode == ChainMode.CHARS:
            return [x + s for s in nextLot]
        elif self.chainMode == ChainMode.WORDS:
            return [[x] + s for s in nextLot]

    def get_possibilities(self, mc):
        """ Returns a list of the possible subsequent characters/strings
        at the end of a given sequence in the Markov chain.  mc should
        be the Markov chain at the final step.
        """
        if self.chainMode == ChainMode.CHARS:
            return [s for s in mc for t in xrange(mc[s])]
        elif self.chainMode == ChainMode.WORDS:
            return [[s] for s in mc for t in xrange(mc[s])]

    def get_rand_list(self, prevString, levels=None, mc=None):
        """ If levels == 0, return a list of the possible next
        character. If levels >= 1, do the same for the next possible
        strings (with length given by levels). Both lists are weighted
        according to the probabilities that the elements occur.
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
        """ Return True if at a word boundary. """
        if self.chainMode == ChainMode.CHARS:
            return lastString[-1] == " "
        elif self.chainMode == ChainMode.WORDS:
            return True
       
    def at_end_of_sentence(self, lastString):
        """ Return True if at the end of a sentence. """
        if self.chainMode == ChainMode.CHARS:
            if self.chainLength >= 2:
                return lastString[-2:] == "  "
            elif self.chainMode == 1:
                return lastString[-1] == " "
        elif self.chainMode == ChainMode.WORDS:
            return lastString[-1] == " "

    def list_to_string(self, l):
        """ Return the string corresponding to l. """
        if self.chainMode == ChainMode.CHARS:
            return l
        elif self.chainMode == ChainMode.WORDS:
            return "".join(l).rstrip()

    def get_paragraph_length(self, length, outputMode):
        """ If the length has been set to 0, return a random paragraph
        length.
        """
        if length >= 1:
            return length
        elif outputMode == OutputMode.SENTENCES:
            return random.randint(LOWER_NUM_SENTENCES, UPPER_NUM_SENTENCES)
        elif outputMode == OutputMode.WORDS:
            return random.randint(LOWER_NUM_WORDS, UPPER_NUM_WORDS)

    def new_paragraph(self):
        """ Return the appropriate string to start a new paragraph. """
        if self.chainMode == ChainMode.CHARS:
            return "\n\n"
        elif self.chainMode == ChainMode.WORDS:
            return ["\n\n"]

    def get_random_message(self, msgLength=0, mode=OutputMode.WORDS,
                           paragraphs=1):
        """ Generate some paragraphs each of length msgLength, which is
        determined by the output mode.
        """
        # Output requested in the form of sentences
        try:
            if mode == OutputMode.SENTENCES and self.noSentences:
                raise SentenceError()
                
            # We're at the start of a new sentence.
            lastString = self.get_init_string()
            msg = self.get_empty_string()
            for i in xrange(paragraphs):
                stopCounter = 0
                paraLength = self.get_paragraph_length(msgLength, mode)
                while stopCounter < paraLength:
                    randList = self.get_rand_list(lastString)
                    if randList:
                        # There is something to choose.
                        nextString = random.choice(randList)
                        msg += nextString
                        lastString = lastString[1:] + nextString
                        if (mode == OutputMode.CHARS
                                or (mode != OutputMode.SENTENCES
                                    and self.chainMode == ChainMode.WORDS)
                                or (mode == OutputMode.WORDS
                                    and self.at_word_boundary(lastString))
                                or (mode == OutputMode.SENTENCES
                                    and self.at_end_of_sentence(lastString))):
                            stopCounter += 1
                    else:
                        """ Nothing to choose, i.e. we have reached the
                        end of the file.  (Presumably there are no other
                        causes for no choice?)  Reset lastString.
                        """
                        lastString = self.get_init_string()
                if i < paragraphs - 1:
                    msg += self.new_paragraph()
            return self.list_to_string(msg)
        except SentenceError as e:
            sys.exit(e)

    def print_random_message(self, length=0, mode=OutputMode.WORDS,
                             paragraphs=1):
        """ Print some paragraphs each of length msgLength, which is
        determined by the output mode.
        """
        print self.get_random_message(length, mode, paragraphs)
            

def main(argv=None):
    if argv is None:
        argv = sys.argv
    
    # Command line arguments.
    p = argparse.ArgumentParser(description="Take some text, create a Markov \
            chain (of chars or words), and use the Markov chain to random \
            generate words and sentences.")
    p.add_argument("inputFile", nargs="?",
            type=argparse.FileType("r"), default=sys.stdin, metavar="FILE",
            help="the FILE from which to create the Markov chain (default: \
            stdin)")
    p.add_argument("-c", "--chain-mode", choices=["chars", "words"],
            default="chars",
            help="create a Markov chain of {%(choices)s}")
    p.add_argument("-l", "--chain-length", type=int,
            default=1, metavar="LENGTH",
            help="the LENGTH of the Markov chain")
    p.add_argument("-w", "--output-words", type=int, default=-1, metavar="N",
            help="output N words (N=0 selects a random positive integer)")
    p.add_argument("-s", "--output-sentences", type=int, default=-1, metavar="N",
            help="output N sentences (N=0 selects a random positive integer)")
    p.add_argument("-p", "--output-paragraphs", type=int, default=1, metavar="N",
            help="output N paragraphs (N=0 selects a random positive integer)")
    args = p.parse_args()
    
    # Requested Markov chain type.
    if args.chain_mode == "words":
        chainMode = ChainMode.WORDS
    else:
        chainMode = ChainMode.CHARS
    outputLength = 0
    
    # Determine what to output, defaulting to words if necessary.
    if args.output_sentences >= 0:
        outputMode = OutputMode.SENTENCES
        outputLength = args.output_sentences
    else:
        outputMode = OutputMode.WORDS
        outputLength = args.output_words
    
    # Number of paragraphs, randomising if not specified.
    if args.output_paragraphs >= 1:
        outputParagraphs = args.output_paragraphs
    else:
        outputParagraphs = random.randint(LOWER_NUM_PARAGRAPHS,
                                          UPPER_NUM_PARAGRAPHS)
    
    # Build the Markov chain
    mc = LanguageGenerator(args.inputFile, args.chain_length, chainMode)
    mc.print_random_message(outputLength, outputMode, outputParagraphs)
    
if __name__ == "__main__":
    sys.exit(main())


