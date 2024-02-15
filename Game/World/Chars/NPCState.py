
import math
import World.WorldCommon as WC
import World.world as World
from World.Chars.Character import AnimType
import sys
sys.path.append("../Server2D")
import Network.mySocket as sck
sys.path.pop()

class Action():
    def __init__(self, element):
        pass

    def Enter(self, char):
        pass

    def Exit(self, char):
        pass

    def Act(self, char, deltaTime):
        pass

class IdleAction(Action):
    def Enter(self, char):
        if not WC.ServerMode:
            char.animType = AnimType.IDLE
            char.walkChannel.pause()
            if char.healthBar is not None:          #defines the healthBar to not visible if enemy char is idle
                char.healthBar.visible = False

class WalkAction(Action):
    def Enter(self, char):
        if not WC.ServerMode:
            char.animType = AnimType.WALK
            char.walkChannel.unpause()
            if char.healthBar is not None:          #defines the healthBar to visible if enemy char is walking
                char.healthBar.visible = True
        super().Enter(char)

class ChaseAction(WalkAction):
    def __init__(self, element):
        self.speed = float(element.get("speed", 0))
        super().__init__(element)

    def Enter(self, char):
        self.target = WC.Players[0]
        char.moveDir, len = WC.ComputeDir(char.GetCenterPosition(), self.target.GetCenterPosition())
        super().Enter(char)

    def Act(self, char, deltaTime):
        WC.MoveDir(char, char.moveDir, self.target.GetCenterPosition(), self.speed, deltaTime)
        char.moveDir, len = WC.ComputeDir(char.GetCenterPosition(), self.target.GetCenterPosition())
        super().Act(char, deltaTime)

class ReturnAction(WalkAction):
    pass

def CreateAction(element):
    action = element.find("Action")
    if action is None:
        return None
    atype = action.get("type")
    if atype == "Idle":
        return IdleAction(action)
    if atype == "Chase":
        return ChaseAction(action)
    if atype == "Return":
        return ReturnAction(action)
    return None

class Decision():
    def __init__(self, element, state):
        self.state = state
        self.trueState = element.get("trueState")
        self.falseState = element.get("falseState")

    def Decide(self, char):
        return False
    
class PlayerInRange(Decision):
    def __init__(self, element, state):
        global SqrD 
        super().__init__(element, state)
        self.dist = int(element.get("distance"))
        self.distSqr = self.dist * self.dist
        SqrD = self.distSqr

    def Decide(self, char):
        if hasattr(self.state.action, "target"):
            target = self.state.action.target
        else:
            target = WC.Players[0]
            
        if not WC.ServerMode and not target.CharAlive:
            return False

        result = GetDifference(target, char)
        print(result)

        return result

class HomeInRange(Decision):
    pass

class WasAttacked(Decision):
    pass

class TimeIsUp(Decision):
    pass

def CreateDecision(element, state):
    type = element.get("decide")
    if type == "player_in_range":
        return PlayerInRange(element, state)
    if type == "home_in_range":
        return HomeInRange(element, state)
    if type == "was_attacked":
        return WasAttacked(element, state)
    if type == "time_is_up":
        return TimeIsUp(element, state)
    return None

def GetDifference(pl, el):
        global SqrD
        if pl is not None:
            plBox = pl.GetCollisionBox()
            aiBox = el.GetCollisionBox()
                
            xdiff = 0
            ydiff = 0
                
            if plBox.x > aiBox.x + aiBox.width:
                xdiff = plBox.x - (aiBox.x + aiBox.width)
            elif plBox.x + plBox.width < aiBox.x:
                xdiff = aiBox.x - (plBox.x + plBox.width)
                
            if plBox.y > aiBox.y + aiBox.height:
                ydiff = plBox.y - (aiBox.y + aiBox.height)
            elif plBox.y + plBox.height < aiBox.y:
                ydiff = aiBox.y - (plBox.y + plBox.height)

            length = xdiff * xdiff + ydiff * ydiff
            return length < SqrD

class State():
    def __init__(self, element):
        self.name = element.get("name")
        self.action = CreateAction(element)
        self.decisions = []
        for decision in element.findall("Decision"):
            d = CreateDecision(decision, self)
            self.decisions.append(d)

    def Update(self, char, deltaTime):
        self.action.Act(char, deltaTime)
        for decision in self.decisions:
            result = decision.Decide(char)
            if result:
                if decision.trueState != char.curState:
                    self.action.Exit(char)
                    return decision.trueState
            else:
                if decision.falseState != char.curState:
                    self.action.Exit(char)
                    return decision.falseState
        
        return None