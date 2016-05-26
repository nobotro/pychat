# -*- coding: utf-8 -*-
import os
import threading
import configs
import datetime
import stringutils

class ContextManager():
    def __init__(self, config):

        # ჩავტვირთოთ კონფიგის პარამეტრები
        self.conf = config

        # ნაკადების მბლოკავის ინიციალიზება.რათა არ მოხდეს ორ ნაკადის შორის საერთო რესურსზე ერთდროული წვდომა
        self.thread_lock = threading.Lock()
        
    
    # აბრუნებს ფაილის შიგთავსს
    def get_context(self, file_name):

        context = None
        time = None
        f = None
        # თუ ამ ფაილის შიგთავსი უკვე გვაქვს ქეშში,მაშინ დავაბრუნოთ ქეშიდან და აღარ წავიკიხოთ ფაილი
        if (file_name in self.conf.file_cache):

            return self.conf.file_cache[file_name][0], self.conf.file_cache[file_name][1]

        else:

            # დავბლოკოთ კოდის ქვემოთა ნაწილი(იგივე სინქრონული ბლოკი)
            self.thread_lock.acquire()

            # ორი შემოწმება საჭიროა ბევრი ნაკადისთვის.
            # თუ რამდენიმე ნაკადი ერთდროულად შემოვიდა else-ში მაშინ ყველა მათგანი წაიკითხავს
            # ერთიდაიგივე ფაილს,ამის ასარიდებლად საჭიროა შევამოწმოთ მეორეჯერ,უკვე ხომ არ წაიკითხა წინა ნაკადმა ფაილი?
            # თუ წაიკითხა დავაბრუნოთ უკვე ამოკითხული,თუ არა მაშინ წავიკითხოთ ფაილი
            if (file_name in self.conf.file_cache):
                return self.conf.file_cache[file_name][0], self.conf.file_cache[file_name][1]

            try:
                # ფაილის წაკითხვა
                f = open(self.conf.web_path + file_name, mode="rb")
                context = f.read()
                
        
             
                context = stringutils.gzip_compress(context,self.conf.gzip_compress_level)                
                                             
                #ამოვიღოთ ფაილის ბოლოს მოდიფიცირების თარიღი
                time = os.path.getmtime(f.name)
                # ფაილის შიგთავსის ქეშში ჩაგდება

                self.conf.file_cache[file_name] = [context, time]

            except Exception as e:

                print("eror getting context" + str(e))

            finally:
                if (f is not None):
                    f.close()

            # მოვხსნათ ნაკადების ბლოკი
            self.thread_lock.release()
             
            return (context, time)
