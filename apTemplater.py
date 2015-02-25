__author__ = 'MagicalGentleman'
__name__ = 'apTemplater'

# Version 1.2

import argparse
import os
import sys
import re

whitespace = re.compile('\s')

class Tokens:

    defOpen = '('
    defClose = ')'
    bodyOpen = '{'
    bodyClose = '}'
    callOpen = '['
    callClose = ']'
    stringDef = '"'
    delimiter = ':'
    varChar = '~'
    # note that isMeta() only checks for
    # the Open and Close type tokens!

    # I could use regex instead but nah.
    def isMeta(self, token):
        if token == self.defOpen:
            return True
        elif token == self.defClose:
            return True
        elif token == self.bodyOpen:
            return True
        elif token == self.bodyClose:
            return True
        elif token == self.callOpen:
            return True
        elif token == self.callClose:
            return True
        else:
            return False


class Flags:
    declaring = True

flag = Flags()

class Arguments:
    pass

arguments = Arguments()

parser = argparse.ArgumentParser(description='A tool to parse ./autoprogram templates.')

parser.add_argument('source', nargs=1, help='Your binary source file.', metavar='source')
parser.add_argument('template', nargs=1, help='Your template file path.', metavar='template')
parser.add_argument('output', nargs='?', default=['output.prog'], help='Your generated autoprogram file.', metavar='output')

parser.parse_args(namespace=arguments)

sourcePath = os.path.normcase(arguments.source[0])
templatePath = os.path.normcase(arguments.template[0])
outputPath = os.path.normcase(arguments.output[0])

output = open(outputPath, 'w')

class ExitProgram:
    
    def error(self, message = "unspecified error."): # TODO: do better error messages!
        # I'll make this better I swear!
        sys.exit("Error: " + message)

    def success(self, message = "Operation complete."):
        print(message)
        sys.exit()

    def warning(self, message = "unspecified warning."):
        print("Warning!")
        print(message)
        self.success()

    def expected(self, required, actual):
        sys.exit("Error:\n    Expected: " + required + "\n    Got: " + actual)
    
exitProg = ExitProgram()

class SourceReader:

    sourceFile = open(sourcePath, 'r')

    def getNext(self):
        token = self.sourceFile.read(1)
        if (token == ''):
            exitProg.success()
        elif (token == '1') or (token == '0'):
            pass
        else:
            token = self.getNext()
        return int(token)


class TemplateReader:

    # The template file reader

    templateFile = open(templatePath, 'r')
    tokens = Tokens()
    token = ''
    isMeta = False
    reusIndex = {}
    varIndex = {}
    address = 0

    def jump(self, addr):
        self.templateFile.seek(addr)
        self.address = addr
        return

    def jumpToKey(self, key):
        if key in self.reusIndex:
            self.jump(self.reusIndex[key])
        else:
            exitProg.error()
        return

    def varFetch(self, varName):
        if varName in self.varIndex:
            return self.varIndex[varName]
        else:
            exitProg.error()
        return

    def getNext(self):
        # Returns the token and
        # also returns True if
        # the token is meta.
        self.token = self.templateFile.read(1)
        if self.token == '':
            exitProg.warning("Source is larger than the templated device.")
        self.address = self.templateFile.tell()
        if self.tokens.isMeta(self.token):
            self.isMeta = True
        else:
           self.isMeta = False
        # The retrieved token is returned by this
        # method, but it is recommended that you
        # get the token by referring to self.token
        return self.token

    def skipws(self):
        # Skip whitespace.
        # If whitespace is skipped, this
        # will stop at the next
        # non-whitespace char.
        # otherwise there will be no movement.
        while whitespace.match(self.token):
            self.getNext()
        return

    def advance(self):
        # get next non-whitespace char.
        # use this only when you need to.
        self.getNext()
        self.skipws()
        return

    def isNum(self):
        try:
            int(self.token)
            return True
        except ValueError:
            return False

    def isVar(self):
        if self.token == self.tokens.varChar:
            return True
        else:
            return False

    def isReus(self):
        if self.isMeta or self.isNum():
            return False
        else:
            return True

    def getNum(self): # TODO: make the getNum() method stricter, and add error messages.
        charAcc = ''
        while not (self.isMeta or whitespace.match(self.token)):
            charAcc += self.token
            self.getNext()
        return int(charAcc)

    def getName(self):
        charAcc = ''
        while not (self.isMeta or whitespace.match(self.token)):
            charAcc += self.token
            self.getNext()
        return charAcc

    def getString(self):
        charAcc = ''
        self.getNext() # get past the opening stringDef
        while self.token != self.tokens.stringDef:
            charAcc += self.token
            self.getNext()
        return charAcc

source = SourceReader()
template = TemplateReader()


def varHandler():
    # Handle var declarations
    template.getNext() # remove leading varChar
    varName = template.getName()
    # Search for body opening bracket:
    template.advance() # advance to next valid char.
    if template.token == template.tokens.bodyOpen:
        template.advance() # Bracket found, advance to string.
        if template.token != template.tokens.stringDef:
            exitProg.expected(template.tokens.stringDef, template.token)
        else:
            zeroName = template.getString()
        template.advance() # advance to the delimiter
        if template.token != template.tokens.delimiter:
            exitProg.expected(template.tokens.delimiter, template.token)
        template.advance() # advance to second string.
        if template.token != template.tokens.stringDef:
            exitProg.expected(template.tokens.stringDef, template.token)
        else:
            oneName = template.getString()
        template.varIndex[varName] = [zeroName, oneName] # Put retrieved data in dict
        template.advance() # advance to bodyClose
        if template.token == template.tokens.bodyClose:
            return
        else:
            exitProg.error("expected " + template.tokens.bodyClose + " after var body.")
    else:
        exitProg.error("expected " + template.tokens.bodyOpen + " after var declaration.")

def reusHandler():
    reusName = template.getName() # Get the reusable template name
    template.skipws() # Make sure we are at defClose
    if template.token != template.tokens.defClose:
        exitProg.error("expected " + template.tokens.defClose + " after template declaration.")
    template.advance() # advance to bodyOpen
    if template.token != template.tokens.bodyOpen:
        exitProg.error("expected " + template.tokens.bodyOpen + " after template declaration.")
    # Copy the template name and address for later calls.
    template.reusIndex[reusName] = template.address

    # Now we must advance past the reusable template's body to
    # the next declaration:

    bodyDepth = 0 # Body bracket counter so we know when we leave the template.

    while True: # This loop will exit on a break later.
        # Get next meta declaration
        while not template.isMeta:
            template.advance()
        # Examine the meta chars:
        if template.token == template.tokens.bodyOpen:
            bodyDepth += 1
        elif template.token == template.tokens.bodyClose:
            bodyDepth -= 1
        # exit loop when past all nested brackets:
        if bodyDepth == 0:
            break
        template.advance()
    return

def defHandler():
    template.advance() # find the identifying character
    if template.isNum():
        flag.declaring = False # leave declaration mode.
    elif template.isVar():
        varHandler()
    elif template.isReus():
        reusHandler()
    else:
        exitProg.error()
    return

def commonParse():
    template.getNext() # get the char to check
    while template.token != template.tokens.bodyClose:
        if template.token == template.tokens.callOpen:
            callHandler()
        elif template.token == template.tokens.defOpen:
            template.advance()
            if template.isNum():
                countParse()
            else:
                exitProg.error("you cannot declare within a loop!")
        elif template.token == template.tokens.stringDef:
            output.write(template.getString())
        template.getNext()

def callHandler():
    # Handles var and template calls.
    if template.token != template.tokens.callOpen:
        exitProg.error()
    template.advance() # advance to name
    callName = template.getName() # Get name
    if callName in template.reusIndex:
        returnAddress = template.address
        template.jumpToKey(callName)
        commonParse()
        template.jump(returnAddress)
    elif callName in template.varIndex:
        output.write(template.varFetch(callName)[source.getNext()]) # The only line that reads from source xD
    else:
        exitProg.error("undefined template or var call")
    return

def countParse():
    # IMPORTANT!
    # countParse assumes that the first digit
    # of the count is the current token!
    count = 0
    if template.isNum():
        count = template.getNum()
    else:
        exitProg.error("expected a number")
    template.skipws() # Make sure we are at the defClose char.
    if template.token != template.tokens.defClose:
        exitProg.error("expected " + template.tokens.defClose)
    template.advance() # Advance to bodyOpen char.
    if template.token != template.tokens.bodyOpen:
        exitProg.error("expected " + template.tokens.bodyOpen)
    # save address at bodyOpen char:
    loopStart = template.address

    # Main parser loop:
    while count > 0:
        count -= 1
        commonParse()
        if count > 0:
            template.jump(loopStart)
        else:
            break
    return

def mainParse():
    while flag.declaring:
        template.advance() # find next declaration token
        if template.isMeta:
            if template.token == template.tokens.defOpen:
                defHandler()
            else:
                exitProg.error("expected " + template.tokens.defOpen)
        else:
            pass # comments are anything outside bracketed statements.

    # Once the declare flag is deactivated, it means we are at the first
    # counter statement.
    countParse()
    # more declarations can be made after this:
    flag.declaring = True
    # declarations() can be looped until the file end is reached.

while True:
    # The program will exit
    # when the end of the source
    # file is reached.
    # This is done from within
    # the source object.
    mainParse()
