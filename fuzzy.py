import pandas as pd
import numpy as np
from fuzzywuzzy import process
from flask_pymongo import PyMongo
import pymongo
import math
import os.path
# from deepface import DeepFace


data = pymongo.MongoClient("mongodb://localhost:27017")['FPD']['data']

path = "/home/dinky/Documents/fake-profile-detector/static/images/"

sameface = {}


def match(user=''):

    if user == '':
        return 0

    elif(len(list(data.find({"username": user})))):

        details = list(data.find({"username": user}))[0]

        matchface = []
        pnames = []

        if user in sameface:
            matchface = sameface[user]
            pnames = [i[0] for i in matchface]

        matchuname, unames = match_param(details['username'], 'username')
        matchfname, fnames = match_param(details['fullname'], 'fullname')
        matchbio, bnames = match_param(
            details['description'], 'description')
        matchlink, lnames = match_param(
            details['external_link'], 'external_link')
        dnames = match_param(details['dob'], 'dob')

        res = list(set(list(set(unames) & set(fnames)) + list(set(fnames) & set(bnames)) + list(set(unames) & set(bnames)) + list(set(pnames) & set(unames)) + list(set(pnames) & set(fnames)) + list(set(pnames) & set(bnames)) + list(set(dnames) & set(unames))
                       + list(set(dnames) & set(fnames)) + list(set(dnames) & set(bnames)) + list(set(dnames) & set(pnames)) + list(set(lnames) & set(unames)) + list(set(lnames) & set(fnames)) + list(set(lnames) & set(bnames)) + list(set(lnames) & set(pnames)) + list(set(lnames) & set(dnames))))
        res2 = list(set(list(set(pnames) & set(unames)) + list(set(pnames) & set(fnames)) + list(
            set(pnames) & set(bnames)) + list(set(dnames) & set(pnames)) + list(set(lnames) & set(pnames))))

        if(len(res)):

            temp = []

            for x in res:
                if(x != user):
                    usr = list(data.find({'username': x}))[0]

                    a, b, c, d, e, f, g = 0, 0, 0, 0, 0, 0, 0

                    if(len([i[2] for i in matchuname if i[0] == x])):
                        a = [i[2] for i in matchuname if i[0] == x][0]
                    if(len([i[2] for i in matchfname if i[0] == x])):
                        b = [i[2] for i in matchfname if i[0] == x][0]
                    if(len([i[2] for i in matchbio if i[0] == x])):
                        c = [i[2] for i in matchbio if i[0] == x][0]
                    if(len([i[2] for i in matchlink if i[0] == x])):
                        d = [i[2] for i in matchlink if i[0] == x][0]
                    if x in dnames:
                        e = 1
                    if x in res2:
                        f = (1 - float([j[1]
                                        for j in matchface if j[0] == x][0]))*100

                    commons = len(set([i for i in usr["friends"].strip("][").split(", ") if i != ""]) & set(
                        [i for i in details["friends"].strip("][").split(", ") if i != ""]))

                    g = round(commons /
                              (min(usr['friends_count'], details['friends_count']))*100, 2)

                    image = f"/static/images/{x}.jpg" if os.path.exists(
                        path + str(x) + ".jpg") else "/static/images/no.jpg"

                    percent = round((a + b + c + d + e*100 + f + g) / 7, 2)
                    if(percent > 35):
                        temp.append((
                            x,
                            image,
                            commons,
                            usr['reports'],
                            percent,
                            a,
                            b,
                            c,
                            d,
                            e,
                            f,
                            g,
                            usr['is_suspended']
                        ))

            response = sorted(
                temp, key=lambda item: item[11], reverse=True)

            return response

        return 'No response'


def match_param(val, param):
    par = [(i['username'], i[param]) for i in list(data.aggregate(
        [{"$match": {'is_fake': 1}}, {"$project": {'username': 1, param: 1, "_id": 0}}]))]

    if(param == 'dob'):
        return [d[0] for d in par if((val.year == d[1].year and val.month == d[1].month) or (val.day == d[1].day and val.month == d[1].month))]
    else:
        if(val):
            res = []
            result = process.extract(val, [i[1] for i in par])
            for i in result:
                r = list(data.aggregate([{"$match": {param: i[0]}}, {
                         "$project": {"username": 1, "_id": 0}}]))

                if([(x['username'], i[0], i[1]) for x in r] not in res):
                    res += [(x['username'], i[0], i[1]) for x in r]

            return res, [y[0] for y in res]

        return [], []
