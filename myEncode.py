
def encode(in):
    out = ""
    for c in in:
        ci = ord(c)

        ci+=20
        co = chr(ci)
        out += co

    return out

def decode(in):
    out = ""
    for c in in:
        ci = ord(c)
        ci -= 20
        co = chr(ci)
        out += co

    return out