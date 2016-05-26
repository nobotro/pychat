# -*- coding: utf-8 -*-
import hashlib
import base64
import gzip

def parse_client_name(text, element_touple):
    result = ""
    try:

        # ამოვიღოთ სტრიქონიდან ტექსტი,მითითებული პატერნისის მიხედვით
        start = text.find(element_touple[0]) + len(element_touple[0])
        end = text.find(element_touple[1], start)
        assert start != 4, "start ==4 cant find start"
        if (end == -1):
            result = text[start:]
        else:
            result = text[start:end]

    except Exception as e:
        print("parse eror" + str(e))

    finally:

        return result


def parse_text(text, element_touple):
    result = ""
    try:

        # ამოვიღოთ სტრიქონიდან ტექსტი,მითითებული პატერნისის მიხედვით
        start = text.index(element_touple[0]) + len(element_touple[0])
        end = text.index(element_touple[1], start)

        result = text[start:end]

    except Exception as e:
        print("parse eror elementtuple{0}".format(str(element_touple)) + str(e))

    finally:

        return result


def get_md5(text):
    return str(hashlib.md5(text.encode()).hexdigest())

def gzip_compress(data,level):
    return gzip.compress(data,compresslevel=level)


def gzip_decompress(data):
    return gzip.decompress(data)


def generate_responce_key(key):
    # ვებ სოკეტის კოდი
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
