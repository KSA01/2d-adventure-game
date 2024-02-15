
import pygame
import World.WorldCommon as WC
import threading

import sys
sys.path.append("../Server")
import Network.mySocket as sck
sys.path.pop()

# Press enter key to open chat window
# when chat window is open, you can enter the message
# Chat window closes when the enter key is pressed
# Chat window shows history of past entered messages
# Ignore other uses of keys when entering chat

_CHAT_HIST_MAX = 5 # Max size of history

def Init():
    global _chatOpen # Is the chat active?
    global _chatHistory # List of past messages
    global _curMessage # Current message being entered
    global _chatSurf # Surface for displaying current message
    global _font # Font used in chat

    _chatOpen = False
    _chatHistory = []
    _curMessage = ""
    _chatSurf = None
    _font = pygame.font.SysFont("arial", 24) # Chat font
    
    p = threading.Thread(target=_PostMessage) #thread for post message so the game doesn't slow down/freeze
    p.daemon = True
    p.start()

def _OpenChat():
    global _chatOpen
    global _chatSurf
    global _font

    _chatOpen = True
    _chatSurf = _font.render(": ", True, (0,0,0))

def _CloseChat():
    global _chatOpen
    global _chatSurf

    _chatOpen = False
    _chatSurf = None

def _AddChat(c):
    global _curMessage 
    global _chatSurf 
    global _font

    if not c:
        return
    
    success = False
    if c == '\b':
        if _curMessage != "":
            _curMessage = _curMessage[:-1]
            success = True
    elif ord(c) >= 32 and ord(c) <= 126: # ASCII
        _curMessage += c
        success = True

    if success:
        _chatSurf = _font.render(": " + _curMessage, True, (0,0,0))

# Function to send the current message to server to post to chat history
def _SendMessage():
    global _curMessage

    if _curMessage == "":
        return

    # Send message to server
    #print(f"Sending {str(_curMessage)} to server")
    sck.SendMessage("SendChatMes", str(_curMessage))

# Actually posts the message to server if it recieves one from the server
def _PostMessage():
    global _curMessage
    global _chatHistory
    global _CHAT_HIST_MAX
    global _font

    while True: #thread stays checking for a message from server for chat
        mes = sck.GetMessage("ReturnChatMes")  # Waits for a message from the server: It may take a couple or more seconds
        if mes is not None: # Once it recieves a valid message it posts to chat history
            #print(f"Added {str(mes)} to chat log")
            _chatHistory.append(_font.render("me: " + str(mes), True, (0, 0, 0)))  # mes is _curMessage
            if len(_chatHistory) > _CHAT_HIST_MAX:
                del _chatHistory[0]

            _curMessage = ""

def ProcessEvent(event):
    global _chatOpen
    
    if event is not None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if not _chatOpen:
                    _OpenChat()
                else:
                    _SendMessage()
                    _CloseChat()
                return True
            elif _chatOpen:
                c = event.unicode
                if event.key == pygame.K_BACKSPACE: # Backspace key
                    c = '\b'
                _AddChat(c)
                return True
        elif event.type == pygame.KEYUP and _chatOpen:
            return True

    return False

def Update(deltaTime):
    pass

def Render(screen):
    global _chatOpen
    global _chatSurf
    global _chatHistory
    
    rect = pygame.Rect((0, WC.ScreenSize[1]), (0,0))
    if _chatOpen:
        rect.top -= _chatSurf.get_height()
        screen.blit(_chatSurf, rect)

    for surf in reversed(_chatHistory):
        rect.top -= surf.get_height()
        screen.blit(surf, rect)