# -*- coding: utf-8 -*-





import configs
 
 
import server
import requesthandler
import threading
def main():
    webconfig = configs.WebServerConfig()
    chatconfig = configs.ChatServerConig()
    web_request_handler=requesthandler.WebRequestHandler(webconfig)
    chat_request_handler=requesthandler.ChatRequestHandler(chatconfig)

    chatsrver = server.ChatServer(chat_request_handler)
    webserver = server.WebServer(chatsrver,web_request_handler)
    
    webserverthread = threading.Thread(target= webserver.start, args=())
    webserverthread.start()
    
    print("server started at {0}:{1}".format(webconfig.server_ip,webconfig.server_port))
    
    chatserverthread = threading.Thread(target= chatsrver.start, args=())
    chatserverthread.start()
    
    
    print("chatserver started at {0}:{1}".format(chatconfig.server_ip,chatconfig.server_port))

# main

if __name__ == '__main__': main()
