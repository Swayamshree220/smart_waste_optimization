import numpy as np
import random

class GeneticAlgorithm:
    def __init__(self, distance_func, n_bins, pop_size=50, generations=100):
        self.distance_func = distance_func
        self.n_bins = n_bins
        self.pop_size = pop_size
        self.generations = generations

    def optimize(self):
        # Create initial random population of routes
        population = [random.sample(range(self.n_bins), self.n_bins) for _ in range(self.pop_size)]
        history = []
        best_route = population[0]
        best_dist = self.distance_func(best_route)

        for _ in range(self.generations):
            # Sort population by distance (shorter is better)
            population = sorted(population, key=lambda x: self.distance_func(x))
            current_best_dist = self.distance_func(population[0])
            
            if current_best_dist < best_dist:
                best_dist = current_best_dist
                best_route = population[0]
            
            history.append(best_dist)
            
            # Simple Crossover/Mutation to evolve
            new_pop = population[:10] # Elitism
            while len(new_pop) < self.pop_size:
                parent = random.choice(population[:20])
                child = parent[:]
                # Mutation: Swap two bins
                idx1, idx2 = random.sample(range(self.n_bins), 2)
                child[idx1], child[idx2] = child[idx2], child[idx1]
                new_pop.append(child)
            population = new_pop

        return best_route, best_dist, history