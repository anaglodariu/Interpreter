from sys import argv
from src.Lexer import Lexer
from dataclasses import dataclass
from src.Interpreter import Interpreter, Parser

# spec for lexer
@dataclass
class Spec:
    spec = [
        ('LAMBDA', '\\ *lambda\\ *'),
        ('OPAR', '\\ *\\(\\ *'),
        ('CPAR', '\\ *\\)\\ *'),
        ('NR', '\\ *[0-9]+\\ *'),
        ('ID', '\\ *([a-z]|[A-Z])+\\ *'),
        ('PLUS', '\\ *\\+\\ *'),
        ('CONCAT', '\\ *\\+\\+\\ *'),
        ('NEWLINE', '\\ *\n\\ *'),
        ('SEPARATOR', '\\ *:\\ *'),
        ('TAB', '\\ *\t\\ *'),
    ]

def main():
    if len(argv) != 2:
        return
    
    filename = argv[1]

    with open(filename, 'r') as file:
        string = file.read()
    
    spec = Spec.spec
    lexer = Lexer(spec)
    token_list = lexer.lex(string)

    parser = Parser(token_list)
    result = parser.parse()

    interpreter = Interpreter(result)
    interpreter.evaluate()

if __name__ == '__main__':
    main()
