import ast
import sys

def code2astPython(
        code
    ):
    """
    Transforme une chaine de caractere de code Python en un abre syntaxique abstrait.

    @param code_etu: une chaîne de caracteres contenant le code soumis

    @return l'Arbre Syntaxique Abstrait du code
    """
    return ast.parse(code)
    # avec dump.ast(...) renvoie un objet str plutot qu'un objet <class 'ast.Module'>

def dump_ast(tree):
    return ast.dump(tree)

class BoucleInfinie(Exception):
    pass

class Tracer():

  def __init__(self):
    """
        lines_trace = liste contenant les lignes executees lors de l'appel d'une fonction
        nb_max_entree = taille maximale de la liste de lines_trace avant de detecter une condition de boucle infini
        dico_event = liste des events a récupérer
    """
    self.lines_trace = []
    self.nb_max_entree = 400
    # call, line, return, exception, opcode
    self.dico_event = ["call", "line"]

  def tracer(self, frame, event, arg = None):
    """
        Definit la methode de trace
    """
    line_no = frame.f_lineno
    # Utiliser la synchronisation basee sur SIGALRM s'est averee peu fiable sur diverses installations python et est inutilisable sur Windows,
    # Une autre solution enviseagable serait d'appeler la fonction dans un thread avec un timeout defini.
    if(len(self.lines_trace)>self.nb_max_entree):
        raise BoucleInfinie()
    if event in self.dico_event:
        #print(f"A {event} at line number {line_no} ")
        self.lines_trace.append(line_no)
    return self.tracer

  def get_trace_and_result(self,fonction,*args,**kwargs):
    """
        Execute une fonction pour en extraire la trace d'execution.

        @param fonction: le nom de la fonction
        @param args: les arguments de la fonction ( mis un par un )

        @return un tuple trace, contenant la liste des lignes executees ainsi que , et res, le resultat de la fonction
    """
    # mise en place de la fonction trace
    sys.settrace(self.tracer)

    # appel de la fonction a tester
    try:
        res = fonction(*args)
    except BoucleInfinie as e:
        trace = self.lines_trace
        self.lines_trace = []
        sys.settrace(None)
        return(trace, "Boucle infinie")
    except: # catch *all* exceptions
        trace = self.lines_trace
        self.lines_trace = []
        sys.settrace(None)
        return(trace, str(sys.exc_info()))

    # on recupere la liste des lignes executees pendant la trace
    trace = self.lines_trace
    self.lines_trace = []
    sys.settrace(None)

    return (trace,res)

# Exemple d'appel à Tracer
# t = Tracer()
# print(t.get_trace_and_result(fun,1,2,3))

# Autres méthodes pour générer une trace :
# - utiliser le module hunter de python
#       trace_f = []
#       hunter.trace(function="g", action=(lambda x: trace_f.append(x)))
#       print(f(5)) #trace_f contient la liste des lignes executees
# - utiliser le module trace de python
#       tracer = trace.Trace(count=False, trace=True)
#       tracer.run("t.get_trace_and_result(fun,arg)")
#       r = tracer.results()

#=========================================================================================

#NODE : Constant-------------------------------------------------
def Constant2AES(self, node, symbolDic):
	return 'Constant_'+node.value.__class__.__name__

#NODE : Name-------------------------------------------------
def Name2AES(self, node, symbolDic):
	return symbolTranslate(node.id,symbolDic)

#NODE : Attribute-------------------------------------------------
def Attribute2AES(self, node, symbolDic):
	return node.attr

#NODE : Subscript-------------------------------------------------
def Subscript2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.value,symbolDic)
def Subscript2AESLevel1(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aesLevel1(node.value,symbolDic)

#NODE : BoolOp-------------------------------------------------
def BoolOp2AES(self, node, symbolDic):
	return node.__class__.__name__+node.op.__class__.__name__+' '+nodeList2aes(node.values,symbolDic)

#NODE : BinOp-------------------------------------------------
def BinOp2AES(self, node, symbolDic):
	return node.__class__.__name__+node.op.__class__.__name__+' '+node2aes(node.left,symbolDic)+' '+node2aes(node.right,symbolDic)

def BoolOpBinOp2AESLevel1(self, node, symbolDic):
	return node.__class__.__name__+node.op.__class__.__name__

#NODE : UnaryOp-------------------------------------------------
def UnaryOp2AES(self, node, symbolDic):
	return node.__class__.__name__+node.op.__class__.__name__+' '+node2aes(node.operand,symbolDic)

#NODE : Assign-------------------------------------------------
def Assign2AES(self, node, symbolDic):
	if len(node.targets) > 1 :
		print('WARNING : Assignment with a targets attribut of size greater than 1... is not considered!!')
	if isinstance(node.targets[0],ast.Tuple) :
		aes = ''
		for elem,val in zip(node.targets[0].elts,node.value.elts):
			aes += node.__class__.__name__+' '+node2aes(elem,symbolDic)+' '+node2aes(val,symbolDic)+' '
		return aes
	else :
		return node.__class__.__name__+' '+node2aes(node.targets[0],symbolDic)+' '+node2aes(node.value,symbolDic)
def Assign2AESLevel1(self, node, symbolDic):
	if len(node.targets) > 1 :
		print('WARNING : Assignment with a targets attribut of size greater than 1... is not considered!!')
	if isinstance(node.targets[0],ast.Tuple) :
		aes = ''
		for elem,val in zip(node.targets[0].elts,node.value.elts):
			aes += node.__class__.__name__+' '+node2aesLevel1(elem,symbolDic)+' '+node2aesLevel1(val,symbolDic)+' '
		return aes
	else :
		return node.__class__.__name__+' '+node2aesLevel1(node.targets[0],symbolDic)+' '+node2aesLevel1(node.value,symbolDic)

#NODE : AugAssign-------------------------------------------------
def AugAssign2AES(self, node, symbolDic):
	return node.__class__.__name__+node.op.__class__.__name__+' '+node2aes(node.target,symbolDic)+' '+node2aes(node.value,symbolDic)
def AugAssign2AESLevel1(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aesLevel1(node.target,symbolDic)+' '+node2aesLevel1(node.value,symbolDic)

#NODE : For, AsyncFor-------------------------------------------------
def For2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.target,symbolDic)+' '+node2aes(node.iter,symbolDic)

#NODE : Compare-------------------------------------------------
def Compare2AES(self, node, symbolDic):
	res = node.__class__.__name__+' '+node2aes(node.left,symbolDic)
	for i in range(len(node.ops)):
		res += ' '+node2aes(node.ops[i],symbolDic)+' '+node2aes(node.comparators[i],symbolDic)
	return res

#NODE : Call-------------------------------------------------
def Call2AES(self, node, symbolDic):
	return node.__class__.__name__+'_'+node2aes(node.func,symbolDic)+' '+nodeList2aes(node.args,symbolDic)

#NODE : List, Tuple-------------------------------------------------
def List2AES(self, node, symbolDic):
	if len(node.elts)==0:
		return 'Empty'+node.__class__.__name__
	else:
		return 'NonEmpty'+node.__class__.__name__

#NODE : While, If---------------------------------------------------
def If2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.test,symbolDic)
def If2AESLevel1(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aesLevel1(node.test,symbolDic)

#NODE : Import---------------------------------------------------
def Import2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+nodeList2aes(node.names,symbolDic)

#NODE : ImportFrom---------------------------------------------------
def ImportFrom2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.module,symbolDic)+' '+nodeList2aes(node.names,symbolDic)

#NODE : alias---------------------------------------------------
def alias2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.name,symbolDic)

#NODE : Assert---------------------------------------------------
def Assert2AES(self, node, symbolDic):
	return ''

#NODE : Expr---------------------------------------------------
def Expr2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.value,symbolDic)

#NODE : Return---------------------------------------------------
def Return2AES(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aes(node.value,symbolDic)
def Return2AESLevel1(self, node, symbolDic):
	return node.__class__.__name__+' '+node2aesLevel1(node.value,symbolDic)

#=========================================================================================

def initializeParameters(node, symbolDic):
	"""initialise les parametres"""
	i=1
	for elem in node.args:
		if elem.arg not in symbolDic.keys():
			symbolDic[elem.arg]='param'+str(i)
			i+=1

def generateNewVarSymbol(symbolDic):
	"""generation d'un nouveau symbole pour le dictionnaire de symboles"""
	l = ''.join(symbolDic.values())
	return 'var'+str(l.count('var')+1)

def symbolTranslate(id, symbolDic):
	"""traduction du symbole, verifie que le symbole n'existe pas"""
	if id not in symbolDic.keys():
		symbolDic[id] = generateNewVarSymbol(symbolDic)
	return symbolDic[id]

def nodeList2aes(l, symbolDic):
	"""iterer sur une liste de noeuds a traduire en une sequence de noeuds"""
	res = ''
	for elem in l:
		res += node2aes(elem, symbolDic)+' '
	return res[:(-1)]

def fonction2aesLevel2():
	ast.Constant.toAES = Constant2AES
	ast.Name.toAES = Name2AES
	ast.Attribute.toAES = Attribute2AES
	ast.Subscript.toAES = Subscript2AES
	ast.BoolOp.toAES = BoolOp2AES
	ast.BinOp.toAES = BinOp2AES
	ast.UnaryOp.toAES = UnaryOp2AES
	ast.Assign.toAES = Assign2AES
	ast.AugAssign.toAES = AugAssign2AES
	ast.For.toAES = For2AES
	ast.AsyncFor.toAES = For2AES
	ast.Compare.toAES = Compare2AES
	ast.Call.toAES = Call2AES
	ast.List.toAES = List2AES
	ast.Tuple.toAES = List2AES
	ast.If.toAES = If2AES
	ast.While.toAES = If2AES
	ast.Import.toAES = Import2AES
	ast.ImportFrom.toAES = ImportFrom2AES
	ast.alias.toAES = alias2AES
	ast.Assert.toAES = Assert2AES
	ast.Expr.toAES = Expr2AES
	ast.Return.toAES = Return2AES

def fonction2aesLevel1():
	ast.Constant.toAESLevel1 = Constant2AES
	ast.Name.toAESLevel1 = Name2AES
	ast.Subscript.toAESLevel1 = Subscript2AESLevel1
	ast.BoolOp.toAESLevel1 = BoolOpBinOp2AESLevel1
	ast.BinOp.toAESLevel1 = BoolOpBinOp2AESLevel1
	ast.Assign.toAESLevel1 = Assign2AESLevel1
	ast.AugAssign.toAESLevel1 = AugAssign2AESLevel1
	ast.If.toAESLevel1 = If2AESLevel1
	ast.While.toAESLevel1 = If2AESLevel1
	ast.Return.toAESLevel1 = Return2AESLevel1

def node2aes(node,symbolDic):
	"""traduire une instruction python en un symbole AES (niveau 2)"""
	try:
		return node.toAES(node,symbolDic)
	#other nodes
	except:
		UnprocessedNodes = [
			'FunctionDef',
			'Lt',
			'Eq',
			'Gt',
			'GtE',
			'LtE',
			'NotEq',
			'In',
			'NotIn',
			'NoneType',]
		if node.__class__.__name__ not in UnprocessedNodes:
			val = ''
			#val=node2aes(node.value,symbolDic) if node.__class__.__name__=='str' else ''
			print("WARNING : node",node.__class__.__name__,": default process",val)
		return node.__class__.__name__

def node2aesLevel1(node, symbolDic):
	"""traduire une instruction python en un symbole AES (niveau 1)"""
	try:
		return node.toAESLevel1(node,symbolDic)
	#other nodes
	except:
		return node.__class__.__name__

def ast_line_to_dict_item(astree, dic_line = dict()):
	"""creer un dictionnaire d'objet AST a partir d'un AST"""
	for field, value in ast.iter_fields(astree):
		if isinstance(value, list):
			for item in value:
				if isinstance(item, ast.AST) and hasattr(item, 'lineno'):
					#print(item, item.lineno)
					if item.lineno not in dic_line:
						dic_line[item.lineno] = item
					ast_line_to_dict_item(item, dic_line)
		elif isinstance(value, ast.AST):
			ast_line_to_dict_item(value, dic_line)
	return dic_line

def dict_item_to_dict_line(dic_aes_items, symbolDic, aeslevel):
	"""creer un dictionnaire de phrases pour chacune des lignes de l'AST"""
	res = dict()
	if aeslevel==2:
		fonction2aesLevel2()
	elif aeslevel==1:
		fonction2aesLevel1()
	for line in dic_aes_items:
		node = dic_aes_items[line]
		if isinstance(node,ast.FunctionDef): #initialization of the param symbols
			initializeParameters(node.args,symbolDic)
		if aeslevel==2:
			res[line] = node2aes(node,symbolDic)
		elif aeslevel==1:
			res[line] = node2aesLevel1(node,symbolDic)
		else :
			res[line] = node.__class__.__name__
	return res

def create_aes(astree, trace, aeslevel=2):
	"""Creer l'AES grace a l'AST et la trace d'execution"""
	res = ''
	symbolDic = {'print':'print', 'len':'len', 'range':'range', 'min':'min', 'max':'max'}
	dict_item = ast_line_to_dict_item(astree)
	dico_phrase = dict_item_to_dict_line(dict_item, symbolDic, aeslevel)
	for i in trace:
		res += dico_phrase[i] + "\n"
	return res

# Exemple d'utilisation :
# c = create_aes(astree, trace)
# print(c)

if __name__=="__main__":
    import importlib
    nom_module = 'exemple'
    spec = importlib.util.spec_from_loader(nom_module, loader=None)
    module_exemple = importlib.util.module_from_spec(spec)
    code_exemple = '''
def f(x):
    res = 0
    for i in range(x):
        res+=i
    if res > 10:
        return 3
    return res
'''
    exec(code_exemple, module_exemple.__dict__)
    sys.modules['module_exemple'] = module_exemple
    t = Tracer()
    trace, resultat = t.get_trace_and_result(module_exemple.f,5)
    print(trace)
    ast_exemple = code2astPython(code_exemple)
    print(ast_exemple)
    c = create_aes(ast_exemple, trace)
    print(c)
