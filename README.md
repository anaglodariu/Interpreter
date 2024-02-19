# Interpreter
Interpreter for a simplified functional programming language

Overview
==
The project consists in the implementation of a lexer in python.
A lexer is a program that divides a string of characters into substrings called lexemes, each of which is classified as a token, based on a specification.
Due to the difficulty of working directly with regexes to verify the belonging of a word in the language, real lexers go through several intermediate stages before starting the analysis of the text.

  - Stage 1 of the project consists of converting NFA into DFA (using the Subset Construction Algorithm)
  - Stage 2 of the project consists of Regex - NFA conversion (using the Thompson Algorithm)
  - Stage 3 of the project consists of implementing a lexer in python.
  - The bonus step is to use the lexer to make an interpreter for a simplistic programming language.


Testing the interpreter
==
The entry point of the interpreter will be the file src/main.py, which receives as an argument the file to be interpreted and 
prints the result of the interpretation to stdout.

Command in terminal:
==
  - python3.12 -m src.main {argumente}
