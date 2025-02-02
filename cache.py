
import socket
import sys
import time


class Cache(object):

    def __init__(self, host='39.106.126.216', port=2003, max_size=128):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.max_size = max_size
        self.counter_cache = {}
        self.timer_cache = {}
        self.percenter_cache = {}
        self.connect()

    def connect(self):
        self.sock.connect((self.host, self.port))

    def reconnect(self):
        try:
            self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect()
        except Exception as error:
            print(error)

    def write_graphite(self, msg):
        ip = '39.106.126.216'
        port = 2003
        try:
            self.graphite_sock.send(msg)
        except Exception:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(msg)
            self.graphite_sock = sock

    def incr(self, key, timestamp, value=1):
        if timestamp in self.counter_cache:
            if key in self.counter_cache[timestamp]:
                self.counter_cache[timestamp][key] += value
            else:
                self.counter_cache[timestamp][key] = value
        else:
            self.send('counter')
            self.counter_cache[timestamp] = {}
            self.counter_cache[timestamp][key] = value

    def create_timer(self, value, num=1):
        timer = {}
        timer['count'] = num
        timer['sum'] = value
        return timer

    def create_percenter(self, value):
        percenter = {}
        percenter['list'] = []
        percenter['list'].append(value)
        return percenter

    def timing(self, key, timestamp, value, num=1):
        if timestamp in self.timer_cache:
            if key in self.timer_cache[timestamp]:
                self.timer_cache[timestamp][key]['count'] += num
                self.timer_cache[timestamp][key]['sum'] += value
            else:
                new_timer = self.create_timer(value, num)
                self.timer_cache[timestamp][key] = {}
                self.timer_cache[timestamp][key] = new_timer
        else:
            if self.is_full('timer'):
                self.send('timer')
            new_timer = self.create_timer(value, num)
            self.timer_cache[timestamp] = {}
            self.timer_cache[timestamp][key] = {}
            self.timer_cache[timestamp][key] = new_timer

    def percentile(self, key, timestamp, value):
        if timestamp in self.percenter_cache:
            if key in self.percenter_cache[timestamp]:
                self.percenter_cache[timestamp][key]['list'].append(value)
            else:
                new_percenter = self.create_percenter(value)
                self.percenter_cache[timestamp][key] = {}
                self.percenter_cache[timestamp][key] = new_percenter
        else:
            if self.is_full('percenter'):
                self.send('percenter')
            new_percenter = self.create_percenter(value)
            self.percenter_cache[timestamp] = {}
            self.percenter_cache[timestamp][key] = {}
            self.percenter_cache[timestamp][key] = new_percenter

    def is_full(self, category):
        if category == 'counter':
            if len(self.counter_cache) == self.max_size:
                return True
        elif category == 'timer':
            if len(self.timer_cache) == self.max_size:
                return True
        elif category == 'percenter':
            if len(self.percenter_cache) == self.max_size:
                return True
        return False

    def counter_format(self, timestamp, item):
        msg = ''
        keys = item.keys()
        for key in keys:
            value = item[key]
            line = key + ' ' + str(value) + ' ' + str(timestamp) + '\n'
            if msg:
                msg += line
            else:
                msg = line
        return msg

    def timer_format(self, timestamp, item):
        msg = ''
        keys = item.keys()
        for key in keys:
            count = item[key]['count']
            sum = item[key]['sum']
            value = float(sum) / float(count)
            line = key + '.mean ' + str(value) + ' ' + str(timestamp) + '\n'
            if msg:
                msg += line
            else:
                msg = line
        return msg

    def percenter_format(self, timestamp, item):
        msg = ''
        keys = item.keys()
        for key in keys:
            sub_list = item[key]['list']
            length = len(sub_list)
            sub_list.sort()

            line = ''
            percent50 = int(length * 0.5) - 1
            line += key + '.50% ' + str(sub_list[percent50]) + ' ' + str(timestamp) + '\n'
            percent70 = int(length * 0.7) - 1
            line += key + '.70% ' + str(sub_list[percent70]) + ' ' + str(timestamp) + '\n'
            percent90 = int(length * 0.9) - 1
            line += key + '.90% ' + str(sub_list[percent90]) + ' ' + str(timestamp) + '\n'
            percent99 = int(length * 0.99) - 1
            line += key + '.99% ' + str(sub_list[percent99]) + ' ' + str(timestamp) + '\n'

            percent_min = 0
            line += key + '.min ' + str(sub_list[percent_min]) + ' ' + str(timestamp) + '\n'
            percent_max = length - 1
            line += key + '.max ' + str(sub_list[percent_max]) + ' ' + str(timestamp) + '\n'
            mean = sum(sub_list) / length
            line += key + '.mean ' + str(mean) + ' ' + str(timestamp) + '\n'

            msg += line
        return msg

    def send(self, category):
        cache = {}
        if category == 'counter':
            cache = self.counter_cache
        elif category == 'timer':
            cache = self.timer_cache
        elif category == 'percenter':
            cache = self.percenter_cache
        cache_list = sorted(cache)
        for key in cache_list:
            if len(cache) <= (self.max_size / 2):
                break
            item = cache[key]
            msg = ''
            if category == 'counter':
                msg = self.counter_format(key, item)
            elif category == 'timer':
                msg = self.timer_format(key, item)
            elif category == 'percenter':
                msg = self.percenter_format(key, item)
            msg = msg.encode(encoding="utf-8")
            if category == 'percenter' and msg != '':
                self.write_graphite(msg)
            else:
                try:
                    self.sock.send(msg)
                except Exception as error:
                    print(error)
                    self.reconnect()


class vCache(Cache):

    def __init__(self, host='39.106.126.216', port=2003, max_size=60):
        Cache.__init__(self, host, port, max_size)

    def timer_format(self, timestamp, item):
        msg = ''
        keys = item.keys()
        for key in keys:
            count = item[key]['count']
            item_sum = item[key]['sum']
            line = key + ' ' + str(count) + ' ' + str(item_sum) + ' ' + str(timestamp) + '\n'
            if msg:
                msg += line
            else:
                msg = line
        return msg
