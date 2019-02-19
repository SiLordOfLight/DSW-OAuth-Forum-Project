def encode(inp):
    out = ""
    for c in inp:
        ci = ord(c)

        ci-=10
        co = chr(ci)
        out += co

    return out

def decode(inp):
    out = ""
    for c in inp:
        ci = ord(c)
        ci += 10
        co = chr(ci)
        out += co

    return out