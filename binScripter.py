__author__ = 'MagicalGentleman'

# Version 1.5

################################################################################
##    binScripter Ver. 2, A template based binary formatter.                  ##
##    Copyright (C) 2015  MagicalGentleman (Quinn Unger)                      ##
##                                                                            ##
##    This program is free software: you can redistribute it and/or modify    ##
##    it under the terms of the GNU General Public License as published by    ##
##    the Free Software Foundation, either version 3 of the License, or       ##
##    (at your option) any later version.                                     ##
##                                                                            ##
##    This program is distributed in the hope that it will be useful,         ##
##    but WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           ##
##    GNU General Public License for more details.                            ##
##                                                                            ##
##    You should have received a copy of the GNU General Public License       ##
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.   ##
################################################################################


import argparse
import os
import sys
import re

parser = argparse.ArgumentParser(description='A tool to parse ./autoprogram templates.')

parser.add_argument('-r', '--recursionlimit', type=int, help="set the parser's recursion limit", default=0)
parser.add_argument('source', nargs = 1, help = 'Your binary source (in a text file).')
parser.add_argument('template', nargs=1, help='Your template file path.')
parser.add_argument('output', nargs='?', default=['output.prog'], help='Your generated autoprogram file.')

args = parser.parse_args()

# Some duct tape to stop infinite recursion
# TODO: replace this with loop detection. e.g. check for second recursive call of func but no source advance
recursionLimit = 512
if args.recursionlimit > 0:
    recursionLimit = args.recursionlimit
sys.setrecursionlimit(recursionLimit)

sourcePath = os.path.normcase(args.source[0])
templatePath = os.path.normcase(args.template[0])
outputPath = os.path.normcase(args.output[0])

print(
    "Writing from binary source file '" + sourcePath + "' to destination file '" + outputPath + "' using template '" + templatePath + "'...\n")

output = open(outputPath, 'w')

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
    escape = '\\'
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

class EscapeCharacters:

    n = '\n'
    t = '\t'

    def convert(self, char):
        # takes the escape character minus the backslash
        if char == 'n':
            return self.n
        elif char == 't':
            return self.t
        else:
            return char

class Flags:
    declaring = True

flag = Flags()

class ExitProgram:
    def errorHeader(self):
        return "Error:\nIn " + template.templateFile.errorLoc() + ":\n"

    def error(self, message = "unspecified error."):
        sys.exit(self.errorHeader() + "    " + message)

    def success(self, message = "Operation complete."):
        print(message)
        sys.exit()

    def warning(self, message = "unspecified warning."):
        print("Warning!")
        print(message)
        self.success()

    def expected(self, required, actual):
        sys.exit(self.errorHeader() + "    Expected: " + required + "\n    Got: " + actual)

class SourceReader:

    sourceFile = open(sourcePath, 'r')
    sourceBuff = []
    bitCount = 0
    currBit = 0

    def __init__(self):
        while (True):
            token = self.sourceFile.read(1)
            if token == '':
                self.sourceBuff.append(token)
                self.sourceFile.close()
                print("Source loaded.")
                return
            elif (token == '1') or (token == '0'):
                self.bitCount += 1
                self.sourceBuff.append(token)

    def getNext(self):
        token = self.sourceBuff[self.currBit]
        if (token == ''):
            exitProg.success()
        else:
            self.currBit += 1
        return int(token)


class TemplateBuffer:
    # The buffer for the main template file.
    # This should include libraries too, eventually.
    # The buffer is designed so that managing when
    # libraries are inserted and what file you're in
    # is completely invisible to whatever is using this
    # class' methods.

    currentFile = 0
    address = [[0, 0]]

    def __init__(self, mainTemplatePath):
        # build up 3 dimensional list structure
        self.buffer = []
        self.buffer.append([])
        self.buffer[0].append([])

        self.fileName = [mainTemplatePath]

        templateFile = [[open(mainTemplatePath, 'r'), mainTemplatePath]]

        fileID = [0]
        line = [0]
        token = ''

        self.fileCount = 0
        activeFileDepth = 0

        while True:
            currFile = fileID[activeFileDepth]
            token = templateFile[currFile][0].read(1)
            self.buffer[currFile][line[activeFileDepth]].append(token)
            if token == '\n':
                self.buffer[currFile].append([])
                line[activeFileDepth] += 1
            elif token == '#':
                token = templateFile[currFile][0].read(1)
                temp = token
                self.buffer[currFile][line[activeFileDepth]].append(token)
                while (not whitespace.match(token)) and (token != ''):
                    token = templateFile[currFile][0].read(1)
                    if not whitespace.match(token):
                        temp += token
                    self.buffer[currFile][line[activeFileDepth]].append(token)
                if temp == "include":
                    token = templateFile[currFile][0].read(1)
                    self.buffer[currFile][line[activeFileDepth]].append(token)
                    if token == '"':
                        token = templateFile[currFile][0].read(1)
                        self.buffer[currFile][line[activeFileDepth]].append(token)
                        temp = token
                        while (token != '"') and (token != ''):
                            token = templateFile[currFile][0].read(1)
                            if token != '"':
                                temp += token
                            self.buffer[currFile][line[activeFileDepth]].append(token)
                    else:
                        temp += token
                        while (not whitespace.match(token)) and (token != ''):
                            token = templateFile[currFile][0].read(1)
                            if not whitespace.match(token):
                                temp += token
                            self.buffer[currFile][line[activeFileDepth]].append(token)

                    # open new file
                    newTemplate = os.path.normcase(temp)
                    templateFile.append([open(newTemplate, 'r'), newTemplate])

                    print("Including template " + newTemplate)

                    self.fileCount += 1  # increase file count

                    # link to next file
                    self.buffer[currFile][line[activeFileDepth]].append(self.fileCount)

                    # new file entry
                    self.buffer.append([])
                    self.buffer[self.fileCount].append([])

                    # new file address index entry
                    self.address.append([0, 0])

                    # new file name entry
                    self.fileName.append(newTemplate)

                    activeFileDepth += 1  # increase depth count
                    fileID.append(self.fileCount)  # new file ID in file process stack
                    line.append(0)  # new line count line process stack
                else:
                    # more preprocessor stuff will go here eventually
                    pass
            elif token == '':
                templateFile[currFile][0].seek(0)
                # when full support for libraries are added, more code
                # should go here.
                if activeFileDepth == 0:
                    print("Template file(s) loaded.")
                    i = 0
                    while i <= self.fileCount:
                        templateFile[i][0].close()
                        i += 1
                    return
                else:
                    # This returns to the previous buffer
                    # for the previous file
                    # link to previous active file
                    self.buffer[currFile][line[activeFileDepth]].pop()
                    self.buffer[currFile][line[activeFileDepth]].append(fileID[activeFileDepth - 1])
                    # pop finished file
                    activeFileDepth -= 1
                    fileID.pop()
                    line.pop()
        return

    def read(self):
        token = self.buffer[self.currentFile][self.address[self.currentFile][0]][self.address[self.currentFile][1]]
        self.address[self.currentFile][1] += 1
        if token == '\n':
            self.address[self.currentFile] = [self.address[self.currentFile][0] + 1, 0]
        elif type(token) is int:
            self.currentFile = token
            return self.read()
        return token

    def jump(self, address):
        self.currentFile = address[0]
        self.address[self.currentFile] = [address[1], address[2]]
        return

    def getAddress(self):
        return [self.currentFile, self.address[self.currentFile][0], self.address[self.currentFile][1]]

    def errorLoc(self):
        return "'" + self.fileName[self.currentFile] + "', Line " + str(self.address[self.currentFile][0])

class TemplateReader:

    # The template file reader

    templateFile = TemplateBuffer(templatePath)
    tokens = Tokens()
    escape = EscapeCharacters()
    token = ''
    isMeta = False
    reusIndex = {}
    varIndex = {}
    address = [0, 0, 0]

    def jump(self, addr):
        self.templateFile.jump(addr)
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
        self.token = self.templateFile.read()
        if self.token == '':
            source.getNext()  # This will successfully exit the program if the whole source has been read.
            exitProg.warning("Source is larger than the templated device.")
        self.address = self.templateFile.getAddress()
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
            if self.token == self.tokens.escape:
                self.getNext()
                charAcc += self.escape.convert(self.token)
            else:
                charAcc += self.token
            self.getNext()
        return charAcc

source = SourceReader()
template = TemplateReader()
exitProg = ExitProgram()

def passBody():
    # used to advance past an element's body.
    bodyDepth = 0 # Body bracket counter so we know when we leave the element.

    while True: # This loop will exit on a break later.
        # Get next meta declaration
        while not template.isMeta:
            template.getNext()
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

def varHandler():
    # Handle var declarations
    template.getNext() # remove leading varChar
    varName = template.getName()
    # Search for body opening bracket:
    template.advance() # advance to next valid char.
    if template.token == template.tokens.bodyOpen:
        template.advance() # Bracket found, advance to first item.
        if template.token == template.tokens.stringDef:
            zeroName = [template.getString(), False]
        elif template.token == template.tokens.callOpen:
            template.getNext()
            callName = template.getName()
            if callName in template.reusIndex:
                zeroName = [template.reusIndex[callName], True] # True == template call address
            elif callName in template.varIndex:
                exitProg.expected("a template call", "a var reference")
            else:
                exitProg.expected("a valid template call", callName + " (undefined!)")
        else:
            exitProg.expected("a string or a template call", template.token)

        template.advance() # advance to the delimiter
        if template.token != template.tokens.delimiter:
            exitProg.expected(template.tokens.delimiter, template.token)

        template.advance() # advance to second item.
        if template.token == template.tokens.stringDef:
            oneName = [template.getString(), False]
        elif template.token == template.tokens.callOpen:
            template.getNext()
            callName = template.getName()
            if callName in template.reusIndex:
                oneName = [template.reusIndex[callName], True] # True == template call address
            elif callName in template.varIndex:
                exitProg.expected("a template call", "a var reference")
            else:
                exitProg.expected("a valid template call", callName + " (undefined!)")
        else:
            exitProg.expected("a string or a template call", template.token)

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
    passBody()
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
        value = template.varFetch(callName)[source.getNext()] # The only line that reads from source xD
        if value[1] == True:  # if the value holds a jump address...
            returnAddress = template.address
            template.jump(value[0])
            commonParse()
            template.jump(returnAddress)
        else:
            output.write(value[0])
    else:
        exitProg.error("undefined template or var call: " + callName)
    return

def countParse():
    # IMPORTANT!
    # countParse assumes that the first digit
    # of the count is the current token!
    count = 0
    if template.isNum():
        count = template.getNum()
        # Ignore a zero count.
        if count == 0:
            template.advance()
            passBody()
            return # Leave function now!
    else:
        exitProg.expected("an integer", template.token)
    template.skipws() # Make sure we are at the defClose char.
    if template.token != template.tokens.defClose:
        exitProg.expected(template.tokens.defClose, template.token)
    template.advance() # Advance to bodyOpen char.
    if template.token != template.tokens.bodyOpen:
        exitProg.expected(template.tokens.bodyOpen, template.token)
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
                exitProg.expected(template.tokens.defOpen, template.token)
        else:
            pass # comments are anything outside bracketed statements.

    # Once the declare flag is deactivated, it means we are at the first
    # counter statement.
    countParse()
    # more declarations can be made after this:
    flag.declaring = True
    # mainParse() can be looped until the file end is reached.

while True:
    # The program will exit normally
    # when the end of the source
    # file is reached.
    # This is done from within
    # the source object.

    try:
        mainParse()
    except RuntimeError as err:
        if err.args[0] == "maximum recursion depth exceeded":
            exitProg.error("Recursion limit exceeded.")
        else:
            raise
