# -*- coding: utf-8 -*-
import os


class Config():

    #სერვერის ლინუქსზე გაშვების შემთხვევაში ფაირვოლის გასაწერი წესები,დოსის საწინააღმდეგოდ
    
    #1)ჩატსერვერის პორტზე 443 ერთიდაიგივე უკვე დაკავშირებული იპიდან მიიღება მხოლოდ წამში 50 პაკეტი,ზედმეტი პაკეტები ჩავარდება
    #iptables -A INPUT -p tcp --dport 443 -m state --state RELATED,ESTABLISHED -m limit --limit 50/second -j ACCEPT
     
    #2)ვებსერვერის პორტზე 80 ერთიდაიგივე უკვე დაკავშირებული იპიდან მიიღება მხოლოდ წამში 50 პაკეტი,ზედმეტი პაკეტები ჩავარდება
    #iptables -A INPUT -p tcp --dport 80 -m state --state RELATED,ESTABLISHED -m limit --limit 50/second -j ACCEPT
    
    #2)ჩატსერვერის პორტზე 443 ერთიდაიგივე იპიდან მიიღება ერთ წამში მხოლოდ 20 ახალი კლიენტი,ზედმეტი კლიენტების დაკავშირებები გაითიშებიან
    #iptables -I INPUT -p tcp --dport 443 -i eth0 -m state --state NEW -m recent --set
    #iptables -I INPUT -p tcp --dport 443 -i eth0 -m state --state NEW -m recent --update --seconds 1 --hitcount 20 -j DROP
    
    #2)ვებსერვერის პორტზე 80 ერთიდაიგივე იპიდან მიიღება ერთ წამში მხოლოდ 20 ახალი კლიენტი,ზედმეტი კლიენტების დაკავშირებები გაითიშებიან
    #iptables -I INPUT -p tcp --dport 80 -i eth0 -m state --state NEW -m recent --set
    #iptables -I INPUT -p tcp --dport 80 -i eth0 -m state --state NEW -m recent --update --seconds 1 --hitcount 20 -j DROP
    
    #3)არასრული,გაყალბებული tcp პაკეტები ჩავარდებიან
    #iptables -A INPUT -p tcp ! --syn -m state --state NEW -j DROP
    #iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP 
    #iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP




    # სერვერის იპ მისამართი

    server_ip = "192.168.0.100"
    # დროის ლიმიტი კლიენტისთვის(ინფორმაციის გამოგზავნის,დაკავშირების,ინფორმაციის მიღების)
    socket_time_out = 5

    # სოკეტის ბუფერის ლიმიტი(ერთი ქართული სიმბოლო=3 ბაიტი,ინგლისური=1 ბაიტი)
    socket_buf_limit = 3072  # ბაიტი


class WebServerConfig(Config):
    # ვებსერვერის პორტი
    server_port = 80

    # web ფაილების დირექტორია

    web_path = "/root/pychat/webfiles/"

    # ვებ მოთხოვნის სტრიქონიდან ,მოთხოვნილი ფაილის ამოღებისთვი საჭირო შაბლონი(საწყისი და საბოლოო სიმბოლო)
    file_from_req_text = ("/", " ")

    etag_from_req_text = ("If-None-Match: ", "\r")

    # ვებ მოთხოვნის სტრიქონიდან ,მოთხოვნილი ფაილის(chat.html)-ის შემთხვევაში clientname-წაკითხვის შაბლონი
    client_name_from_req_text = ("name=", "\r\n")

    # binary mode read files extensions
    image_files = (".jpeg", ".ico", ".gif")




    #Cache-Control:max-age=18000 მაქსიმუმ 5 საათი იქნება ფაილი ბრაუზერის ქეშში,მერე უკვე შეამოწმებს etags 
    #თუ განსხვავებული იქნება ახალს წამოიღებს,თუ არა ისევ ქეშიდან ამიღებს


    # web responce text
    web_responce = "HTTP/1.1 {rstatus} \nContent-Type: {rtype}/{rfext}\nCache-Control:max-age=18000\nETag:{retag}\nVary: Accept-Encoding\nContent-Encoding:gzip\nContent-Length:{clen}\n\n"

    # ქეში ფაილებისთვის(dictionary.{key,value})
    file_cache = {}

    #gzip კომპრესიის დონე.(gzip გამოიყენება ფაილების შესაკუმშად და ისე გასაგზავნად)
    gzip_compress_level=5

class ChatServerConig(Config):
    # ჩატსერვერის პორტი
    server_port = 443

    # პასუხი ვებ სოკეტის მოთხოვნაზე
    websocket_answer = (
        'HTTP/1.1 101 Switching Protocols',
        'Upgrade: websocket',
        'Connection: Upgrade',
        'Sec-WebSocket-Accept: {key}\r\n\r\n',
    )

    # ვებ სოკეტის კოდი
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    # ვებ სოკეტის მოთხოვნიდან ჰეშის ამოღების შაბლონი
    client_hash_from_websckt_req_text = ("hash?", " HTTP")

    # ვებ სოკეტის მესიჯის ფორმატი(json) "action:0,person:1,data:2"
    # action-მესიჯის მიზანი,to-პიროვნება ვინც გააგზავნა ან ვინც მიიღებს ამ მესიჯს,data-მესიჯის ტანი(მონაცემები)
    # action მნიშვნელობები text,usrslist,auser,ruser

    # თუ სერვერზე მივა მესიჯი რომელსა action-აქვს text,სერვერი ამოიკითხავს პიროვნებას ამ მესიჯიდან(ანუ ვისაც უგზავნის კლიენტი ამ მესიჯს)
    # პიროვნების მნიშვნელობას შეცვლის ამ მესიჯის გამომგზავნი პიროვნებით და გაუგზავნის პიროვნების პირველ მნივნელობის მქონე კლიენტს
    # სერვერი ამუშავებს კლიენტისგან მიღებულ მესიჯებს მხოლოდ იმ შემთხვევაში თუ მათი action არის text
    # თუ კლიენტზე მივა მესიჯი რომელსა action-აქვს text,კლიენტი ამოიკითხავს პიროვნებას(ანუ ვინ გაუგზავნა ამ კლიენტს მესიჯი) და დაბეჭდავს ეკრანზე

    action_text = "text"

    # თუ კლიენტზე მივა მესიჯი რომელსა action-აქვს usrs(ამ გზით სერვერი უგზავნის ახალ შემოსულ კლიენტს,არსებული კლიენტების სიას),კლიენტი ამოიკითხავს მნიშვნელობას(კლიენტების სიას) და
    # დაამატებს მათ chat.html-ს select id="names"-ელემენტში
    action_send_users_list = "users"

    # თუ კლიენტზე მივა მესიჯი რომელსა action-აქვს ruser(ამ გზით სერვერი უგზავნის შეტყობინებას ყველა კლიენტს, კლიენტის გათიშვაზე),კლიენტი ამოიკითხავს მნიშვნელობას(წაშლილ კლიენტს) და
    # წაშლის მას chat.html-ს <select id="names">-ელემენტიდან
    action_ruser = "ruser"

    # თუ კლიენტზე მივა მესიჯი რომელსა action-აქვს auser(ამ გზით სერვერი უგზავნის შეტყობინებას ყველა კლიენტს,ახალი კლიენტის დაკავშირებაზე),კლიენტი ამოიკითხავს მნიშვნელობას(ახალ კლიენტს) და
    # დაამატებს მას chat.html-ს <select id="names">-ელემენტში
    action_auser = "auser"
