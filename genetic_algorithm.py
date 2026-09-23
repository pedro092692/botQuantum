import numpy as np


class Individual:
    def __init__(self, n_genes, gene_ranges, genes=None):
        if genes is None:
            genes = [np.random.randint(gene_ranges[x][0], gene_ranges[x][1]) for x in range(n_genes)]
        # each individual owns its genes and its results (never shared between individuals)
        self.genes = list(genes)
        self.fitness = float('-inf')
        self.results = None


class Population:
    def __init__(self, generation_size, n_genes, gene_ranges, n_best, mutation_rate, n_elite=1):
        self.population = [Individual(n_genes, gene_ranges) for _ in range(generation_size)]
        self.n_genes = n_genes
        self.n_best = n_best
        self.n_elite = n_elite
        self.generation_size = generation_size
        self.mutation_rate = mutation_rate
        self.gene_ranges = gene_ranges

    def evaluate(self, fitness_fn):
        """fitness_fn(genes) -> results dict of Backtester (with 'fitness_function')."""
        for individual in self.population:
            individual.results = fitness_fn(individual.genes)
            individual.fitness = individual.results['fitness_function']
        self.population.sort(key=lambda individual: individual.fitness, reverse=True)

    def best(self):
        return max(self.population, key=lambda individual: individual.fitness)

    def selection(self):
        return sorted(self.population, key=lambda individual: individual.fitness, reverse=True)[0:self.n_best]

    def crossover(self):
        selected = self.selection()
        # the best ones pass untouched to the next generation (elitism)
        new_population = [Individual(self.n_genes, self.gene_ranges, genes=ind.genes)
                          for ind in selected[:self.n_elite]]
        while len(new_population) < self.generation_size:
            father_idx = np.random.choice(self.n_best, size=2, replace=False)
            father = [selected[i] for i in father_idx]
            point = np.random.randint(1, self.n_genes)
            # copies of the parents' genes, the parents are never modified
            genes = list(father[0].genes[:point]) + list(father[1].genes[point:])
            new_population.append(Individual(self.n_genes, self.gene_ranges, genes=genes))
        self.population = new_population

    def mutation(self):
        # the elite is not mutated
        for individual in self.population[self.n_elite:]:
            for j in range(self.n_genes):
                if np.random.random() <= self.mutation_rate:
                    low, high = self.gene_ranges[j]
                    if high - low <= 1:
                        continue
                    new_gen = np.random.randint(low, high)
                    while new_gen == individual.genes[j]:
                        new_gen = np.random.randint(low, high)
                    individual.genes[j] = new_gen
