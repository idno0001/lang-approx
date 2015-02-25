# language-generator

## About
As the name suggests, *language-generator* generates text that resembles a 
language in some way.  The idea is simple: it takes a sample input text and 
computes the conditional probabilities that characters (respectively words) 
follow a string of other characters (respectively words) of, say, length *n*.  
This gives an *n*-step Markov chain.  Using this Markov chain, 
*language-generator* can then print random text with the same conditional 
probabilities.

## Requirements
The only requirement is [Python 2.7](https://www.python.org/downloads/).  
Older releases of Python may also work, but this has not been tested.

## Input texts
[Project Gutenberg](https://www.gutenberg.org/) is a good source for free 
ebooks that can serve as input texts; *language-generator* was tested using 
George Eliot's [*Middlemarch*](https://www.gutenberg.org/ebooks/145), although 
any reasonably long text will produce interesting results.

If you want to generate full sentences with *language-generator*, sentences in 
the input text need to be separated by *double spaces*.<sup>1</sup>  For 
example:
```
This is a sentence.  This is another sentence.
```
(Sentences in *Middlemarch* are delimited by double spaces.)

## Example usage
Let us suppose that our input text is the file `middlemarch.txt`.
```
python language-generator.py --chain-length 2 --chain-mode words --sentences 4 --paragraphs 3 middlemarch.txt
```
This creates a *2*-step Markov chain of *words*, i.e. the next word depends on 
the previous *2* words.  The output is given as *3* paragraphs, each with *4* 
sentences.

```
python language-generator.py --chain-length 3 --chain-mode chars --sentences 2 --paragraphs 5 middlemarch.txt
```
This creates a *3*-step Markov chain of *chars* (characters), i.e. the next 
word depends on the previous *3* characters.  The output is given as *5* 
paragraphs, each with *2* sentences.

```
python language-generator.py --chain-length 3 --chain-mode chars --words 50 middlemarch.txt
```
This produces the same Markov chain as the previous example.  The output is 
given as *1* paragraph (the `--paragraphs 1` argument may be omitted) with 50 
words. (Not quite! We are currently counting things incorrectly.)

```
python language-generator.py --chain-length 3 --chain-mode words --sentences 0 --paragraphs 0 middlemarch.txt
```
This produces a *3*-step Markov chain of words. The `--paragraphs 0` argument 
chooses a random number of paragraphs to print, and the `--sentences 0` 
argument means that each paragraph has a random number of sentences.

## General usage
```
usage: language-generator.py [-h] [-c {chars,words}] [-l LENGTH] [-w N] [-s N]
                             [-p N]
                             [FILE]

Take some text, create a Markov chain (of chars or words), and use the Markov
chain to random generate words and sentences.

positional arguments:
  FILE                  the FILE from which to create the Markov chain
                        (default: stdin)

optional arguments:
  -h, --help            show this help message and exit
  -c {chars,words}, --chain-mode {chars,words}
                        create a Markov chain of {chars, words}
  -l LENGTH, --chain-length LENGTH
                        the LENGTH of the Markov chain
  -w N, --words N       output N words (N=0 selects a random positive integer)
  -s N, --sentences N   output N sentences (N=0 selects a random positive
                        integer)
  -p N, --paragraphs N  output N paragraphs (N=0 selects a random positive
                        integer)
```

## Current issues and future improvements
The following may be added or improved in the future:
* When the user chooses to print a fixed number of words, the number printed 
may be incorrect.
* $0$-step Markov chains do not work.
* Double space sentence delimiters should be generalised.
* The conditional probabilities are recalculated each time. A temporary file 
could be used to store the Markov chain for later use.

<sup>1</sup> A quick search for `double space sentence` on your favourite 
search engine will reveal that this is frowned upon by many people.  I do it 
in this `README` for consistency with the Python comments ([PEP 
8](https://www.python.org/dev/peps/pep-0008/) insists).  This is certainly 
something that will be changed in future versions of *language-generator*, but 
I wrote it this way because double spacing provides a very obvious way to 
delimit sentences.
