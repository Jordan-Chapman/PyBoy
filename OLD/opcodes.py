def bc(b, c, reg):
    reg["b"] = b
    reg["c"] = c

def de(d, e, reg):
    reg["d"] = d
    reg["e"] = e

def af(a, f, reg):
    reg["a"] = a
    reg["f"] = f

def hl(h, l, reg):
    reg["h"] = h
    reg["l"] = l

### MAIN ###

def exe(rom, pos, reg):
    byte = rom[pos]
    if byte == "01":
        bc(rom[pos+1], rom[pos+2], reg)
        pos += 2
    if byte == "
