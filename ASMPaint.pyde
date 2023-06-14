
from INIT import *

def setup():
    #size(800,800)
    fullScreen()
    rectMode(CENTER)
    pass

def mousePressed():
    #print("M clicked")
    global mousePressedT
    mousePressedT = 1
    
def mouseReleased():
    global mousePressedT
    mousePressedT = 2 if mousePressedT == 1 else 0

def mousePressedReleased():
    global mousePressedT
    if mousePressedT == 2 and not mousePressed:
        mousePressedT = 0
        return True
    return False

def setUnity(unity):
    global UNITY
    UNITY = int(unity[0])

def setColor(colors):
    global SELECTED_COL
    print(colors)
    SELECTED_COL = color(int(colors[0]),int(colors[1]),int(colors[2]))

def setPNAME(name):
    global P_NAME
    P_NAME = name[0]+".txt"

def sendCommand(txt):
    s_command = txt.split(' ')
    command = s_command[0]
    print(command)
    if command in commands:
        commands[command]()
    if command in utility:
        try:
            #print(utility[s_command[0]](s_command[1],globals()[s_command[2]])[0].name if len(s_command) == 3 else utility[s_command[0]](s_command[1])[0].name)
            utility[command]([arg for arg in s_command[1:]])
        except:
            pass
    pass

QUADRANT = {}

def setSelected(type,data,origin):
    global SELECT
    SELECTED["type"] = type
    SELECTED["data"] = data
    SELECTED["origin"] = origin
    if type != None:
        LAST_SELECTED["type"] = type
        LAST_SELECTED["data"] = data
        LAST_SELECTED["origin"] = origin

def selectAnchor(a):
    setSelected("anchor",a,(a.x,a.y))

class anchor:
    
    s_rad = 25
    rad = 20
    
    s_col = color(255,0,0)
    col = color(255,155,0)
    
    selected = False
    selectable = False
    
    x = 0
    y = 0
    
    ox = 0
    oy = 0
    
    parent = None
    
    def __init__(self, posx = 0, posy = 0, parent = None):
        self.x = posx
        self.y = posy
        self.ox = self.x
        self.oy = self.y
        self.parent = parent
        
        if QUADRANT.has_key((posx // SNATCHRAD , posy // SNATCHRAD )):
            QUADRANT[(posx // SNATCHRAD , posy // SNATCHRAD )].append(self)
        else:
            QUADRANT[(posx // SNATCHRAD , posy // SNATCHRAD )] = []
            QUADRANT[(posx // SNATCHRAD , posy // SNATCHRAD )].append(self)

    def display(self):
        if(self.selected):
            fill(self.s_col)
            ellipse(self.x,
                    self.y,
                    self.s_rad/SCALE,
                    self.s_rad/SCALE)
        else:
            fill(self.col)
            ellipse(self.x,
                    self.y,
                    self.rad/SCALE,
                    self.rad/SCALE)
        self.selected = False
    
    def mouseSnatch(self):
        global SELECTED
        if(dist(self.x,self.y,mouseX/SCALE-GLOBAL_X,mouseY/SCALE-GLOBAL_Y) < self.rad/SCALE and not MOVING):
            cursor(HAND)
            self.selected = True
            if SELECTED["type"] == None and mousePressed:
                selectAnchor(self)
    
    def move_visually(self, x, y):
        if self.parent != None:
            self.parent.update_visually(self)
        self.x = x
        self.y = y
        
    def move(self):
        
        self.x = round(self.x/UNITY) * UNITY
        self.y = round(self.y/UNITY) * UNITY
        
        try:
            QUADRANT[(self.ox // SNATCHRAD  ),(self.oy // SNATCHRAD )].remove(self)
        except:
            print("at delete : ",QUADRANT[(self.ox // SNATCHRAD  ),(self.oy // SNATCHRAD )])
            
        if QUADRANT.has_key((self.x // SNATCHRAD , self.y // SNATCHRAD )):
            QUADRANT[( self.x // SNATCHRAD , self.y // SNATCHRAD )].append(self)
        else:
            QUADRANT[( self.x // SNATCHRAD , self.y // SNATCHRAD )] = []
            QUADRANT[( self.x // SNATCHRAD , self.y // SNATCHRAD )].append(self)
        
        self.ox = self.x
        self.oy = self.y

class rectan:
    
    col = SELECTED_COL
    
    def __init__(self,posx,posy,rad = 100):
        self.x = posx
        self.y = posy
        
        self.p1 = anchor(posx,posy,self)
        self.p2 = anchor(posx+rad,posy,self)
        self.p3 = anchor(posx+rad,posy+rad,self)
        self.p4 = anchor(posx,posy+rad,self)
        
        self.pivots = [self.p1,self.p2,self.p3,self.p4]
    
    def moveShape(self,dx,dy):
        for p in self.pivots:
            p.x += dx
            p.y += dy
            p.move()
    
    def display(self):
        fill(self.col)
        #stroke(SHAPE_BOR_COL)
        noStroke()
        
        beginShape()
        for p in self.pivots:
            vertex(p.x, p.y)
        endShape(CLOSE)
        
        for p in self.pivots:
            p.display()

    def update_visually(self,pivot):
        
        if pivot == self.p1:
            self.p2.y = pivot.y
            self.p4.x = pivot.x
        
        if pivot == self.p2:
            self.p1.y = pivot.y
            self.p3.x = pivot.x
        
        if pivot == self.p3:
            self.p4.y = pivot.y
            self.p2.x = pivot.x
        
        if pivot == self.p4:
            self.p1.x = pivot.x
            self.p3.y = pivot.y
            
    def lesserPivot(self):
        
        ret = self.p1
        
        for p in self.pivots:
            if p.x < ret.x and p.y < ret.y:
                ret = p
        
        return ret
    
    def greaterPivot(self):
        
        ret = self.p3
        
        for p in self.pivots:
            if p.x > ret.x and p.y > ret.y:
                ret = p
        
        return ret
    
    def getSize(self):
        
        lP = self.lesserPivot()
        gP = self.greaterPivot()
        
        return (gP.x-lP.x,gP.y-lP.y)
    
    def update_pivots(self):
        lP = self.lesserPivot()
        gP = self.greaterPivot()
        
        print("Lesser corner",lP.x,lP.y)
        print("Greater corner",gP.x,gP.y)
        
        pass
        
    def update(self):
        for p in self.pivots:
            p.move()
        self.update_pivots()
        pass    

class tria:
    
    col = color(255,255,0)
    
    def __init__(self, posx = 0, posy = 0,rad = 100, col = SELECTED_COL):
        self.x = posx
        self.y = posy
        
        self.col = col
        
        self.p1 = anchor(posx,posy,self)
        self.p2 = anchor(posx+rad,posy+rad,self)
        self.p3 = anchor(posx,posy+rad,self)
        
        self.pivots = [self.p1,self.p2,self.p3]

        self.ttype = 0
        
    def moveShape(self,dx,dy):
        for p in self.pivots:
            p.x += dx
            p.y += dy
            p.move()
    
    def display(self):
        fill(self.col)
        noStroke()
        beginShape()
        for p in self.pivots:
            vertex(p.x,p.y)
        endShape(CLOSE)
        
        for p in self.pivots:
            p.display()
    
    def update_visually(self,pivot):
        
        if pivot == self.p1:
            self.p3.x = pivot.x
        
        if pivot == self.p2:
            self.p3.y = pivot.y
        
        if pivot == self.p3:
            self.p1.x = pivot.x
            self.p2.y = pivot.y
                        
    def lesserPivot(self):
        
        ret = self.p1
        
        for p in self.pivots:
            if p.x < ret.x and p.y <= ret.y:
                ret = p
        
        return ret
    
    def greaterPivot(self):
        
        ret = self.p2
        
        for p in self.pivots:
            if p.x > ret.x and p.y > ret.y:
                ret = p
        
        return ret
    
    def getSize(self):
        
        lP = self.lesserPivot()
        gP = self.greaterPivot()


        if self.p1.y <= self.p3.y:
            if self.p1.x <= self.p2.x:
                self.ttype = 0
            else:
                self.ttype = 1
        else:
            if self.p1.x <= self.p2.x:
                self.ttype = 2
            else:
                self.ttype = 3
        
        return (gP.x-lP.x,gP.y-lP.y)
    
    def update_pivots(self):
        lP = self.lesserPivot()
        gP = self.greaterPivot()
        
        print("Lesser corner",lP.x,lP.y)
        print("Greater corner",gP.x,gP.y)
        
        pass
        
    def update(self):
        self.p1.move()
        self.p2.move()
        self.p3.move()
        self.update_pivots()
        pass

class tool:
    
    def __init__(self, name, behaviour):
        #self.shapee = shapee
        self.name = name
        self.behaviour = behaviour
        self.selected = False
        pass
        
    def display(self, x, y, sizee):
        global mousePressedT
        
        if SELECTED["data"] == self:
            fill(TOOL_BG_SEL)
        else:
            fill(TOOL_BG)
            
        rect(x,y,sizee,sizee,30)
        #shape(self.shapee)
        
        if( mousePressedReleased() and dist(mouseX,mouseY,x,y) < sizee and SELECTED["data"] != self):
    
            mousePressedT = 0
            setSelected("tool", self, (0,0))
            self.selected = True
            return
        
        if( mousePressedReleased() and dist(mouseX,mouseY,x,y) < sizee/2 and SELECTED["data"] == self):
            
            mousePressedT = 0
            setSelect( None, None, (0,0))
            self.selected = True
            return     

shapes = [rectan(random(600),random(600)) for x in range(0)]

def updateSpeed():
    global SPEED_X, SPEED_Y, AXIS_X, AXIS_Y, keys
    
    AXIS_X = (keys[39] - keys[37])
    AXIS_Y = (keys[40] - keys[38])
        
    SPEED_X += AXIS_X * 0.5
    SPEED_Y += AXIS_Y * 0.5

def grid():
    #strokeWeight(5)
    
    stroke(GRID_COL)
    
    for x in range(int(width/SCALE)//UNITY):
        line(x*UNITY-GLOBAL_X+GLOBAL_X%UNITY,
             0-GLOBAL_Y,
             x*UNITY-GLOBAL_X+GLOBAL_X%UNITY,
             height/SCALE-GLOBAL_Y)
        
    for y in range(int(height/SCALE)//UNITY):
        line(0-GLOBAL_X,
             y*UNITY-GLOBAL_Y+GLOBAL_Y%UNITY,
             width/SCALE-GLOBAL_X,
             y*UNITY-GLOBAL_Y+GLOBAL_Y%UNITY)
            
    stroke(ORIGIN_COL)
    
    line(0-GLOBAL_X,0,width/SCALE-GLOBAL_X,0)
    line(0,0-GLOBAL_Y,0,height/SCALE-GLOBAL_Y)
    
    stroke(SCREEN_COL)
    strokeWeight(1)
    line(0-GLOBAL_X,SCREEN_HEIGHT,width/SCALE-GLOBAL_X,SCREEN_HEIGHT)
    line(SCREEN_WIDTH,0-GLOBAL_Y,SCREEN_WIDTH,height/SCALE-GLOBAL_Y)

    
    stroke(ORIGIN_COL)
    strokeWeight(1)

def rectBehaviour(x,y):
    print("Rect",x,y)
    global SELECTED
    n_rect = rectan(x, y, 0)
    n_rect.col = SELECTED_COL
    shapes.append(n_rect)
    setSelected( "anchor", n_rect.p3, (n_rect.p1.ox,n_rect.p1.oy))

def triaBehaviour(x,y):
    print("tria",x,y)
    global SELECTED
    n_tria = tria(x, y)
    n_tria.col = SELECTED_COL
    shapes.append(n_tria)
    setSelected( "anchor", n_tria.p2, (n_tria.p2.ox,n_tria.p2.oy))

rectTool = tool("rect",rectBehaviour)
triaTool = tool("tria",triaBehaviour)

tools = [rectTool,triaTool]

def toolBox():
    
    for i,tool in enumerate(tools):
        #fill(220,244,245)
        #rect(width - (75 * i) - 75, height-75,50,50,10)
        tool.display(width - (75 * i) - 75, height-75, 50)
    pass
    
def saveShapes():

    txt = [""]

    for s in shapes:
        if isinstance(s,rectan):
            lP = s.lesserPivot()
            posx = int(lP.x)
            posy = int(lP.y)
            
            size = s.getSize()
            if 0 <= posx < 2000:
                txt.append("\tadd x1, x1, "+str(posx))
            else:
                txt.append("\tsub x1, x1, "+str(-posx))
            if 0 <= posy < 2000:
                txt.append("\tadd x2, x2, "+str(posy))
            else:
                txt.append("\tsub x2, x2, "+str(-posy))
            txt.append("\tmovz x3, "+str(abs(int(size[0]))))
            txt.append("\tmovz x4, "+str(abs(int(size[1]))))
            txt.append("\tmovz x5, 0x"+hex(s.col>> 16 & 0xFF)[6:]+", lsl 16")
            txt.append("\tmovk x5, 0x"+hex(s.col>>  8 & 0xFF)[6:]+hex(s.col>> 0 & 0xFF)[6:]+", lsl 00")
            txt.append("")
            txt.append("\tbl rect")
            txt.append("")
            txt.append("")
            
        if isinstance(s,tria):
            lP = s.lesserPivot()
            posx = int(lP.x)
            posy = int(lP.y)
            
            print("Possesions",posx,posy)
            
            size = s.getSize()
            if 0 <= posx < INM_LIMIT:
                txt.append("\tadd x1, x1, "+str(posx))
            else:
                txt.append("\tsub x1, x1, "+str(-posx))
            if 0 <= posy < INM_LIMIT:
                txt.append("\tadd x2, x2, "+str(posy))
            else:
                txt.append("\tadd x2, x2, "+str(-posy))
            txt.append("\tmovz x3, "+str(abs(int(size[0]))))
            txt.append("\tmovz x4, "+str(abs(int(size[1]))))
            txt.append("\tmovz x5, 0x"+hex(s.col>> 16 & 0xFF)[6:]+", lsl 16")
            txt.append("\tmovk x5, 0x"+hex(s.col>> 8 & 0xFF)[6:]+hex(s.col>> 0 & 0xFF)[6:]+", lsl 00")
            txt.append("")
            txt.append("\tbl trian"+str(s.ttype))
            txt.append("")
            txt.append("")
                
    saveStrings(P_NAME,txt)

def showTextBox():
    if len(TEXT_CACHE) > 0:
        textAlign(LEFT)
        fill(0)
        textSize(TEXT_SIZE)
        text(TEXT_CACHE,45,height-100)

def pickMouse():
    global SELECTED_COL
    loadPixels()
    SELECTED_COL = pixels[mouseX+(mouseY*width)]

def selectAll():
    setSelected("group", shapes, (0,0))

commands = {
    "!save": saveShapes,
    "!pickMouse": pickMouse,
    "!selectAll": selectAll
}

utility = {
    "!setColor": setColor,
    "!setUnity": setUnity,
    "!setPName": setPNAME
}


def draw():
    
    global SELECTED, SCALE, MOVING, GLOBAL_X, GLOBAL_Y, ORIGIN_X,ORIGIN_Y, SPEED_X, SPEED_Y, AXIS_X, AXIS_Y
    
    if SELECTED["type"] == None or not keys[' ']:
        cursor(ARROW)
        pass
    
    background("#FAFAFA")
    
    pushMatrix()
    
    scale(SCALE)
    translate(GLOBAL_X,GLOBAL_Y)
    
    grid()
    
    #GLOBAL_X = cos(frameCount/100.0)*400
    #GLOBAL_Y = sin(frameCount/100.0)*400
    
    #SCALE = 1+cos(frameCount/100.0)*0.5
    
    SPEED_X *= 0.94
    GLOBAL_X -= SPEED_X
    
    SPEED_Y *= 0.94
    GLOBAL_Y -= SPEED_Y
    
    for rectan in shapes:
        rectan.display()
        
    deltex = mouseX/SCALE-GLOBAL_X
    deltey = mouseY/SCALE-GLOBAL_Y
    
    if QUADRANT.has_key((deltex // SNATCHRAD,deltey // SNATCHRAD)):
        #print(QUADRANT[(mouseX // SNATCHRAD),(mouseY // SNATCHRAD)])
        for punto in QUADRANT[(deltex // SNATCHRAD),(deltey // SNATCHRAD)]:
            #punto.selected = True
            punto.mouseSnatch()
    
    if mousePressed:
        if SELECTED["type"] == "anchor":
            SELECTED["data"].move_visually(deltex, deltey)
        
        if SELECTED["type"] == "tool":
            SELECTED["data"].behaviour(deltex,deltey)
                
    else:
        if SELECTED["type"] == "anchor":
            if SELECTED["data"].parent != None:
                SELECTED["data"].parent.update_visually(SELECTED["data"])
                SELECTED["data"].parent.update()
            SELECTED["data"].move()
            setSelected( None, None, (0,0))
    
    if keyPressed:
        #print(key,keyCode)
        
        if key == CODED:
            updateSpeed()
            if keyCode == ESC:
                exit()
                
        if key == ' ':
            
            if mousePressed and SELECTED["type"] == None:
                cursor(HAND)
                MOVING = True
                GLOBAL_X = ORIGIN_X+mouseX/SCALE
                GLOBAL_Y = ORIGIN_Y+mouseY/SCALE
            else:
                MOVING = False
                ORIGIN_X = GLOBAL_X-mouseX/SCALE
                ORIGIN_Y = GLOBAL_Y-mouseY/SCALE

    popMatrix()
    
    toolBox()
    showTextBox()
    fill(SELECTED_COL)
    rect(60,60,100,100,50)

def keyPressed():
    
    global TEXT_CACHE
    
    if key == CODED:
        keys[keyCode] = True
    else:
        keys[key] = True
    
    if len(TEXT_CACHE) <= 0:
        if key == 'w':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(0,-UNITY)
            if LAST_SELECTED["type"] == "anchor":
                if LAST_SELECTED["data"].parent != None:
                    LAST_SELECTED["data"].parent.moveShape(0,-UNITY)

        if key == 's':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(0, UNITY)
            if LAST_SELECTED["type"] == "anchor":
                if LAST_SELECTED["data"].parent != None:
                    LAST_SELECTED["data"].parent.moveShape(0,UNITY)

        if key == 'a':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(-UNITY,0)
            if LAST_SELECTED["type"] == "anchor":
                if LAST_SELECTED["data"].parent != None:
                    LAST_SELECTED["data"].parent.moveShape(-UNITY,0)

        if key == 'd':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape( UNITY,0)
            if LAST_SELECTED["type"] == "anchor":
                if LAST_SELECTED["data"].parent != None:
                    LAST_SELECTED["data"].parent.moveShape(UNITY,0)
        
        if key == 'c':
            setSelected('tool', rectTool, (0,0))
        
        if key == 't':
            setSelected('tool', triaTool, (0,0))
        
        if key == 'u':
            LAST_SELECTED["type"] = None
        
        if key == '\x7f':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    shapes.remove(s)
                LAST_SELECTED["type"] = None
            if LAST_SELECTED["type"] == "anchor":
                if LAST_SELECTED["data"].parent != None:
                    if LAST_SELECTED["data"].parent in shapes:
                        shapes.remove(LAST_SELECTED["data"].parent)
                        LAST_SELECTED["type"] == None
    
        if key == 'o':
            saveShapes()
        
    if key in [ENTER,DELETE,BACKSPACE]:
        if key == BACKSPACE:
            TEXT_CACHE = TEXT_CACHE[:-1]
        if key == ENTER:
            sendCommand(TEXT_CACHE)
            TEXT_CACHE = ""

def keyTyped():
    global TEXT_CACHE
    if len(TEXT_CACHE) <= 0:
        if key != '!':
            return
    if key not in [ENTER,DELETE,BACKSPACE]:
        TEXT_CACHE += key
    pass

def keyReleased():
    if key == CODED:
        keys[keyCode] = False
    else:
        keys[key] = False

def mouseWheel(event):
    global SCALE, GLOBAL_X, GLOBAL_Y
    e = event.getCount()/10.0
    SCALE -= e
