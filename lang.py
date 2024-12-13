from enum import Enum
import re

import assembler

class TokenType(Enum):
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"
    OPERATOR = "OPERATOR"
    NEWLINE = "NEWLINE"
    EOF = "EOF"

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None
        
        self.keywords = {
            'func', 'draw', 'compute', 'var',
            'if', 'while', 'end', 'return'
        }

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace() and self.current_char != '\n':
            self.advance()

    def get_number(self):
        result = ''
        while self.current_char and (self.current_char.isdigit() or 
              self.current_char in ['x', 'b'] or 
              self.current_char in ['a', 'b', 'c', 'd', 'e', 'f']):
            result += self.current_char
            self.advance()
        return result

    def get_identifier(self):
        result = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return result

    def get_next_token(self):
        while self.current_char:
            if self.current_char.isspace() and self.current_char != '\n':
                self.skip_whitespace()
                continue

            if self.current_char == '\n':
                self.advance()
                return Token(TokenType.NEWLINE, '\n')

            if self.current_char == '#':
                while self.current_char and self.current_char != '\n':
                    self.advance()
                continue

            if self.current_char.isdigit():
                return Token(TokenType.NUMBER, self.get_number())

            if self.current_char.isalpha() or self.current_char == '_':
                identifier = self.get_identifier()
                if identifier in self.keywords:
                    return Token(TokenType.KEYWORD, identifier)
                return Token(TokenType.IDENTIFIER, identifier)

            if self.current_char in '+-*/=<>()':
                op = self.current_char
                self.advance()
                return Token(TokenType.OPERATOR, op)

            raise SyntaxError(f"Invalid character: {self.current_char}")

        return Token(TokenType.EOF, None)

class Compiler:
    def __init__(self):
        self.variables = {}
        self.current_section = "CPU"
        self.output = []

    def compile(self, source):
        lexer = Lexer(source)
        token = lexer.get_next_token()
        
        while token.type != TokenType.EOF:
            if token.type == TokenType.KEYWORD:
                if token.value == 'compute':
                    self.output.append(".CPU")
                    self.current_section = "CPU"
                elif token.value == 'draw':
                    self.output.append(".GPU")
                    self.current_section = "GPU"
                elif token.value == 'var':
                    token = lexer.get_next_token()
                    if token.type != TokenType.IDENTIFIER:
                        raise SyntaxError("Expected identifier after 'var'")
                    var_name = token.value
                    
                    token = lexer.get_next_token()
                    if token.type != TokenType.OPERATOR or token.value != '=':
                        raise SyntaxError("Expected '=' after variable name")
                    
                    token = lexer.get_next_token()
                    if token.type != TokenType.NUMBER:
                        raise SyntaxError("Expected number after '='")
                    
                    self.variables[var_name] = int(token.value, 0)
                    self.output.append(f"LDA {token.value}")
                    self.output.append(f"STA {hex(len(self.variables) + 0x20)}")

            elif token.type == TokenType.IDENTIFIER:
                if self.current_section == "GPU":
                    if token.value == "clear":
                        self.output.append("CLEAR")
                    elif token.value == "plot":
                        self.output.append("PLOT")
                    elif token.value == "rect":
                        token = lexer.get_next_token()
                        width = token.value
                        token = lexer.get_next_token()
                        height = token.value
                        self.output.append(f"RECT {width} {height}")
                    elif token.value == "setpos":
                        token = lexer.get_next_token()
                        x = token.value
                        token = lexer.get_next_token()  # Get y
                        y = token.value
                        self.output.append(f"SETX {x}")
                        self.output.append(f"SETY {y}")
                    elif token.value == "setcolor":
                        token = lexer.get_next_token()
                        self.output.append(f"SETC {token.value}")

            token = lexer.get_next_token()

        if self.current_section == "CPU":
            self.output.append("HALT")
        else:
            self.output.append("GHALT")

        return "\n".join(self.output)

if __name__ == "__main__":
    source_code = """
    compute
        var x = 5
        var y = 10
        var z = 0
        z = x + y

    """

    compiler = Compiler()
    assembly = compiler.compile(source_code)
    print("Generated Assembly:")
    print(assembly)

    assembler.main(assembly)