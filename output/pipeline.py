import networkx as nx
import glob
import random
import numpy as np
import sys
from proj_utils import score, parse_input
from solver1 import Solver
from multiprocessing import Pool

def get_greedy_solver(fl):
    G, num_buses, size_bus, constraints = parse_input(fl)
    G.remove_edges_from(G.selfloop_edges())
    s1 = Solver(G, num_buses, size_bus, constraints, fl)
    s1.better_greedy_init()
    return s1

def get_bogo_solver(fl):
    G, num_buses, size_bus, constraints = parse_input(fl)
    G.remove_edges_from(G.selfloop_edges())
    s1 = Solver(G, num_buses, size_bus, constraints, fl)
    s1.bogo_init()
    return s1

def get_cache_solver(fl):
    G, num_buses, size_bus, constraints = parse_input(fl)
    G.remove_edges_from(G.selfloop_edges())
    s1 = Solver(G, num_buses, size_bus, constraints, fl)
    s1.cache_init(fl.replace('input','output') + '.out')
    return s1

def task(fl, gs, swap_strat, swap_count):
    file_score = -1
    try:
        meta = open(fl.replace('input','meta'), 'r')
        file_score = float(meta.readline())
        meta.close()
    except:
        print('Error opening meta file for ' + fl)
        meta = open(fl.replace('input','meta'), 'w')
        meta.write('0')
        meta.close()
    
    if file_score > 0.9999999:
        return
    
    cached_score = file_score
    print(fl, cached_score)
    
    buses = None

    solver_score, _ = gs.score_self()
    if solver_score > file_score:
        buses = gs.buses
        file_score = solver_score


    solver_score = swap_strat(swap_count, cached_score)
    if solver_score > file_score:
        buses = gs.buses
        file_score = solver_score
        print(fl, 'cached score', cached_score, 'new score', file_score)
    else:
        print(fl, cached_score, 'no improvement')


    if buses:
        output_file = open(fl.replace('input', 'output') + '.out', 'w')
        for b in buses:
            output_file.write(str(b) + '\n')
    meta = open(fl.replace('input','meta'), 'w')
    meta.write('%.30f' % file_score)

def greedy_task(fl, steps):
    gs = get_greedy_solver(fl)
    task(fl, gs, gs.greedy_swap, steps)

def bogo_task(fl, steps):
    gs = get_bogo_solver(fl)
    task(fl, gs, gs.greedy_swap, steps)

def bogo_annealing_task(fl, steps):
    gs = get_bogo_solver(fl)
    task(fl, gs, gs.annealing_swap, steps)

def bogo_annealing2_task(fl, steps):
    gs = get_bogo_solver(fl)
    task(fl, gs, gs.annealing_swap2, steps)

def cache_task(fl, steps):
    gs = get_cache_solver(fl)
    task(fl, gs, gs.annealing_swap, steps)

def cache2_task(fl, steps):
    gs = get_cache_solver(fl)
    task(fl, gs, gs.annealing_swap2, steps)

def bogo_init_task(fl, steps):
    gs = get_bogo_solver(fl)
    task(fl, gs, gs.dummy_swap, steps)

size = sys.argv[1]
num_iter = int(sys.argv[2])
num = '*'

files = glob.glob("input/%s/%s" % (size, num))

tasks = []
for fl in files:
    tasks.append((fl,num_iter))

random.shuffle(tasks)
num_threads = 16

tasks = tasks[:100]

for _ in range(100):
    pool = Pool(num_threads)
    results = [pool.apply_async(cache2_task, (t)) for t in tasks]
    output = [p.get() for p in results]
    pool.close()
    pool.join()
