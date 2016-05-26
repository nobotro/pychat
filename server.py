# -*- coding: utf-8 -*-
import socket
import threading
import socket
import os
import stringutils
import filecontextmanager
import re
import json


#მსობელი კლასი.მისი ობიექტის შექმნა შეუძლებელია
class Server:
    def __init__(self):
      raise Exception("cant create object of server class")

    #ეს მეთოდი მემკვიდრეობით გადაეცემათ chatserver-ს და webserver-ს
    def start(self):

        #იხსნება სოკეტი და იწყება პორტზე მოსმენა
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.conf.server_ip, self.conf.server_port))
        sock.listen(5)
      

        while True:
           
            conn, addr = sock.accept()

            #თუ კლიენტი დაგვიკავშირდა გადავცეთ ის webrequesthandler-ს
            thr = threading.Thread(target=self.request_handler.handle, args=(conn,addr,self.chat_server))
            thr.start()

#server-ს შვლობილი კლასი ვებ სერვერი
class WebServer(Server):

    #ვებსერვერის ინიციალიზება
    def __init__(self,chat_server,request_handler):

        #ამუშავებს ვებ სერვერზე მოსულ მოთხოვნებს
        self.request_handler=request_handler

        #შეიცავს ვებ სერვერის პარამეტრებს(config)
        self.conf = request_handler.conf
       
        #ეს არი ჩატ სერვერის ცვლადი რომელიც ჩატ სერვერზე მიმართვისთვის გვწირდება
        self.chat_server = chat_server

#server-ს შვლობილი კლასი ჩატ სერვერი
class ChatServer(Server):

    #ჩატსერვერის ინიციალიზება
    def __init__(self,request_handler):

        #კონკრეტულ,მიმდინარე ჩატსერვერის ობიექტს ვინახავთ ცვლადში რათა მემკვიდრეობით გადმოცემულმა 
        #start მეთოდმა ამოიღოს ამ ობექტიდან ვებ სერვერი
        self.chat_server = self
        self.request_handler=request_handler
        self.conf = request_handler.conf
        self.chat_server_clients = {}
        self.thread_lock = threading.Lock()
  
      
    #თვითოეული კლიენტისთვის იქმნება ახალი მესიჯის მიღების სესია ახალ ნაკადში
    #ეს მეოდი გამოიძახება ChatRequestHandler-ის მიერ
    def receive_message_sesion(self, client_chat_socket, hash, addr):

        try:
            #ამოვიღოთ სიიდან ყველა კლიენტის სახელი
            users = self.sync_get_clients_name(hash)

            #კლიენტს რომლის სესიაშიც ვიმოფებით გავუგზავნოთ მომხმარებლების სია
            self.send_message(client_chat_socket,
                              self.create_message_body(self.conf.action_send_users_list, "all", users))

            #უსასრულო ციკლი რათა კლიენტისგან ინფორმაციის მიღება არ შეწყდეს
            while True:
                

                #ველოდებით კლიენტისგან ინფორმაციის მიღებას
                data = client_chat_socket.recv(self.conf.socket_buf_limit)

                # თუ კლიენტისგან მივიღეთ ცარიელი სომბოლო ან "0x88"
                # "0x88"- ამას ფირეფოქს აბრუნებს ვებსოკეტის კავშირის გაწყვეტის მერე
                # გამოვიწვიოთ შეცდომა

                if (len(data) == 0 or data[0] == 0x88):
                    raise Exception("chat client {0} disconected".format(addr))

                #თუ არა მაშინ გავშიფროთ მესიჯი და გადავცეთ json_msg_handler-ს
                mes = self.decode_message(data)
                thr = threading.Thread(target=self.json_msg_handler, args=(mes, hash))
                thr.start()



        except Exception as e:

            #თუ კლიენტს სესიაში რომელშიც ეხლა ვიმყოფებით მოხდა შეცდომა,წავშალოთ ეს კლიენტი
            self.execute_synced(self.sync_del_client, hash)
            #დავბეჭდოთ შეცდომა
            try:
              print(str(e))
            except:
              print("unsuported character to print or windows dont suport utf8 in console :facepalm:")
           

            return

    def json_msg_handler(self, json_text, hash):
      try:
        #დავბეჭდოთ მიღებული ჯსონ ტექსტი
        try:
               print("jsontext: " + json_text)
        except:
              print("unsuported character to print or windows dont suport utf8 in console :facepalm:")
        
        
        #გავპარსოთ ჯსონ ტექსტი
        parsed_json = json.loads(json_text)

        #ამოვიღოთ სიიდან იმ კლიენტის სოკეტი,ვისაც გაუგზავნეს ეს მესიჯი
        socket = self.execute_synced(self.sync_get_client_socket, stringutils.get_md5(parsed_json["person"]))

        #შევამოწმოთ ესეთი კლიენტი და სოკეთი თუ არსებობს
        if (socket):

            #თუ მესიჯის action-არის ტექსტის გაგზავნა,ანუ მესიჯი არ წარმოადგენს სხვა ბრძანებას
            #ჯსონ მესიჯის მიმღების სახელი შევცვალოთ გამომგზავნის სახელით და გავუგზავნოთ მიმღებს

            if (parsed_json["action"] == self.conf.action_text):
                parsed_json["person"] = self.execute_synced(self.sync_get_client_name, hash)

                self.send_message(socket,
                                  self.create_message_body(parsed_json["action"], parsed_json["person"],
                                                           parsed_json["data"]))
      except Exception as e:
      
        self.execute_synced(self.sync_del_client, hash)      
        try:
              print(str(e))
        except:
              print("unsuported character to print or windows dont suport utf8 in console :facepalm:")
           

  
              
    #მეთოდი ახდენს ჯსონ მესიჯის შიფრაციას ვებსოკეტების პროტოკოლის შესაბამისად
    def create_message_body(self, action, person, data):

        json_msg = json.dumps({"action": action, "person": person, "data": str(data)})
        bytes_formatted = []
        bytes_formatted.append(129)

        bytes_raw = json_msg.encode()
        bytes_length = len(bytes_raw)
        if bytes_length <= 125:
            bytes_formatted.append(bytes_length)
        elif bytes_length >= 126 and bytes_length <= 65535:
            bytes_formatted.append(126)
            bytes_formatted.append((bytes_length >> 8) & 255)
            bytes_formatted.append(bytes_length & 255)
        else:
            bytes_formatted.append(127)
            bytes_formatted.append((bytes_length >> 56) & 255)
            bytes_formatted.append((bytes_length >> 48) & 255)
            bytes_formatted.append((bytes_length >> 40) & 255)
            bytes_formatted.append((bytes_length >> 32) & 255)
            bytes_formatted.append((bytes_length >> 24) & 255)
            bytes_formatted.append((bytes_length >> 16) & 255)
            bytes_formatted.append((bytes_length >> 8) & 255)
            bytes_formatted.append(bytes_length & 255)

        bytes_formatted = bytes(bytes_formatted)
        bytes_formatted = bytes_formatted + bytes_raw
        return bytes_formatted


    #მეთოდი აგზავნის მესიჯს და თან აყენებს დროით ინტერვალს ამ ოპერაციისთვის
    def send_message(self, client_chat_socket, msg):


        client_chat_socket.settimeout(self.conf.socket_time_out)
        client_chat_socket.sendall(msg)
        client_chat_socket.settimeout(None)




    #მეთოდი chatserver-ის ყველა კლიენტს უგზავნის მესიჯს.
    #ეს მეთოდი გამოიყენება სერვერზე ახალი კლიენტის დამატების ან წაშლის დროს
    def send_broadcast(self, msg, usrs):

        for user in usrs:

            try:
                thr = threading.Thread(target=self.send_message,
                                       args=(user, msg))
                thr.start()
                thr.join()

            except Exception as e:
                continue


    #მეთოდი გაშიფრავს ვებსოკეტისგან მიღებულ მონაცემებს
    def decode_message(self, string_streamIn):
        byte_array = string_streamIn
        data_length = byte_array[1] & 127
        index_first_mask = 2
        if data_length == 126:
            index_first_mask = 4
        elif data_length == 127:
            index_first_mask = 10
        masks = [m for m in byte_array[index_first_mask: index_first_mask + 4]]
        index_first_data_byte = index_first_mask + 4
        decoded_chars = []
        i = index_first_data_byte
        j = 0
        while i < len(byte_array):
            decoded_chars.append(byte_array[i] ^ masks[j % 4])
            i += 1
            j += 1
        return bytearray(decoded_chars).decode()

    #მეთოდი გამოიძახება chatrequesthandler-ის მიერ ,ახალი კლიენტის დაკავშირების დროს
    #მეთოდი ანხორციელებს ვებსოკეტების hanshake-ს ახალ კლიენტთან და წარმატებით დასრულების შემთხვევაში
    #კლიენტს ამატებს მომხმარებლების სიაში

    def web_socket_handshake(self, client_chat_socket, addr):

        try:
            # დავუწესოთ კლიენტს ინფორმაციის გამოსაგზავნად დროითი ინტერვალი
            client_chat_socket.settimeout(self.conf.socket_time_out)

            text = client_chat_socket.recv(self.conf.socket_buf_limit).decode()

            # ინფორმაცია მიღებულია გავაუქმოთ დროითი ინტერვალი
            client_chat_socket.settimeout(None)

            # ამოვიღოთ კლიენტის მოთხოვნიდან ვებსოკეტის კოდი და დავაფორმიროთ პასუხი
            key = (re.search('Sec-WebSocket-Key:\s+(.*?)[\n\r]+', text)
                   .groups()[0]
                   .strip())

            # ამოვიღოთ კლიენტის მოთხოვნიდან ჰეში
            hash = stringutils.parse_text(text, self.conf.client_hash_from_websckt_req_text)

            # თუ მომხმარებელის სახელი არაა სიაში
            if (not self.execute_synced(self.sync_user_exist, hash)):
                raise Exception("name not in list")

            # დავაგენერიროთ ვებსოკეტის კეი და პსუხი
            response_key = stringutils.generate_responce_key(key)
            response = '\r\n'.join(self.conf.websocket_answer).format(key=response_key)

            # დავუწესოთ კლიენტს ინფორმაციის მისაღებად დროითი ინტერვალი
            client_chat_socket.settimeout(self.conf.socket_time_out)

            # გავუგზავნოთ ვებსოკეტს პასუხი
            client_chat_socket.sendall(response.encode())

            # ინფორმაცია გაგზავნილია გავაუქმოთ დროითი ინტერვალი
            client_chat_socket.settimeout(None)

            # თუ ყველაფერმა წარმატებიტ ჩაიარა ,მივანიჭოთ კლიენტს მისი სოკეტი
            self.execute_synced(self.sync_set_socket_to_client, hash, client_chat_socket)

            return hash



        except Exception as e:

            if (str(e) == "name not in list"):
                self.execute_synced(self.sync_del_client, hash)

            print("eror during handshake client{0}".format(addr) + str(e))
            return False

    # მეთოდების სინქრონიზებული შემსრულებელი
    def execute_synced(self, func, *args):

        self.thread_lock.acquire()
        res = func(*args)
        self.thread_lock.release()
        return res

    # აბრუნებს დადასტურებულ კლიენტების სიას
    def sync_get_clients_name(self, hash):
        return [self.chat_server_clients[b][0] for b in self.chat_server_clients if
                len(self.chat_server_clients[b]) > 1 and b != hash]

    def sync_get_clients_sockets(self):
        return [self.chat_server_clients[b][1] for b in self.chat_server_clients if
                len(self.chat_server_clients[b]) > 1]

    # ამატებს ახალ კლიენტს(ჰეშს და სახელს)
    def sync_add_client_name(self, hash, client_name):

        self.chat_server_clients[hash] = [client_name]

    # კლიენტს ანიჭებს სოკეტს
    def sync_set_socket_to_client(self, hash, client_socket):

        self.send_broadcast(self.create_message_body("auser", "all", self.sync_get_client_name(hash)),
                            self.sync_get_clients_sockets())

        self.chat_server_clients[hash].append(client_socket)

        user = self.sync_get_client_name(hash)

        try:
               print("added chat client {0} ".format(user) + " users Count{0}".format(len(self.sync_get_clients_sockets())))

        except:
              print("unsuported character to print or windows dont suport utf8 in console :facepalm:")
           
        
    # შლის კლიენტის ჩანაწერს,თუ არსებობს
    def sync_del_client(self, hash):

        if (self.sync_user_exist(hash)):
            socket = self.sync_get_client_socket(hash)
            if (socket):
                socket.close()

            user = self.sync_get_client_name(hash)

            del self.chat_server_clients[hash]

            thr = threading.Thread(target=self.send_broadcast,
                                   args=(
                                   self.create_message_body("ruser", "all", user), self.sync_get_clients_sockets()))
            thr.start()
            thr.join()
            try:
              print("deleted chat client {0} ".format(user) + " users Count{0}".format(len(self.sync_get_clients_sockets())))

            except:
              print("unsuported character to print or windows dont suport utf8 in console :facepalm:")
             
    # ამოწმებს არსებობს თუ არა კლიენტი
    def sync_user_exist(self, hash):

        return hash in self.chat_server_clients

      
    #აბრუნებს კლიენტის სახელს
    def sync_get_client_name(self, hash):
        return self.chat_server_clients[hash][0]



    # აბრუნებს კლიენტის სოკეტს
    def sync_get_client_socket(self, hash):

        if (self.sync_user_exist(hash) and len(self.chat_server_clients[hash]) == 2):
            return self.chat_server_clients[hash][1]

        return False