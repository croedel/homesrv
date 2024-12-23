#!/usr/bin/env python3
"""
DBtimetableAPI Helper classes
(c) 2024 by Christian Rödel 
"""

import logging
#FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


#===============================================================
# Represents a timetable
class DBtimetable:
    #---------------------------
    def __init__(self, tt_type="departure"):
        self.tt_type = tt_type # departure or arrival 
        self.timetable = [] 

    #---------------------------
    def append(self, item):
        self.timetable.append(item)

    #---------------------------
    def extend(self, timetable):
        self.timetable.extend(timetable.timetable)

    #---------------------------
    def get_timetable(self):
        return self.timetable

    #---------------------------
    def sort(self, field, order="ASC"):
        reverse = True if order == "DESC" else False    
        if field == "date":
            self.timetable.sort(key=lambda k : k["date"], reverse=reverse)
        elif field == "train":
            self.timetable.sort(key=lambda k : k["train"], reverse=reverse)
        elif field == "from_to":
            self.timetable.sort(key=lambda k : k["from_to"], reverse=reverse)
        elif field == "platform":
            self.timetable.sort(key=lambda k : k["platform"], reverse=reverse)

    #---------------------------
    def filter_train(self, trains):
        timetable = DBtimetable()
        for item in self.timetable:
            if item["train"] in trains:
                timetable.append(item)
        self.timetable = timetable.timetable

    #---------------------------
    def filter_destination(self, destination):
        timetable = DBtimetable()
        for item in self.timetable:
            if destination in item["path"]:
                timetable.append(item)
        self.timetable = timetable.timetable        

    #---------------------------
    def print(self, path_filter=None):
        txt = ""
        item = {}         
        for item in self.timetable:
            time = item["date"]
            if item.get("scheduled_date"):    
                time = "{} [{}]".format(time, item["scheduled_date"])
            platform = item.get("platform")
            if item.get("scheduled_platform"):
                platform = "{} [{}]".format(platform, item["scheduled_platform"])         
            from_to = item.get("from_to")
            if item.get("scheduled_from_to"):
                from_to = "{} [{}]".format(from_to, item["scheduled_from_to"])
            status = ""
            if item.get("status") and len(item.get("status"))>0:
                status = "- " + item.get("status")     
            if item.get("message"):
                status += " ! " + item.get("message") + " !"    
            path_str = ""
            if path_filter:
                path_str = "- "
                path = item.get("path")
                if "|" in path:
                    path = item.get("path").split("|")
                for i in path:
                    if path_filter in i:
                        if len(path_str)>2:
                            path_str += ", "
                        path_str += i        
            txt += "{}: {} {}, Gleis {} {} {}\n".format(time, item["train"], from_to, platform, status, path_str)
        return txt

#===============================================================
# Cached data representing a train stop (a train stopping by a a station)
class DBtrain_stop:
    #---------------------------
    def __init__(self):
        self.base = {}
        self.arrival = {}
        self.departure = {}
        self.messages = []
   
    #---------------------------
    def get_arrival(self):
        if self.arrival.get("time") or self.arrival.get("changed_time"):
            item = {} 
            if self.arrival["line"]:
                if self.arrival["line"][0].isdigit():
                    item["train"] = self.base["category"] + " " + self.arrival["line"]
                else:
                    item["train"] = self.arrival["line"]
            else:       
                item["train"] = self.base["category"] + " " + self.base["train_no"]
            item["path"] = self.arrival["path"]
            item["date"] = self.arrival["changed_time"] if self.arrival["changed_time"] else self.arrival["time"]
            item["from_to"] = self.arrival["changed_from"] if self.arrival["changed_from"] else self.arrival["from"]
            item["platform"] = self.arrival["changed_platform"] if self.arrival["changed_platform"] else self.arrival["platform"]
            if self.arrival.get("change_status")=='c':
                item["status"] = "CANCELLED"
            elif self.arrival.get("change_status")=='p':    
                item["status"] = "PLANNED"
            elif self.arrival.get("change_status")=='a':    
                item["status"] = "ADDED"
            else:
                item["status"] = "" 
            if self.arrival["changed_time"]:
                item["date"] = self.arrival["changed_time"] 
                item["scheduled_date"] = self.arrival["time"]
            if self.arrival["changed_from"]:
                item["from_to"] = self.arrival["changed_from"] 
                item["scheduled_from_to"] = self.arrival["from"]
            if self.arrival["changed_platform"]:  
                item["platform"] = self.arrival["changed_platform"] 
                item["scheduled_platform"] = self.arrival["platform"]
            max_prio = 99
            for msg in self.messages: # choose message with highest prio
                prio = int(msg.get("priority",99))
                if prio < max_prio:
                    item["message"] = msg.get("category")
            return item

    #---------------------------
    def get_departure(self):
        if self.departure.get("time") or self.departure.get("changed_time"):
            item = {} 
            item["train_id"] = self.base["train_id"]
            if self.departure["line"]:
                if self.departure["line"][0].isdigit():
                    item["train"] = self.base["category"] + " " + self.departure["line"]
                else:
                    item["train"] = self.departure["line"]
            else:       
                item["train"] = self.base["category"] + " " + self.base["train_no"]
            item["path"] = self.departure["path"]
            item["date"] = self.departure["time"]
            item["from_to"] = self.departure["to"]
            item["platform"] = self.departure["platform"]
            if self.arrival.get("change_status")=='c':
                item["status"] = "CANCELLED"
            elif self.arrival.get("change_status")=='p':    
                item["status"] = "PLANNED"
            elif self.arrival.get("change_status")=='a':    
                item["status"] = "ADDED"
            else:
                item["status"] = ""    
            if self.departure.get("changed_time"):
                item["date"] = self.departure.get("changed_time") 
                item["scheduled_date"] = self.departure.get("time")
            if self.departure.get("changed_to"):
                item["from_to"] = self.departure.get("changed_to") 
                item["scheduled_from_to"] = self.departure.get("to")
            if self.departure.get("changed_platform"):  
                item["platform"] = self.departure.get("changed_platform") 
                item["scheduled_platform"] = self.departure.get("platform")
            max_prio = 99
            for msg in self.messages: # choose message with highest prio
                if msg.get("priority",99):
                    prio = int(msg.get("priority",99))
                else:
                    prio = 99    
                if prio < max_prio:
                    item["message"] = msg.get("category")
            return item 

    #---------------------------
    def print(self):
        txt = "  Base:\n"
        for p, v in self.base.items():
            if v:
                txt += "    - {:20}: {}\n".format(p, v)
        txt += "  Arrival:\n"
        for p, v in self.arrival.items():
            if v:
                txt += "    - {:20}: {}\n".format(p, v)
        txt += "  Departure:\n"
        for p, v in self.departure.items():
            if v:
                txt += "    - {:20}: {}\n".format(p, v)
        txt += "  Messages:\n"
        for i in self.messages:
            for p, v in i.items():
                if v:
                    txt += "    - {:20}: {}\n".format(p, v)
        return txt
    
