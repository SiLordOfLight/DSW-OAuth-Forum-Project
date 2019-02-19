from myEncode import *

with open("static/badWords.json") as inFile:
    out = encode(inFile.read())

with open("static/badWords.json", 'w') as outFile:
    outFile.write(out)