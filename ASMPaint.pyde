import random
from datetime import datetime

# -------------------- COLOR RGB TUPLES (moved to setup) --------------------

_GRID_RGB       = (216, 239, 255)
_ORIGIN_RGB     = (126, 191, 240)
_SHAPE_BOR_RGB  = (39,  39,  39)
_TOOL_BG_SEL_RGB= (180, 200, 200)
_TOOL_BG_RGB    = (166, 200, 166)
_SCREEN_RGB     = (255, 180,  43)
_SELECTED_RGB   = (200, 155, 155)

# These will be overwritten by color(...) in setup()
GRID_COL       = None
ORIGIN_COL     = None
SHAPE_BOR_COL  = None
TOOL_BG_SEL    = None
TOOL_BG        = None
SCREEN_COL     = None
SELECTED_COL   = None

SCREEN_WIDTH   = 640
SCREEN_HEIGHT  = 480

UNITY          = 100

# -------------------- SELECTION TRACKING --------------------

SELECTED = {
    "type": None,    # "tool", "anchor", or "group"
    "data": None,    # The actual object (Tool instance, Anchor, or list of shapes)
    "origin": (0, 0)
}

LAST_SELECTED = {
    "type": None,
    "data": None,
    "origin": (0, 0)
}

SNATCHRAD      = 100  # Spatial-hash cell size for anchors

# -------------------- CANVAS PAN / ZOOM STATE --------------------

GLOBAL_X = 0
GLOBAL_Y = 0
ORIGIN_X = 0
ORIGIN_Y = 0
SCALE    = 1.0

MOVING   = False
SPEED_X  = 0
SPEED_Y  = 0
AXIS_X   = 0
AXIS_Y   = 0

QUADRANT = {}  # maps (cell_x, cell_y) → list of Anchor instances

# -------------------- KEY STATE --------------------

keys = {
    37: False,  # LEFT ARROW
    38: False,  # UP ARROW
    39: False,  # RIGHT ARROW
    40: False,  # DOWN ARROW
    ' ': False  # SPACEBAR
}

TEXT_CACHE    = ""
TEXT_SIZE     = 30

INM_LIMIT     = 3000

mousePressedT = False

# Collection of all shapes (RectangleShape, TriangleShape, EllipseShape)
shapes = []

# Default P_NAME uses current datetime “dd-mm-YYYY-HH-MM.txt”
P_NAME = datetime.now().strftime("%d-%m-%Y-%H-%M") + ".txt"


# -------------------- SELECTION HELPERS --------------------

def setSelected(sel_type, data, origin):
    """
    Update the SELECTED dictionary and, if sel_type is not None,
    also record in LAST_SELECTED.
    """
    SELECTED["type"] = sel_type
    SELECTED["data"] = data
    SELECTED["origin"] = origin
    if sel_type is not None:
        LAST_SELECTED["type"] = sel_type
        LAST_SELECTED["data"] = data
        LAST_SELECTED["origin"] = origin

def selectAnchor(a):
    """Shortcut to select a single Anchor."""
    setSelected("anchor", a, (a.x, a.y))

def selectAll():
    """Select all shapes as a group."""
    setSelected("group", shapes, (0, 0))


# -------------------- ANCHOR CLASS --------------------

class Anchor:
    """
    Draggable pivot point. On release, snaps to nearest UNITY grid and updates its parent shape.
    """
    s_rad      = 25  # radius when hovered/selected
    rad        = 20  # normal radius

    def __init__(self, posx=0, posy=0, parent=None):
        self.x = posx
        self.y = posy
        self.ox = posx
        self.oy = posy
        self.parent = parent
        self.selected = False  # for drawing highlight
        cell = (int(self.x) // SNATCHRAD, int(self.y) // SNATCHRAD)
        if cell in QUADRANT:
            QUADRANT[cell].append(self)
        else:
            QUADRANT[cell] = [self]

    def display(self):
        """Draw the pivot circle (larger if selected)."""
        if self.selected:
            fill(255, 0, 0)
            ellipse(self.x, self.y, self.s_rad / SCALE, self.s_rad / SCALE)
        else:
            fill(255, 155, 0)
            ellipse(self.x, self.y, self.rad / SCALE, self.rad / SCALE)
        self.selected = False

    def mouseSnatch(self):
        """
        If the mouse is within rad/SCALE of this anchor, highlight it
        and—if no other selection—select it on click.
        """
        mx = mouseX / SCALE - GLOBAL_X
        my = mouseY / SCALE - GLOBAL_Y
        if dist(self.x, self.y, mx, my) < (self.rad / SCALE) and not MOVING:
            cursor(HAND)
            self.selected = True
            if SELECTED["type"] is None and mousePressed:
                selectAnchor(self)

    def move_visually(self, new_x, new_y):
        """
        While dragging, update this anchor’s position (continuous),
        notify parent shape to adjust shape visually.
        """
        if self.parent is not None:
            self.parent.update_visually(self)
        self.x = new_x
        self.y = new_y

    def move(self):
        """
        On mouse release: snap to UNITY grid, re-hash into QUADRANT,
        and finalize parent shape’s pivots.
        """
        # Snap to nearest UNITY increment
        self.x = round(self.x / UNITY) * UNITY
        self.y = round(self.y / UNITY) * UNITY

        old_cell = (self.ox // SNATCHRAD, self.oy // SNATCHRAD)
        new_cell = (self.x // SNATCHRAD, self.y // SNATCHRAD)

        # Remove from old cell
        try:
            QUADRANT[old_cell].remove(self)
        except:
            pass

        # Add to new cell
        if new_cell in QUADRANT:
            QUADRANT[new_cell].append(self)
        else:
            QUADRANT[new_cell] = [self]

        self.ox = self.x
        self.oy = self.y


# -------------------- SHAPE CLASSES --------------------

class RectangleShape:
    """
    Axis-aligned rectangle defined by four Anchors: p1(top-left), p2(top-right),
    p3(bottom-right), p4(bottom-left). Dragging any corner keeps it axis-aligned.
    """
    def __init__(self, posx, posy, size=100, col=None):
        self.col = col
        self.p1 = Anchor(posx, posy, self)
        self.p2 = Anchor(posx + size, posy, self)
        self.p3 = Anchor(posx + size, posy + size, self)
        self.p4 = Anchor(posx, posy + size, self)
        self.pivots = [self.p1, self.p2, self.p3, self.p4]

    def moveShape(self, dx, dy):
        """Translate all pivots and re-hash them."""
        for p in self.pivots:
            p.x += dx
            p.y += dy
            p.move()

    def display(self):
        """Draw a filled rectangle (via beginShape/endShape) and its pivots."""
        fill(self.col)
        noStroke()
        beginShape()
        for p in self.pivots:
            vertex(p.x, p.y)
        endShape(CLOSE)
        for p in self.pivots:
            p.display()

    def update_visually(self, pivot):
        """
        While dragging pivot:
        - If pivot == p1, keep p2.y = p1.y and p4.x = p1.x
        - If pivot == p2, keep p1.y = p2.y and p3.x = p2.x
        - If pivot == p3, keep p2.x = p3.x and p4.y = p3.y
        - If pivot == p4, keep p1.x = p4.x and p3.y = p4.y
        """
        if pivot == self.p1:
            self.p2.y = pivot.y
            self.p4.x = pivot.x
        elif pivot == self.p2:
            self.p1.y = pivot.y
            self.p3.x = pivot.x
        elif pivot == self.p3:
            self.p4.y = pivot.y
            self.p2.x = pivot.x
        elif pivot == self.p4:
            self.p1.x = pivot.x
            self.p3.y = pivot.y

    def lesserPivot(self):
        """Return the top-left pivot (smallest x and y)."""
        ret = self.p1
        for p in self.pivots:
            if p.x < ret.x and p.y < ret.y:
                ret = p
        return ret

    def greaterPivot(self):
        """Return the bottom-right pivot (largest x and y)."""
        ret = self.p3
        for p in self.pivots:
            if p.x > ret.x and p.y > ret.y:
                ret = p
        return ret

    def getSize(self):
        """Compute (width, height) from lesser vs. greater pivots."""
        lP = self.lesserPivot()
        gP = self.greaterPivot()
        return (gP.x - lP.x, gP.y - lP.y)

    def update_pivots(self):
        """(Optional) Debug print of corners."""
        # lP = self.lesserPivot()
        # gP = self.greaterPivot()
        # print("Rect corners:", (lP.x, lP.y), (gP.x, gP.y))
        pass

    def update(self):
        """Snap each pivot to the grid and then recalc corners."""
        for p in self.pivots:
            p.move()
        self.update_pivots()


class TriangleShape:
    """
    Right-angled triangle with three pivots: p1, p2, p3. Always axis-aligned:
    - p1 = one corner, p2 = opposite corner of right angle, p3 = third vertex.
    Dragging a pivot keeps the right-angle behavior.
    """
    def __init__(self, posx=0, posy=0, size=100, col=None):
        self.col = col
        self.p1 = Anchor(posx, posy, self)
        self.p2 = Anchor(posx + size, posy + size, self)
        self.p3 = Anchor(posx, posy + size, self)
        self.pivots = [self.p1, self.p2, self.p3]
        self.ttype = 0  # orientation type (0..3)

    def moveShape(self, dx, dy):
        """Translate all pivots and re-hash."""
        for p in self.pivots:
            p.x += dx
            p.y += dy
            p.move()

    def display(self):
        """Draw filled triangle and its pivots."""
        fill(self.col)
        noStroke()
        beginShape()
        for p in self.pivots:
            vertex(p.x, p.y)
        endShape(CLOSE)
        for p in self.pivots:
            p.display()

    def update_visually(self, pivot):
        """
        While dragging:
        - If pivot == p1, set p3.x = p1.x.
        - If pivot == p2, set p3.y = p2.y.
        - If pivot == p3, set p1.x = p3.x and p2.y = p3.y.
        """
        if pivot == self.p1:
            self.p3.x = pivot.x
        elif pivot == self.p2:
            self.p3.y = pivot.y
        elif pivot == self.p3:
            self.p1.x = pivot.x
            self.p2.y = pivot.y

    def lesserPivot(self):
        """Return the pivot with smallest x and y."""
        ret = self.p1
        for p in self.pivots:
            if p.x <= ret.x and p.y <= ret.y:
                ret = p
        return ret

    def greaterPivot(self):
        """Return the pivot with largest x and y."""
        ret = self.p2
        for p in self.pivots:
            if p.x >= ret.x and p.y >= ret.y:
                ret = p
        return ret

    def getSize(self):
        """
        Compute (width, height) from bounding box, and set ttype for orientation.
        ttype:
          0 = p1 above p3 and p1 left of p2,
          1 = p1 above p3 but p1 right of p2, etc.
        """
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
        return (gP.x - lP.x, gP.y - lP.y)

    def update_pivots(self):
        """(Optional) Debug print."""
        # lP = self.lesserPivot()
        # gP = self.greaterPivot()
        # print("Triangle corners:", (lP.x, lP.y), (gP.x, gP.y))
        pass

    def update(self):
        """Snap each pivot and recalc corners."""
        self.p1.move()
        self.p2.move()
        self.p3.move()
        self.update_pivots()


class EllipseShape:
    """
    Ellipse inscribed in a bounding rectangle whose corners are p1..p4 anchors:
    p1 = top-left, p2 = top-right, p3 = bottom-right, p4 = bottom-left.
    Dragging any pivot keeps the opposite edges aligned as a rectangle.
    """
    def __init__(self, posx, posy, size=100, col=None):
        self.col = col
        self.p1  = Anchor(posx, posy, self)
        self.p2  = Anchor(posx + size, posy, self)
        self.p3  = Anchor(posx + size, posy + size, self)
        self.p4  = Anchor(posx, posy + size, self)
        self.pivots = [self.p1, self.p2, self.p3, self.p4]

    def moveShape(self, dx, dy):
        """Translate all pivots and re-hash."""
        for p in self.pivots:
            p.x += dx
            p.y += dy
            p.move()

    def display(self):
        """
        Draw ellipse inside the rectangle defined by pivots, then pivots themselves.
        """
        fill(self.col)
        noStroke()
        lP = self.lesserPivot()
        w, h = self.getSize()
        cx = lP.x + w / 2.0
        cy = lP.y + h / 2.0
        ellipse(cx, cy, w, h)
        for p in self.pivots:
            p.display()

    def update_visually(self, pivot):
        """
        While dragging:
        - If pivot == p1, keep p2.y = p1.y and p4.x = p1.x
        - If pivot == p2, keep p1.y = p2.y and p3.x = p2.x
        - If pivot == p3, keep p4.y = p3.y and p2.x = p3.x
        - If pivot == p4, keep p1.x = p4.x and p3.y = p4.y
        """
        if pivot == self.p1:
            self.p2.y = pivot.y
            self.p4.x = pivot.x
        elif pivot == self.p2:
            self.p1.y = pivot.y
            self.p3.x = pivot.x
        elif pivot == self.p3:
            self.p4.y = pivot.y
            self.p2.x = pivot.x
        elif pivot == self.p4:
            self.p1.x = pivot.x
            self.p3.y = pivot.y

    def lesserPivot(self):
        """Return top-left pivot."""
        ret = self.p1
        for p in self.pivots:
            if p.x < ret.x and p.y < ret.y:
                ret = p
        return ret

    def greaterPivot(self):
        """Return bottom-right pivot."""
        ret = self.p3
        for p in self.pivots:
            if p.x > ret.x and p.y > ret.y:
                ret = p
        return ret

    def getSize(self):
        """Return (width, height) of bounding box."""
        lP = self.lesserPivot()
        gP = self.greaterPivot()
        return (gP.x - lP.x, gP.y - lP.y)

    def update_pivots(self):
        """(Optional) Debug print."""
        # lP = self.lesserPivot()
        # gP = self.greaterPivot()
        # print("Ellipse corners:", (lP.x, lP.y), (gP.x, gP.y))
        pass

    def update(self):
        """Snap each pivot and recalc bounding box."""
        for p in self.pivots:
            p.move()
        self.update_pivots()


# -------------------- TOOL & BEHAVIOR CLASSES --------------------

class Tool:
    """
    A clickable icon (rounded rectangle). Selecting it sets its “behaviour”
    so that the next click in the canvas creates the corresponding shape.
    """
    def __init__(self, name, behaviour):
        self.name = name
        self.behaviour = behaviour  # function(x, y)
        self.selected = False

    def display(self, x, y, sizee):
        """
        Draw the tool icon at (x,y) with width=height=sizee.
        If clicked (mouseReleased inside), toggle selection.
        """
        global mousePressedT
        if SELECTED["data"] == self:
            fill(TOOL_BG_SEL)
        else:
            fill(TOOL_BG)

        noStroke()
        rect(x, y, sizee, sizee, 30)

        if mousePressedReleased() and dist(mouseX, mouseY, x, y) < sizee:
            # If not currently selected, select this tool; else deselect
            if SELECTED["data"] != self:
                mousePressedT = False
                setSelected("tool", self, (0, 0))
                self.selected = True
            else:
                mousePressedT = False
                setSelected(None, None, (0, 0))
                self.selected = False


def rectBehaviour(x, y):
    """
    When rectangle tool is active and user clicks a point,
    create a new RectangleShape (size=0), set its p3 pivot as selected
    so user can drag out the rectangle.
    """
    global SELECTED
    n_rect = RectangleShape(x, y, size=0, col=SELECTED_COL)
    shapes.append(n_rect)
    setSelected("anchor", n_rect.p3, (n_rect.p1.x, n_rect.p1.y))


def triaBehaviour(x, y):
    """
    When triangle tool is active: new TriangleShape at (x,y) with size=0,
    immediately select its p2 pivot so user can drag out the triangle.
    """
    global SELECTED
    n_tria = TriangleShape(x, y, size=0, col=SELECTED_COL)
    shapes.append(n_tria)
    setSelected("anchor", n_tria.p2, (n_tria.p2.x, n_tria.p2.y))


def ellipseBehaviour(x, y):
    """
    When ellipse tool is active: new EllipseShape at (x,y) with size=0,
    immediately select its p3 pivot for dragging out.
    """
    global SELECTED
    n_el = EllipseShape(x, y, size=0, col=SELECTED_COL)
    shapes.append(n_el)
    setSelected("anchor", n_el.p3, (n_el.p1.x, n_el.p1.y))


# Instantiate tool icons
rectTool    = Tool("rect", rectBehaviour)
triaTool    = Tool("tria", triaBehaviour)
ellipseTool = Tool("ellipse", ellipseBehaviour)
tools = [rectTool, triaTool, ellipseTool]


def toolBox():
    """Draw all tool icons at bottom-right corner."""
    for i, t in enumerate(tools):
        t.display(width - (75 * i) - 75, height - 75, 50)


# -------------------- EXPORT HELPERS (ASSEMBLY) --------------------

def build_color_asm(r, g, b, a=255):
    """
    Produce lines:
      movz x1, 0xRR   ; A in hex
      movz x2, 0xGG   ; R in hex
      movz x3, 0xBB   ; G in hex
      movz x4, 0xAA   ; B in hex
      bl   build_color
    Resulting packed color in x4.
    """
    lines = []
    lines.append("\tmovz x1, 0x{:02X}".format(a))
    lines.append("\tmovz x2, 0x{:02X}".format(r))
    lines.append("\tmovz x3, 0x{:02X}".format(g))
    lines.append("\tmovz x4, 0x{:02X}".format(b))
    lines.append("\tbl build_color")
    return lines


def saveShapes():
    """
    Iterate over each shape in `shapes`:
      1) Extract (posx, posy) from lesserPivot.
      2) Extract (width, height) from getSize().
      3) Extract RGBA from s.col.
      4) Emit build_color_asm(r,g,b,a) → x0 contains packed color.
      5) movz x1, posx; movz x2, posy; movz x3, width; movz x4, height
      6) mov x5, x0
      7) bl <routine>   (rect / trian0..3 / ellipse)
    Finally, write all lines to `P_NAME` (timestamped).
    """
    global P_NAME, SELECTED_COL
    P_NAME = datetime.now().strftime("%d-%m-%Y-%H-%M") + ".txt"
    txt = []

    for idx, s in enumerate(shapes):
        if isinstance(s, RectangleShape):
                        # 1) Gather all three pivot coordinates
            xs = [p.x for p in s.pivots]
            ys = [p.y for p in s.pivots]

            # 2) Compute bounding‐box by min/max
            lpx = min(xs)
            lpy = min(ys)
            gpx = max(xs)
            gpy = max(ys)

            posx = int(lpx)
            posy = int(lpy)
            w = abs(int(gpx - lpx))
            h = abs(int(gpy - lpy))
            
            rr = (s.col >> 16) & 0xFF
            gg = (s.col >> 8)  & 0xFF
            bb = (s.col     ) & 0xFF
            aa = 255
            txt.extend(build_color_asm(rr, gg, bb, aa))
            txt.append("\tmovz x5, " + str(posx))
            txt.append("\tmovz x8, " + str(posy))
            txt.append("\tmovz x6, " + str(w))
            txt.append("\tmovz x9, " + str(h))
            txt.append("\tbl rectangle")
            txt.append("")

        elif isinstance(s, TriangleShape):
            _ = s.getSize() 
            
            # 1) Gather all three pivot coordinates
            xs = [p.x for p in s.pivots]
            ys = [p.y for p in s.pivots]

            # 2) Compute bounding‐box by min/max
            lpx = min(xs)
            lpy = min(ys)
            gpx = max(xs)
            gpy = max(ys)

            posx = int(lpx)
            posy = int(lpy)
            w = abs(int(gpx - lpx))
            h = abs(int(gpy - lpy))

            ttype = s.ttype  # 0..3 (orientation)

            # 3) Extract RGBA from s.col
            rr = (s.col >> 16) & 0xFF
            gg = (s.col >> 8)  & 0xFF
            bb = (s.col      ) & 0xFF
            aa = 255

            # 4) Build color → X0
            txt.extend(build_color_asm(rr, gg, bb, aa))

             # 7) Load the right‐angle pivot (px,py) + leg lengths (w,h)
            txt.append("\tmovz x5, " + str(posx))   # X1 = p3.x
            txt.append("\tmovz x8, " + str(posy))   # X2 = p3.y
            txt.append("\tmovz x6, " + str(w))    # X3 = horizontal leg length
            txt.append("\tmovz x9, " + str(h))    # X5 = vertical leg length

            # 6) Call the correct triangle routine
            txt.append("\tbl triangle_" + str(ttype))
            txt.append("")
            
        elif isinstance(s, EllipseShape):
            # 1) Get top‐left corner and full width/height
                        # 1) Gather all three pivot coordinates
            xs = [p.x for p in s.pivots]
            ys = [p.y for p in s.pivots]

            # 2) Compute bounding‐box by min/max
            lpx = min(xs)
            lpy = min(ys)
            gpx = max(xs)
            gpy = max(ys)

            posx = int(lpx)
            posy = int(lpy)
            w, h = s.getSize()
            w = abs(int(w))
            h = abs(int(h))

            # 2) Extract RGBA bytes from s.col
            rr = (s.col >> 16) & 0xFF
            gg = (s.col >> 8)  & 0xFF
            bb = (s.col      ) & 0xFF
            aa = 255
    
            # 3) Build the 32‐bit ARGB color → ends up in X4
            txt.extend(build_color_asm(rr, gg, bb, aa))

            # 5) Compute center and radii (integer division)
            cx = posx + w // 2   # center X
            cy = posy + h // 2   # center Y
            rx = w // 2          # horizontal radius
            ry = h // 2          # vertical radius

            # 6) Load them into X5, X6, X8, X9
            txt.append("\tmovz x5, " + str(cx))  # cx → X5
            txt.append("\tmovz x6, " + str(rx))  # rx → X6
            txt.append("\tmovz x8, " + str(cy))  # cy → X8
            txt.append("\tmovz x9, " + str(ry))  # ry → X9

            # 7) Call ellipse
            txt.append("\tbl ellipse")
            txt.append("")
        
    saveStrings(P_NAME, txt)


# -------------------- COMMAND & UTILITY REGISTRATION --------------------

commands = {
    "!save": saveShapes,
    "!selectAll": selectAll,
    "!pickMouse": lambda: pickMouse()
}

utility = {
    "!setColor": lambda args: setColor(args),
    "!setUnity": lambda args: setUnity(args),
    "!setPName": lambda args: setPNAME(args)
}

def sendCommand(txt):
    """
    On ENTER in the text box, split by spaces:
    If the first token matches a key in `commands`, call it.
    Otherwise if it matches a key in `utility`, call that with args.
    """
    s_command = txt.split(' ')
    cmd = s_command[0]
    if cmd in commands:
        commands[cmd]()
    elif cmd in utility:
        try:
            utility[cmd](s_command[1:])
        except:
            pass


# -------------------- MOUSE & KEY HELPERS --------------------

def mousePressed():
    global mousePressedT
    mousePressedT = 1

def mouseReleased():
    global mousePressedT
    mousePressedT = 2 if mousePressedT == 1 else 0

def mousePressedReleased():
    """
    Return True exactly once when the mouse is released after being pressed.
    Then reset state.
    """
    global mousePressedT
    if mousePressedT == 2 and not mousePressed:
        mousePressedT = 0
        return True
    return False

def mouseWheel(event):
    """
    Zoom in/out with scroll wheel → adjust SCALE (clamp at 0.1).
    """
    global SCALE
    delta = event.getCount() / 10.0
    SCALE -= delta
    if SCALE < 0.1:
        SCALE = 0.1

def keyPressed():
    """
    Handle:
      - Arrow keys & WASD for nudging shapes
      - c/t/e for selecting rectangle/triangle/ellipse tools
      - u to deselect
      - DEL to delete
      - o to save quickly
      - Text input (commands) with ENTER/BACKSPACE
    """
    global TEXT_CACHE, MOVING, GLOBAL_X, GLOBAL_Y, ORIGIN_X, ORIGIN_Y, SPEED_X, SPEED_Y

    if key == CODED:
        keys[keyCode] = True
        if keyCode == ESC:
            exit()
    else:
        keys[key] = True

    # If no text command in progress, handle shortcuts
    if len(TEXT_CACHE) <= 0:
        if key == 'w':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(0, -UNITY)
            elif LAST_SELECTED["type"] == "anchor":
                p = LAST_SELECTED["data"]
                if p.parent is not None:
                    p.parent.moveShape(0, -UNITY)

        elif key == 's':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(0, UNITY)
            elif LAST_SELECTED["type"] == "anchor":
                p = LAST_SELECTED["data"]
                if p.parent is not None:
                    p.parent.moveShape(0, UNITY)

        elif key == 'a':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(-UNITY, 0)
            elif LAST_SELECTED["type"] == "anchor":
                p = LAST_SELECTED["data"]
                if p.parent is not None:
                    p.parent.moveShape(-UNITY, 0)

        elif key == 'd':
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    s.moveShape(UNITY, 0)
            elif LAST_SELECTED["type"] == "anchor":
                p = LAST_SELECTED["data"]
                if p.parent is not None:
                    p.parent.moveShape(UNITY, 0)

        # Tool shortcuts
        if key == 'c':
            setSelected('tool', rectTool, (0, 0))
        elif key == 't':
            setSelected('tool', triaTool, (0, 0))
        elif key == 'e':
            setSelected('tool', ellipseTool, (0, 0))
        elif key == 'u':
            LAST_SELECTED["type"] = None
        elif key == '\x7f':  # DELETE
            if LAST_SELECTED["type"] == "group":
                for s in LAST_SELECTED["data"]:
                    shapes.remove(s)
                LAST_SELECTED["type"] = None
            elif LAST_SELECTED["type"] == "anchor":
                p = LAST_SELECTED["data"]
                if p.parent is not None and p.parent in shapes:
                    shapes.remove(p.parent)
                    LAST_SELECTED["type"] = None
        elif key == 'o':  # Quick save
            saveShapes()

    # Text command handling
    if key in [ENTER, DELETE, BACKSPACE]:
        if key == BACKSPACE:
            TEXT_CACHE = TEXT_CACHE[:-1]
        elif key == ENTER:
            sendCommand(TEXT_CACHE)
            TEXT_CACHE = ""

def keyReleased():
    """Update key state dictionary."""
    if key == CODED:
        keys[keyCode] = False
    else:
        keys[key] = False

def keyTyped():
    """
    Accumulate characters into TEXT_CACHE if the first character was '!'
    or we are already typing a command.
    """
    global TEXT_CACHE
    if len(TEXT_CACHE) <= 0 and key != '!':
        return
    if key not in [ENTER, DELETE, BACKSPACE]:
        TEXT_CACHE += key


# -------------------- GRID & CAMERA CONTROL --------------------

def updateSpeed():
    """
    If arrow keys are held, accelerate camera pan.
    """
    global SPEED_X, SPEED_Y, AXIS_X, AXIS_Y
    AXIS_X = (1 if keys.get(39, False) else 0) - (1 if keys.get(37, False) else 0)
    AXIS_Y = (1 if keys.get(40, False) else 0) - (1 if keys.get(38, False) else 0)
    SPEED_X += AXIS_X * 0.5
    SPEED_Y += AXIS_Y * 0.5

def grid():
    """
    Draw:
      - Evenly spaced vertical lines (in GRID_COL)
      - Evenly spaced horizontal lines (in GRID_COL)
      - Axes at origin (in ORIGIN_COL)
      - Screen boundary lines (in SCREEN_COL)
    """
    strokeWeight(1)
    stroke(GRID_COL)

    # Vertical lines
    cols = int(width / SCALE) // UNITY + 2
    for xi in range(cols):
        x_screen = xi * UNITY - GLOBAL_X + (GLOBAL_X % UNITY)
        line(x_screen, -GLOBAL_Y, x_screen, height / SCALE - GLOBAL_Y)

    # Horizontal lines
    rows = int(height / SCALE) // UNITY + 2
    for yi in range(rows):
        y_screen = yi * UNITY - GLOBAL_Y + (GLOBAL_Y % UNITY)
        line(-GLOBAL_X, y_screen, width / SCALE - GLOBAL_X, y_screen)

    # Origin axes
    stroke(ORIGIN_COL)
    strokeWeight(2)
    line(-GLOBAL_X, 0, width / SCALE - GLOBAL_X, 0)
    line(0, -GLOBAL_Y, 0, height / SCALE - GLOBAL_Y)

    # SCREEN boundary
    stroke(SCREEN_COL)
    strokeWeight(2)
    line(-GLOBAL_X, SCREEN_HEIGHT, width / SCALE - GLOBAL_X, SCREEN_HEIGHT)
    line(SCREEN_WIDTH, -GLOBAL_Y, SCREEN_WIDTH, height / SCALE - GLOBAL_Y)


# -------------------- COLOR‐PICKER UTILITY --------------------

def pickMouse():
    """
    Pick color from pixel under mouse (unscaled coords) and assign to SELECTED_COL.
    """
    global SELECTED_COL
    loadPixels()
    idx = mouseX + mouseY * width
    if 0 <= idx < len(pixels):
        SELECTED_COL = pixels[idx]


# -------------------- SETTERS FOR UTILITY COMMANDS --------------------

def setUnity(args):
    """Set UNITY from args[0]."""
    global UNITY
    UNITY = int(args[0])

def setColor(args):
    """Set SELECTED_COL from [r, g, b]."""
    global SELECTED_COL
    r = int(args[0]); g = int(args[1]); b = int(args[2])
    SELECTED_COL = color(r, g, b)

def setPNAME(args):
    """Override P_NAME to args[0] + '.txt'."""
    global P_NAME
    P_NAME = args[0] + ".txt"


# -------------------- PROCESSING SETUP & DRAW --------------------

def setup():
    """
    Initialize fullScreen, enable color variables, set modes, textSize, etc.
    """
    global GRID_COL, ORIGIN_COL, SHAPE_BOR_COL, TOOL_BG_SEL, TOOL_BG, SCREEN_COL, SELECTED_COL

    # Create a full-screen window
    fullScreen()
    # Convert RGB‐tuples into actual Processing colors now that the context exists
    GRID_COL      = color(_GRID_RGB[0], _GRID_RGB[1], _GRID_RGB[2])
    ORIGIN_COL    = color(_ORIGIN_RGB[0], _ORIGIN_RGB[1], _ORIGIN_RGB[2])
    SHAPE_BOR_COL = color(_SHAPE_BOR_RGB[0], _SHAPE_BOR_RGB[1], _SHAPE_BOR_RGB[2])
    TOOL_BG_SEL   = color(_TOOL_BG_SEL_RGB[0], _TOOL_BG_SEL_RGB[1], _TOOL_BG_SEL_RGB[2])
    TOOL_BG       = color(_TOOL_BG_RGB[0], _TOOL_BG_RGB[1], _TOOL_BG_RGB[2])
    SCREEN_COL    = color(_SCREEN_RGB[0], _SCREEN_RGB[1], _SCREEN_RGB[2])
    SELECTED_COL  = color(_SELECTED_RGB[0], _SELECTED_RGB[1], _SELECTED_RGB[2])

    rectMode(CENTER)
    textSize(TEXT_SIZE)


def draw():
    """
    Each frame:
      - Clear background
      - pushMatrix(): scale/translate → draw grid, shapes, handle anchor snatches
      - popMatrix()
      - Draw toolbox
      - Draw text command (if any)
      - Draw small swatch showing SELECTED_COL
    """
    global SCALE, MOVING, GLOBAL_X, GLOBAL_Y, ORIGIN_X, ORIGIN_Y, SPEED_X, SPEED_Y

    background(100)

    pushMatrix()
    scale(SCALE)
    translate(GLOBAL_X, GLOBAL_Y)

    # Draw the grid + axes
    grid()

    # Smooth camera movement
    SPEED_X *= 0.94
    SPEED_Y *= 0.94
    GLOBAL_X -= SPEED_X
    GLOBAL_Y -= SPEED_Y

    # Draw every shape
    for shp in shapes:
        shp.display()

    # Check which anchors live in the same SNATCHRAD cell as the mouse
    mx = mouseX / SCALE - GLOBAL_X
    my = mouseY / SCALE - GLOBAL_Y
    cell = (int(mx) // SNATCHRAD, int(my) // SNATCHRAD)
    if cell in QUADRANT:
        for punto in QUADRANT[cell]:
            punto.mouseSnatch()

    # If the mouse is pressed, either drag an anchor or create a new shape via selected tool
    if mousePressed:
        if SELECTED["type"] == "anchor":
            sel_anchor = SELECTED["data"]
            sel_anchor.move_visually(mx, my)
        elif SELECTED["type"] == "tool":
            tool_inst = SELECTED["data"]
            tool_inst.behaviour(mx, my)
    else:
        # On release, finalize anchor’s move & snap to grid
        if SELECTED["type"] == "anchor":
            sel_anchor = SELECTED["data"]
            if sel_anchor.parent is not None:
                sel_anchor.parent.update_visually(sel_anchor)
                sel_anchor.parent.update()
            sel_anchor.move()
            setSelected(None, None, (0, 0))

    # Handle camera panning with SPACE + drag
    if keyPressed:
        if key == CODED:
            updateSpeed()
        elif key == ' ':
            if mousePressed and SELECTED["type"] is None:
                cursor(HAND)
                MOVING = True
                GLOBAL_X = ORIGIN_X + mouseX / SCALE
                GLOBAL_Y = ORIGIN_Y + mouseY / SCALE
            else:
                MOVING = False
                ORIGIN_X = GLOBAL_X - mouseX / SCALE
                ORIGIN_Y = GLOBAL_Y - mouseY / SCALE

    popMatrix()

    # Draw the toolbox icons
    toolBox()

    # If user is typing a command, show TEXT_CACHE
    if len(TEXT_CACHE) > 0:
        textAlign(LEFT)
        fill(0)
        text(TEXT_CACHE, 45, height - 100)

    # Draw a small rectangle in top-left showing current SELECTED_COL
    fill(SELECTED_COL)
    noStroke()
    rect(60, 60, 100, 100, 50)
