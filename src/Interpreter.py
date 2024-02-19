from dataclasses import dataclass
import ast
from collections import deque

# number of parantheses open for a lambda expression
par_cnt = 0
# if we are still parsing a lambda expression
is_lambda = False
# nr of values that will replace the ids in a lambda expression
cnt = 0
# dictionary that will contain the ids and their corresponding values
dict_id_val = {}

@dataclass
class Expr:
    def evaluate(self) -> str:
        raise NotImplementedError('Subclasses should implement this!')

@dataclass
class Id(Expr):
    value: str

    def evaluate(self) -> str:
        return self.value
    
    def replace_by_value(self, value: str) -> str:
        self.value = value
        return self.value

@dataclass	
class Lambda(Expr):
    id: list[Expr]
    body: Expr
    values: list[Expr] or []

    def evaluate(self) -> str:
        # evaluate ids
        ids = []
        for id in self.id:
            ids.append(id.evaluate())
        
        # if the values list is empty, the lambda is a value for another lambda
        if self.values == []:
            res = self.body.evaluate()
            str_output = ''
            for id in ids:
                str_output += f'lambda {id}: '
            new_res = ''
            if '(' in res:
                for i in range(len(res)):
                    if res[i].isalnum():
                        new_res += '(' + res[i] + ')'
                    if i < len(res) - 2 and res[i].isalnum() and res[i + 2] != ')':
                        new_res += ','
                res = new_res
            else:
                new_res += '(' + res[0] + ')'
                res = new_res
            str_output += res
            return str_output
        
        values = []
        for value in self.values:
            values.append(value.evaluate())
        
        global dict_id_val
        dict_id_val = dict(zip(ids, values))

        # evaluate body
        res = self.body.evaluate()

        # number of values that will replace the ids
        global cnt
        cnt = len(values)

        # boolean variable to check if the values are of lambda type
        is_lambda = any('lambda' in value for value in values)

        # if the body contains a list we have to put commas between elements
        if '(' in res:
            new_res = ''
            for i in range(len(res)):
                if res[i] in '()':
                    new_res += res[i]
                if res[i].isalnum():
                    new_res += '(' + res[i] + ')'
                if is_lambda == False and i < len(res) - 2 and res[i].isalnum() and res[i + 2] != ')':
                    new_res += ','
            res = new_res
        
        for i in range(len(values)):
            # if the value contains a list we have to put commas between elements
            # if the value contains lambdas we don't put commas between elements
            if '(' in values[i] and 'lambda' not in values[i]:
                new_value = ''
                for j in range(len(values[i])):
                    new_value += values[i][j]
                    if j < len(values[i]) - 2 and values[i][j].isalnum() and values[i][j + 2] != ')':
                        new_value += ','
                values[i] = new_value

        # recreate the lambda expression so that it has the right syntax for 
        # ast module from python to evaluate it
        lambda_expr = ''
        # for each id in ids we put a lambda before it and : after it
        lambda_expr += '('
        for id in ids:
            lambda_expr += f'lambda {id}: '
        
        # add the body
        lambda_expr += res
        lambda_expr += ')'
        # add each value in its own parantheses
        for value in values:
            lambda_expr += f'({value})'

        # evaluate the lambda expression
        tree = ast.parse(lambda_expr, mode='eval')
        result = eval_lambda(tree.body)

        # make output into string
        str_result = str(result)
        # make output into the right format
        str_result = str_result.replace(',', '').replace('(', '( ').replace(')', ' )')
        return str_result

@dataclass
class Plus(Expr):
    elements: list[Expr]

    def evaluate(self) -> int:
        result = []
        # the plus operation will add every number element in its elements list of numbers and lists
        for element in self.elements:
            result.append(element.evaluate())
        
        result = ' '.join(result)

        # for each id in dict_id_val replace it with the corresponding value
        global dict_id_val
        for id in dict_id_val:
            result = result.replace(id, dict_id_val[id])
        
        # we add all the numbers in result
        result = result.replace('(', '').replace(')', '')
        list_result = [int(s) for s in result.split()]
        sum_result = sum(list_result)
        return str(sum_result)
    
@dataclass
class Concat(Expr):
    # you can concatenate a number with a list
    # you can concatenate a list with a list
    elements: list[Expr]

    def evaluate(self) -> str:
        # concatenate the elements in the list
        result = []
        
        for element in self.elements:
            if isinstance(element, Number):
                result.append(element.evaluate())
            elif isinstance(element, List):
                if len(element.elements) != 0:
                    result.append(element.get_list_elements())
            elif isinstance(element, Plus):
                result.append(element.evaluate())
            elif isinstance(element, Id):
                result.append(element.evaluate())
            elif isinstance(element, Lambda):
                res = element.evaluate()
                result.append(res)
            else:
                raise Exception('Invalid token!')
        return ' '.join(result)

@dataclass
class List(Expr):
    elements: list[Expr]

    def evaluate(self) -> str:
        result = []

        # if elements is just an empty list
        if len(self.elements) == 0:
            result.append('()')
            return ' '.join(result)
        
        # create a list of the elements in string format
        result.append('(')
        
        for element in self.elements:
            result.append(element.evaluate())

        global cnt	
        if cnt > 0:
            cnt -= 1
            # eliminate first (
            result.pop(0)
        else:
            result.append(')')
        
        return ' '.join(result)
    
    # for concat operation
    def get_list_elements(self) -> str | None:
        result = []
        if len(self.elements) == 0:
            return ''
        for element in self.elements:
            result.append(element.evaluate())
        return ' '.join(result)

@dataclass
class Number(Expr):
    value: str

    def evaluate(self) -> str:
        return self.value

# evaluate lambda using the ast module from python
def eval_lambda(node):
    if isinstance(node, ast.Lambda):
        func = eval(compile(ast.Expression(node), filename='<ast>', mode='eval'))
        return func
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Call):
        func = eval_lambda(node.func)
        args = [eval_lambda(arg) for arg in node.args]
        return func(*args)
    elif isinstance(node, ast.List):
        return (eval_lambda(elt) for elt in node.elts)
    elif isinstance(node, ast.Tuple):
        return tuple(eval_lambda(elt) for elt in node.elts) 
    else:
        raise Exception(f'Unknown node {node}')

class Interpreter:
    def __init__(self, result_list: Expr) -> None:
        self.result_list = result_list
        self.output = []
    
    def evaluate(self) -> None:
        print(self.result_list.evaluate())
        
        # '(lambda x: lambda y: lambda z: (((x) (z)) (y))) (lambda x: lambda y: (x)) (1) (2)'
        # '(lambda x: lambda y: (((x) (y))(x)))(lambda x: lambda y: (x))(lambda x: lambda y: (y))(1)(2)'
        # '(lambda x: ((x), (x))) ((1, 2))'
        # '(lambda x: lambda y: ((y), (x))) ((1, 2, 3)) ((4, 5, 6))'
        # '(lambda x: lambda y: lambda z: (x)) (1) (2) (3)'
        # '(lambda x: lambda x: (x)) (1) (2)'


class Parser:
    def __init__(self, token_list: list[tuple[str, str]]) -> None:
        # turn the list into a deque for easier parsing
        self.token_list = deque(token_list)

    def parse_num(self) -> Expr:
        # pop NR
        nr = self.token_list.popleft()[1]
        # eliminate spaces from nr
        nr = nr.replace(' ', '')
        return Number(nr)
        
    def parse(self) -> Expr:
        global par_cnt
        global is_lambda
        if len(self.token_list) == 0:
            return None
        elif self.token_list[0][0] == 'NR':
            if is_lambda == False:
                par_cnt = 0
            return self.parse_num()
        elif self.token_list[0][0] == 'OPAR' and self.token_list[1][0] == 'PLUS':
            if is_lambda == False:
                par_cnt = 0
            return self.parse_plus()
        elif self.token_list[0][0] == 'OPAR':
            if is_lambda == False:
                par_cnt += 1
            return self.parse_nested_expr()
        elif self.token_list[0][0] == 'CONCAT':
            if is_lambda == False:
                par_cnt = 0
            return self.parse_concat()
        elif self.token_list[0][0] == 'PLUS':
            if is_lambda == False:
                par_cnt = 0
            return self.parse_plus()
        elif self.token_list[0][0] == 'ID':
            if is_lambda == False:
                par_cnt = 0
            return self.parse_id()
        elif self.token_list[0][0] == 'LAMBDA':
            if (is_lambda == True):
                return self.parse_lambda_values()
            else:
                is_lambda = True
                res = self.parse_lambda()
                par_cnt = 0
                is_lambda = False
                return res
        elif self.token_list[0][0] == 'CPAR':
            # pop CPAR
            self.token_list.popleft()
            return self.parse()
        elif self.token_list[0][0] == 'NEWLINE':
            # pop NEWLINE
            self.token_list.popleft()
            return self.parse()
        elif self.token_list[0][0] == 'TAB':
            # pop TAB
            self.token_list.popleft()
            return self.parse()
        else:
            raise Exception('Invalid token!')
        
    def parse_id(self) -> Expr:
        # pop ID
        id = self.token_list.popleft()[1]
        # eliminate spaces from id
        id = id.replace(' ', '')
        return Id(id)

    # parse lambdas  
    def parse_lambda(self) -> Expr:
        global par_cnt
        ids = []
        while self.token_list[0][0] == 'LAMBDA':
            
            # pop LAMBDA
            self.token_list.popleft()
            # parse ID
            ids.append(self.parse_id())
            # pop SEPARATOR
            self.token_list.popleft()

        # parse body
        body = self.parse()

        values = []
        # until we close all the parantheses that we opened since the first lambda
        # there will still be values to be given to the ids
        while par_cnt != 0 and len(self.token_list) != 0:
            values.append(self.parse())
            par_cnt -= 1

        return Lambda(ids, body, values)
    
    # parse the values that will be given to the ids, that are also lambdas
    def parse_lambda_values(self) -> Expr:
        ids = []
        while self.token_list[0][0] == 'LAMBDA':
            # pop LAMBDA
            self.token_list.popleft()
            # parse ID
            ids.append(self.parse_id())
            # pop SEPARATOR
            self.token_list.popleft()

        # parse body of lambda
        body = self.parse()

        # the values will be an empty list
        return Lambda(ids, body, [])

    # parse lists
    def parse_nested_expr(self) -> Expr:
        # pop OPAR
        self.token_list.popleft()
        
        elem = []
        while len(self.token_list) != 0 and self.token_list[0][0] != 'CPAR':
            res = self.parse()
            if res != None:
                elem.append(res)

        # pop CPAR
        if len(self.token_list) != 0:
            self.token_list.popleft()
        return List(elem)
    
    # parse concatenation
    def parse_concat(self) -> Expr:
        # pop CONCAT
        self.token_list.popleft()
        # pop OPAR
        self.token_list.popleft()
        # elements that will be concatenated
        elem = []
        while self.token_list[0][0] != 'CPAR':
            elem.append(self.parse())

        # pop CPAR
        self.token_list.popleft()
        return Concat(elem)
    
    # parse plus
    def parse_plus(self) -> Expr:
        # pop OPAR
        self.token_list.popleft()
        # pop PLUS
        self.token_list.popleft()
        # elements that will be added
        elem = []
        while self.token_list[0][0] != 'CPAR':
            elem.append(self.parse())

        # pop CPAR
        self.token_list.popleft()
        return Plus(elem)
