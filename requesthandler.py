# -*- coding: utf-8 -*-
import configs
import filecontextmanager
import stringutils
import os
 
#მსობელი კლასი.მისი ობიექტის შექმნა შეუძლებელია
class RequestHandler:
     def __init__(self):
      raise Exception("cant create object of request handler class")

     #ეს მეთოდი უნდა გადაფაროს შვილობილმა კლასმა
     def handle(self,client_socket,addr,chat_server):
        pass



#RequestHandler-ის შვილობილი კლასი რომელიც ამუსავებს ვებ მოთხოვნებს
class WebRequestHandler(RequestHandler):

    def __init__(self,config):
        self.conf=config
        self.context_manager = filecontextmanager.ContextManager(self.conf)




    def handle(self,client_socket,addr,chat_server):

        #ენიჭება კლიენტის სახელი გადაყვანილი md5-ში
        hash = ""

        #dictionary რომელიც გამოიყენება web_responce-ს ფორმატირების დროს
        res_headers = {"rstatus": "200 OK", "rtype": "text", "rfext": "html", "retag": "","clen":""}

        try:

            # მივიღოთ კლიენტისგან მოთხოვნა,დავაწესოთ ოპერაციისთვის დროითი ლიმიტი
            client_socket.settimeout(self.conf.socket_time_out)
            request = client_socket.recv(self.conf.socket_buf_limit).decode()
            client_socket.settimeout(None)

            # ამოვიღოთ მოთხოვნიდან ფაილის სახელი
            file_name = stringutils.parse_text(request, self.conf.file_from_req_text)
           
            try:
              print("client:{0} need file:{1}".format(addr, file_name))
            except:
              print("unsuported character to print or windows dont suport utf8 in console :facepalm:")
            #ამოვიღოთ მოთხოვნიდან etag (სტატიკური ფაილების ქეშირებისთვის)
            etag = stringutils.parse_text(request, self.conf.etag_from_req_text)


            # ამ ცვლადში ვინახავთ ფაილის სავარაუდო გაფართოებას
            extension = ".html"

             # http პასუხის ჰედერები
            responce_header = self.conf.web_responce

             # თუ ფაილის სახელი ცარიელია ,ავტომატურად მივანიჭოთ index.html
            if (file_name == ""):
                file_name = "index.html"





            else:

               # შევამოწმოთ ფაილის გაფართოება თუ ემთხვევა სურათის გაფართოებებს
                for extens in self.conf.image_files:

                    # თუ ემთხვევა მაშინ შევცვალოთ http ჰედერები
                    if (file_name.endswith(extens)):
                        extension = ""
                        res_headers["rtype"] = "image"
                        res_headers["rfext"] = extens.replace(".", "")
                         
                        
                        break



                
                    #ვებ სერვერი იმუშავებს ფაილის სახელ როგორც index.html ასევე index ზე ან chat.html ან chat და სე შემდეგ..
                    #თუ მოთხოვნილი ფაილი არ აღმოჩნდა web დირექტორიაშო ფაილის სახელი გავუტილოთ eror404.html
                if (os.path.isfile(self.conf.web_path+file_name + extension)):
                    file_name = file_name + extension
                elif (not os.path.isfile(self.conf.web_path+file_name)):
                   
                    file_name = "eror404.html"
                    res_headers["rtype"] = "text"
                    res_headers["rfext"] = "html"
                   



              

            # ამოვიღოთ ფაილის ბიტები და etag(წარმოადგენს ფაილის ბოლო შევცლის თარიღს)
            file_context, saved_etag = self.context_manager.get_context(file_name)

            #http პასუხის ჰედერი ეტაგ შევცვალოთ მნიშვნეობით
            res_headers["retag"] = str(saved_etag)
            res_headers["clen"]=len(file_context)
            #თუ კლიენტისგან მოსული ფაილის სახელის ეტაგ ემთხვევა ჩვენ ფაილის ეტაგს(ესეიგი ფაილი არ შეცვლილა)
            #შევცვალოთ http პასუხის ჰედერები და წაკითხული ბიტები გავანულოთ
            if (str(saved_etag) == etag and file_name != "chat.html"):
                res_headers["rstatus"] = "304 Not Modified"
                file_context = b""

            # თუ ფაილის სახელია chat.html ყოველთვის ახალი უნდა გაიგზავნოს
            if (file_name == "chat.html"):

                 # ამოვიღოთ კლიენტის სახელი ჩატის მოთხოვნიდან
                client_name = stringutils.parse_client_name(request, self.conf.client_name_from_req_text)
                if (not client_name):
                    raise Exception("empty client name")
                hash = stringutils.get_md5(client_name)

                # თუ კლიენტის ჰეში სიაში არ გვაქვს ან გვაქვს მაგრამ სოკეტი არ აქვს მინიჭებული

                if not chat_server.execute_synced(chat_server.sync_user_exist, hash) or not chat_server.execute_synced(chat_server.sync_get_client_socket,hash):

                    # დავამატოთ კლიენტი სიაში
                    #შევცვალოთ chat.html -ში არსებული პარამეტრები.

                    chat_server.execute_synced(chat_server.sync_add_client_name, hash, client_name)

                    #აღვადგინოთ საწყისი ბიტები კომპრესირებული ბიტებიდან
                    file_context=stringutils.gzip_decompress(file_context).decode()
                     
                    #შევცავლოთ პარამეტრები chat.html ფაილში
                    file_context =file_context.replace("-uid-", hash)
                    file_context =file_context.replace("-serverip-", self.conf.server_ip)
                    file_context =file_context.replace("-chatserverport-", str(chat_server.conf.server_port))
                    file_context =file_context.encode()

                    #საწყის ბიტებს გავუკეთოტ ისევ კომპრესია
                    file_context=stringutils.gzip_compress(file_context,self.conf.gzip_compress_level)
                    res_headers["clen"]=len(file_context)
                    #თუ კლიენტის სახელი უკვე სიაშია შევცალოთ გასაგზავნი ბიტები Choose another name-ით
                else:

                    file_context = "Choose another name".encode()
                    responce_header = ""

            
                     # გავუგზავნოთ კლიენტს პასუხი,დავაწესოთ ოპერაციისთვის დროითი ლიმიტი
            client_socket.settimeout(self.conf.socket_time_out)
            client_socket.sendall(responce_header.format(**res_headers).encode() + file_context)
            client_socket.settimeout(None)



        except Exception as e:

            # შეცდომის შემთხვევაში წავშალოთ კლიენტი
            chat_server.execute_synced(chat_server.sync_del_client, hash)

            print("eror during webrequest handle " + str(e))


        finally:
             # ბოლოს დავხუროთ სოკეტი
            client_socket.close()




#RequestHandler-ის შვილობილი კლასი რომელიც ამუსავებს ჩატ მოთხოვნებს
class ChatRequestHandler(RequestHandler):

     def __init__(self,config):
        self.conf=config
       
    
     def handle(self, client_chat_socket, addr,chat_server):

          #   თუ ხელმოწერა წარმატებით დასრულდა ,დავიწყოთ კლიენტისგან მესიჯების მოსენა
        hash = chat_server.web_socket_handshake(client_chat_socket, addr)

        if (hash):
           chat_server.receive_message_sesion(client_chat_socket, hash, addr)

 