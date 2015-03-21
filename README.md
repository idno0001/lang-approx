# language-generator

## About
As the name suggests, *language-generator* generates text that resembles a 
language in some way. The idea is simple: it takes a sample input text and 
computes the conditional probabilities that characters (respectively words) 
follow a string of other characters (respectively words) of, say, length n. 
This gives an n-step Markov chain. Using this Markov chain, 
*language-generator* can then print random text with the same conditional 
probabilities.

## Requirements
The only requirement is [Python 2.7](https://www.python.org/downloads/). Python 
3 is not supported, but older releases of Python *may* work as long as the 
`argparse` module is [installed](https://pypi.python.org/pypi/argparse/).

## Input texts
[Project Gutenberg](https://www.gutenberg.org/) is a good source for free 
ebooks that can serve as input texts; *language-generator* was tested using 
George Eliot's [*Middlemarch*](https://www.gutenberg.org/ebooks/145), although 
any reasonably long text will produce interesting results.

If you want to generate full sentences with *language-generator*, sentences in 
the input text need to be separated by *double spaces*.<sup>1</sup> For 
example:
```
This is a sentence. This is another sentence.
```
(Sentences in *Middlemarch* are delimited by double spaces.)

## Example usage
Let us suppose that our input text is the file `middlemarch.txt`.

1. Use:

    ```
    $ python language-generator.py -l 2 -c words -s 4 -p 3 middlemarch.txt
    ```
to create a 2-step Markov chain of *words*, i.e. the next word depends on the 
previous 2 words. The output is given as 3 paragraphs, each with 4 sentences.
Equivalently, we can use:

    ```
    $ python language-generator.py --chain-length 2 --chain-mode words --output-sentences 4 --output-paragraphs 3 middlemarch.txt
    ```

2. Use:

    ```
    $ python language-generator.py -l 3 -c chars -s 2 -p 5 middlemarch.txt
    ```
to create a 3-step Markov chain of *chars* (characters), i.e. the next word 
depends on the previous 3 characters. The output is given as 5 paragraphs, 
each with 2 sentences.
3. Use:

    ```
    $ python language-generator.py -l 3 -c chars -w 50 middlemarch.txt
    ```
to produce the same Markov chain as the previous example, but this time with 
the output given as 50 words. When omitted, the `-p`/`--paragraphs` argument 
is assumed to be `-p 1`/`--paragraphs 1`. (Not quite! Words are currently 
being counted incorrectly.)
4. Use:

    ```
    $ python language-generator.py -l 3 -c words -s 0 -p 0 middlemarch.txt
    ```
to produce a 3-step Markov chain of words. The `-p 0` argument chooses a 
random number of paragraphs to print, and the `--sentences 0` argument means 
that each paragraph has a random number of sentences.
5. Use:

    ```
    $ python language-generator.py -l 3 -c chars -w 50 --no-punctuation --case-insensitive middlemarch.txt
    ```
to produce a case insensitive version of Example 3 with all punctuation 
removed.

## General usage
```
usage: language-generator.py [-h] [-c {chars,words}] [-l LENGTH] [-w N] [-s N]
                             [-p N] [--case-sensitive] [--case-insensitive]
                             [--punctuation] [--no-punctuation]
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
  -w N, --output-words N
                        output N words (N=0 selects a random positive integer)
  -s N, --output-sentences N
                        output N sentences (N=0 selects a random positive
                        integer)
  -p N, --output-paragraphs N
                        output N paragraphs (N=0 selects a random positive
                        integer)
  --case-sensitive      do not ignore case (default)
  --case-insensitive    ignore case
  --punctuation         retain all punctuation (default)
  --no-punctuation      remove punctuation
```

## Current issues and future improvements
The following may be added or improved in the future:
* When the user chooses to print a fixed number of words, the number printed 
may be incorrect.
* 0-step Markov chains do not work.
* Double space sentence delimiters should be generalised.
* The conditional probabilities are recalculated each time. A temporary file 
could be used to store the Markov chain for later use.
* Quotation marks are sometimes orphaned.

<sup>1</sup> A quick search for `double space sentence` on your favourite 
search engine will reveal that this is frowned upon by many people. From my 
point of view, double spaces provide an obvious delimeter for sentences. This 
is certainly a restriction that I hope to change in future versions of 
*language-generator*, although there are various challenges. For example, 
abbreviations such as `e.g. `, `Ph.D. ` and `A.C.M.E. ` may be incorrectly 
marked as the end of a sentence.

