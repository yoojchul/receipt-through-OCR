import os, io, sys
import re

def detect_text(path):
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    merged = []
    words = texts[0].description.split("\n")
    i = 1   # concat title in a word if possible
    for w in words:
        xs, ys = [], []
        while  i <  len(texts) and texts[i].description in w:
            for vertex in texts[i].bounding_poly.vertices:
                xs.append(vertex.x)
                ys.append(vertex.y)
            i += 1
        if xs == []:
            continue
        left_low = (min(xs), min(ys))
        left_high = (min(xs), max(ys))
        right_low = (max(xs), min(ys))
        right_high = (max(xs), max(ys))
        merged.append([w, left_low, left_high, right_low, right_high])

    return(merged)  # list of [word, (), (), (), ()]

class ParsingError(Exception):

        def __init__(self, *args):
            self.message = "parsing error at " + args[0] + ". " + args[1] + " is expected."

        def __str__(self):
            return (self.message)

def parser(path):
    targets = []
    f = open(path)
    state = 0
    while True:
        if state == 0:
            line = f.readline()
            if not line: 
                raise ParsingError("EOF", "-mark")
            tokens = re.findall(r'\S+', line.strip())
            if tokens[0].startswith('-'):
                state = 1
            else:
                raise ParsingError(tokens[0], "-mark")
        elif state == 1:
            mark = [tokens[0]]
            line = f.readline()
            if not line:
                raise ParsingError("EOF", "condition:")
            tokens = re.findall(r'\S+', line.strip())
            if tokens[0].endswith(':'): 
                state = 2
            else:
                raise ParsingError(tokens[0], "condition:")
        elif state == 2:
            conditions = [None, None, None, None, None]
            i = 0
            while i < len(tokens):
                if tokens[i] == "index:":
                    conditions[0] = tokens[i+1]
                elif tokens[i] == "format:":
                    conditions[1] = tokens[i+1]
                elif tokens[i] == "string:":
                    conditions[2] = tokens[i+1]
                elif tokens[i] == "location:":
                    conditions[3] = tokens[i+1]
                elif tokens[i] == "action:":
                    conditions[4] = tokens[i+1]
                else:
                    ParingError(tokens[i], "conditions:")
                i = i + 2
            mark.append(conditions)
            line = f.readline()
            if not line: 
                targets.append(mark)
                break
            tokens = re.findall(r'\S+', line.strip())
            if tokens[0].startswith('-'):
                state = 1
                targets.append(mark)
            elif tokens[0].endswith(':'):
                state = 2
            else:
                raise ParsingError(tokens[0], "-mark or condition:")
    return(targets)
    


rules = parser(sys.argv[1])
print(rules)

texts = detect_text(sys.argv[2])
for t in texts:
    t[0] = t[0].replace(' ', '')
#    print(t[0])

landscape = 0
for m in texts[:11]:
    diffx = m[4][0] - m[1][0] # right_high - left_low
    diffy = m[4][1] - m[1][1]
    if diffx >= diffy:
        landscape -= 1
    else:
        landscape += 1

max_x = 0
max_y = 0
for t in texts:
    if max_x < t[4][0]: max_x = t[4][0]
    if max_y < t[4][1]: max_y = t[4][1]

for r in rules:   # [-company_name, [<3, None, ~seoul, None, None], ...]
    for conditions in r[1:]:   # check syntax  
        if conditions[0] != None: # index:
            if not conditions[0][0] in ['<', '>', '=']:
                raise ParingError(conditions[0], "<, >, =")
        elif conditions[3] != None: # location:
            if not conditions[3][0] in ['<', '>', '^', '_']:
                raise ParingError(conditions[3], "<, >, ^, _")

coord = {}  # for location:
used = []   # index of which t is found
for r in rules:
    print(r[0])
    found = False
    for conditions in r[1:]:
        if conditions[0] != None: # index:
            op = conditions[0][0] 
            num = int(conditions[0][1:])
        if conditions[2] != None: # string:
            voca = conditions[2].split(',')
            nega = []
            posi = []
            for v in voca:
                if v[0] == '~':
                    nega.append(v[1:])
                else:
                    posi.append(v)
        if conditions[3] != None: # location:
            loc = conditions[3][0] 
            if not loc in ['<', '>', '^', '_']:
                raise ParsingError(conditions[3], "<, >, ^, or _")
        if conditions[4] != None: 
            act = conditions[4][0]
            if not act in ['~', '=']:
                raise ParsingError(conditions[4], "~ or =")

        for ti, t in enumerate(texts):
            if ti in used: continue
            flag = True 
            if conditions[0] != None: # index:
                ind = texts.index(t)
                if op == '<' and ind >= num:
                    continue
                elif op == '>' and ind <= num:
                    continue
                elif op == '-' and ind != num:
                    continue
            if conditions[1] != None: # format:
                match = conditions[1]
                word = t[0]
                if len(match) > len(word): continue # next
                i = 0 
                j = 0
                strict = False
                # _ means any  
                while i < len(match) and j < len(word):
                    if match[i] != '_':
                        if strict:
                            if match[i] != word[j]:
                                flag = False
                                break
                        else:
                            strict = True
                            while  j < len(word) and match[i] != word[j]:
                                j += 1
                            if j >= len(word):
                                flag = False
                                break
                    i += 1
                    j += 1
                if i < len(match): continue
                if not flag: continue
            if conditions[2] != None: # string:
                for v in nega:
                    if v in t[0]:
                        flag = False
                        break
                for v in posi:
                    if not v in t[0]:
                        flag = False
                        break
                if not flag: continue
            if conditions[3] != None: # location: 
                mid_x = (t[4][0] + t[1][0] ) / 2
                mid_y = (t[4][1] + t[1][1] ) / 2
                if conditions[3][1:] in coord:
                    next_mark = coord[conditions[3][1:]]
                else:
                    continue
                if abs(mid_x - next_mark[0]) < 0.001 and abs(mid_y - next_mark[1]) < 0.001: 
                    continue  # same 
                if loc == '>':
                    if landscape <= 0:   # portrait
                        if mid_x < next_mark[0] or abs(mid_y - next_mark[1]) > max_y/100:
                            continue
                    else:
                        if mid_y < next_mark[1] or abs(mid_x - next_mark[0]) > max_x/100:
                            continue
            print(t[0])
            used.append(ti)
            coord[r[0][1:]] = ( (t[4][0]+t[1][0])/2, (t[4][1]+t[1][1])/2 )
            found = True
            break
        if found: break   # out of conditions:


