import numpy as np
from backtester import Backtester


class Individual:
    def __init__(self, n_genes, gene_ranges, backtester: Backtester):
        self.genes = [np.random.randint(gene_ranges[x][0], gene_ranges[x][1]) for x in range(n_genes)]
        self.backtester = backtester


class Population:
    def __init__(self, generation_size, n_genes, gene_ranges, n_best, mutation_rate, backtester):
        self.population = [Individual(n_genes, gene_ranges, backtester) for _ in range(generation_size)]
        self.n_genes = n_genes
        self.n_best = n_best
        self.generation_size = generation_size
        self.mutation_rate = mutation_rate
        self.gene_ranges = gene_ranges

    def selection(self):
        return sorted(
            self.population,
            key=lambda individual: individual.backtester.results(
                symbol='-',
            )['fitness_function']
        )[0:self.n_best]

    def crossover(self):
        selected = self.selection()
        point = 0
        father = []
        for i in range(self.generation_size):
            father = np.random.choice(self.n_best, size=2, replace=False)
            father = [selected[i] for i in father]
            point = np.random.randint(0, self.n_genes)
            self.population[i].genes[:point] = father[0].genes[:point]
            self.population[i].genes[point:] = father[1].genes[point:]

    def mutation(self):
        for i in range(self.generation_size):
            point = 0
            for j in range(self.n_genes):
                point = np.random.randint(0, self.n_genes)
                if np.random.random() <= self.mutation_rate:
                    new_gen = np.random.randint(self.gene_ranges[point][0], self.gene_ranges[point][1])

                    while new_gen == self.population[i].genes[point]:
                        new_gen = np.random.randint(self.gene_ranges[point][0], self.gene_ranges[point][1])

                    self.population[i].genes[point] = new_gen

