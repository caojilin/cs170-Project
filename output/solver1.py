import networkx as nx
import glob
import random
import numpy as np
import copy
import sys
import time
from proj_utils import score, parse_input, get_assignment

def sublist(sub, l):
    for e in sub:
        if e not in l:
            return False
    return True

def intersect(a, b):
    return list(set(a) & set(b))

def deep_copy(l):
    r = []
    for x in l:
        r += [copy.copy(x)]
    return r
class Solver(object):
    def __init__(self, G, num_buses, size_bus, constraints, fl):
        self.G = G
        self.num_buses = num_buses
        self.size_bus = size_bus
        self.constraints = constraints
        self.fl = fl


    def bus_score(self, bus):
        rowdy = set([])
        for c in self.constraints:
            if sublist(c, bus):
                rowdy.update(c)
        s = 0
        for n in bus:
            if n in rowdy:
                continue
            for b in self.G[n]:
                if b in bus and b not in rowdy:
                    s += 1
        return s/2

    def total_score(self, buses):
        scores = [self.bus_score(b) for b in buses]
        return sum(scores), scores

    def score_naive(self, bus):
        s = 0
        for n in bus:
            for b in self.G[n]:
                if b in bus and self.G.has_edge(n,b):
                    s += 1
        return int(s/2)


    def incomplete_greedy_init(self):
        # Greedy best bus for this node
        def u(node):
            curr_bus = [node]
            for neighbor in self.G[node]:
                violated = False
                for c in self.constraints:
                    if sublist(c, curr_bus + [neighbor]):
                        violated = True
                if not violated:
                    curr_bus += [neighbor]
                if len(curr_bus) >= self.size_bus:
                    break
            return curr_bus

        def close(bus):
            l = set([])
            for c in self.constraints:
                i = intersect(bus,c)
                if sublist(i, c):
                    diff = set(c).difference(set(i))
                    if len(diff) == 1:
                        l.update(diff)
            return l

        def argmax(d, f):
            v = -1
            r = None
            for key in d:
                cv = f(d[key])
                if cv > v and d[key]:
                    v = cv
                    r = d[key]
            return r,v

        def remove(d, l):
            if not l:
                return
            l = l[:]
            for e in l:
                for b in d:
                    if e in d[b]:
                        d[b].remove(e)


        ib = {}
        for node in self.G.nodes:
            ib[node] = u(node)
        buses = []
        close_rowdy = []
        s = []
        while len(buses) < self.num_buses:
            curr_bus, v = argmax(ib, self.score_naive)
            if not curr_bus:
                break
            buses.append(curr_bus[:])
            s.append(self.score_naive(curr_bus))
            close_rowdy.append(close(curr_bus))
            remove(ib, curr_bus)
        # Now we have a greedy, incomplete initialization for the buses
        self.greedy_buses = buses
        self.close_rowdy = close_rowdy
        self.ib = ib

    def greedy_init(self):
        self.incomplete_greedy_init()
        buses = deep_copy(self.greedy_buses)
        close_rowdy = deep_copy(self.close_rowdy)
        ib = copy.copy(self.ib)
        unused = set([])
        unused2 = set([])
        for v in ib:
            unused.update(ib[v])
        for v in unused:
            added = False
            for j in range(len(buses)):
                if v not in close_rowdy[j] and len(buses[j]) < self.size_bus:
                    buses[j] += [v]
                    added = True
                    break
            if not added:
                unused2.add(v)
        num_empty = self.num_buses - len(buses)
        while len(unused2) < num_empty:
            b = random.choice(buses)
            if len(b) == 1:
                continue
            n = random.choice(b)
            b.remove(n)
            unused2.add(n)
        count = 0
        for v in unused2:
            if count < num_empty:
                count += 1
                buses += [[v]]
            else:
                while True:
                    i = random.randint(0, self.num_buses - 1)
                    if len(buses[i]) < self.size_bus:
                        buses[i] += [v]
                        break

        s, scores = self.total_score(buses)
        self.buses = buses
        self.scores = scores

    def better_greedy_init(self):
        used = set([])
        buses = []
        scores = []
        while len(buses) < self.num_buses:
            n = random.choice(self.G.nodes)
            if not n in used:
                buses += [[n]]
                scores += [0]
                used.add(n)
        for n in self.G.nodes:
            max_update_score = -100000000000
            index = -1
            for i in range(len(buses)):
                if len(buses[i]) >= self.size_bus:
                    continue
                update_score = self.bus_score(buses[i] + [n]) - scores[i]
                if update_score > max_update_score:
                    max_update_score = update_score
                    index = i
            scores[index] = scores[index] + max_update_score
            buses[index] += n
        return buses, scores


    def bogo_init(self):
        buses = [[] for _ in range(self.num_buses)]
        p = np.random.permutation(self.num_buses * self.size_bus)
        i = 0
        for node in self.G.nodes:
            buses[p[i] // self.size_bus].append(node)
            i += 1
        self.buses = buses
        _, self.scores = self.total_score(buses)

    def cache_init(self, output_file):
        self.buses = get_assignment(output_file)
        _, self.scores = self.total_score(self.buses)

    def swap_outcome(self):
        if len(self.buses) == 1:
            return 0,0, None, None, -100, -100
        a,b = random.sample(range(self.num_buses), 2)
        node_a, node_b = None, None
        bus_a = self.buses[a][:]
        bus_b = self.buses[b][:]
        if len(bus_a) < self.size_bus:
            bus_a.append(None)
        if len(bus_b) < self.size_bus:
            bus_b.append(None)

        node_a = random.choice(bus_a)
        node_b = random.choice(bus_b)

        bus_a.append(node_b)
        bus_b.append(node_a)
        
        bus_a.remove(node_a)
        bus_b.remove(node_b)

        bus_a = [n for n in bus_a if n]
        bus_b = [n for n in bus_b if n]

        if not bus_a or not bus_b:
            return 0, 0, None, None, -100, -100
            
        
        score_a = self.bus_score(bus_a)
        score_b = self.bus_score(bus_b)
        return a,b, bus_a, bus_b, score_a, score_b

    def actual_swap(self):
        a = None
        b = None
        bus_a = None
        bus_b = None
        node_a = None
        node_b = None
        l = random.shuffle(deep_copy(self.constraints))
        while l:
            c = l.pop()
            found = False
            for i in range(len(self.buses)):
                if sublist(c,self.buses[i]):
                    bus_a = self.buses[i][:]
                    a = i
                    found = True
                    break
            if found:
                break
        if bus_a:
            node_a = random.choice(bus_a)
            b = random.choice(range(self.num_buses - 1))
            if b >= a:
                b += 1
            bus_b = self.buses[b][:]

            while bus_b == bus_a:
                bus_b = random.choice(self.buses)
            bus_b = bus_b[:]
            if len(bus_b) < self.size_bus:
                bus_b.append(None)
            node_b = random.choice(bus_b)
            bus_b = [n for n in bus_b if n]
            if not bus_a or not bus_b:
                return 0, 0, None, None, -100, -100
            score_a = self.bus_score(bus_a)
            score_b = self.bus_score(bus_b)
            return a,b, bus_a, bus_b, score_a, score_b
        else:
            return self.swap_outcome()
        


    def shuffle(self):
        if len(self.buses) == 1:
            return
        for i in range(nx.number_of_nodes(self.G)//3):
            a,b = random.sample(range(self.num_buses), 2)
            node_a, node_b = None, None
            bus_a = self.buses[a][:]
            bus_b = self.buses[b][:]
            if len(bus_a) < self.size_bus:
                bus_a.append(None)
            if len(bus_b) < self.size_bus:
                bus_b.append(None)

            node_a = random.choice(bus_a)
            node_b = random.choice(bus_b)

            if not node_a and len(bus_b) == 1:
                continue
            if not node_b and len(bus_a) == 1:
                continue

            bus_a.append(node_b)
            bus_b.append(node_a)
            
            bus_a.remove(node_a)
            bus_b.remove(node_b)

            bus_a = [n for n in bus_a if n]
            bus_b = [n for n in bus_b if n]



    def greedy_swap(self, count):
        solver_score = -1
        for _ in range(count):
            a, b, bus_a, bus_b, score_a, score_b = self.swap_outcome()
            if score_a == -100:
                continue
            if self.scores[a] + self.scores[b] <= score_a + score_b:
                self.buses[a] = bus_a
                self.buses[b] = bus_b
                self.scores[a] = score_a
                self.scores[b] = score_b

        curr_score, _ = self.score_self()
        if curr_score > solver_score:
            solver_score = curr_score

        return solver_score

    def print_to_file(self, solver_score):
        meta = open(self.fl.replace('input','meta'), 'w')
        meta.write('%.30f' % solver_score)
        output_file = open(self.fl.replace('input', 'output') + '.out', 'w')
        for b in self.buses:
            output_file.write(str(b) + '\n')
        print('PRINTED TO FILE')


    def annealing_swap(self, count, cached_score):
        solver_score = cached_score
        stale_steps = 0
        steps_mod = 70000
        for step in range(count):
            a, b, bus_a, bus_b, score_a, score_b = self.swap_outcome()
            if score_a == -100:
                continue
            accept = False
            if self.scores[a] + self.scores[b] <= score_a + score_b:
                stale_steps = 0
                accept = True
            else:
                p = (1-(step/count))**(2.5)
                if np.random.uniform() < p:
                    accept = True
                else:
                    stale_steps += 1
            if accept:
                self.buses[a] = bus_a
                self.buses[b] = bus_b
                self.scores[a] = score_a
                self.scores[b] = score_b

            elif stale_steps >= 500:
                self.shuffle()
                stale_steps = 0
            if step % steps_mod == 0:
                curr_score, _ = self.score_self()
                if curr_score > solver_score:
                    print(self.fl, solver_score, curr_score)
                    solver_score = curr_score
                    self.print_to_file(solver_score)

        curr_score, _ = self.score_self()
        if curr_score > solver_score:
            solver_score = curr_score

        return solver_score

    def annealing_swap2(self, count, cached_score):
        solver_score = cached_score
        stale_steps = 0
        steps_mod = 70000
        for step in range(count):
            a, b, bus_a, bus_b, score_a, score_b = None, None, None, None, None, None
            if np.random.uniform() < 0.001:
                a, b, bus_a, bus_b, score_a, score_b = self.actual_swap()
            else:    
                a, b, bus_a, bus_b, score_a, score_b = self.swap_outcome()
            if score_a == -100:
                continue
            accept = False
            if self.scores[a] + self.scores[b] <= score_a + score_b:
                stale_steps = 0
                accept = True
            else:
                p = (1-(step/count))**(2.5)
                if np.random.uniform() < p:
                    accept = True
                else:
                    stale_steps += 1
            if accept:
                self.buses[a] = bus_a
                self.buses[b] = bus_b
                self.scores[a] = score_a
                self.scores[b] = score_b

            elif stale_steps >= count / 100:
                if np.random.uniform() < 0.25:
                    self.shuffle()
                else:
                    self.actual_swap()
                stale_steps = 0
            if step % steps_mod == 0:
                curr_score, _ = self.score_self()
                if curr_score > solver_score:
                    print(self.fl, solver_score, curr_score)
                    solver_score = curr_score
                    self.print_to_file(solver_score)

        curr_score, _ = self.score_self()
        if curr_score > solver_score:
            solver_score = curr_score

        return solver_score

    def dummy_swap(self, count, cached_score):
        curr_score, _ = self.score_self()
        solver_score = cached_score
        if curr_score > solver_score:
            solver_score = curr_score

        return solver_score


    def score_self(self):
        return score(self.G.copy(), self.num_buses, self.size_bus,
                self.constraints[:], self.buses)
