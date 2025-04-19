import numpy as np
from backtester import Backtester
from strategy import Strategy


class Individual:
    def __init__(self, n_genes, gene_ranges):
        # Initialize genes within specified ranges
        self.genes = [
            np.random.randint(gene_ranges[x][0], gene_ranges[x][1])
            for x in range(n_genes)
        ]
        self.initial_balance = 1000  # Store initial balance per individual
        self.backtester = Backtester(initial_balance=self.initial_balance, leverage=1, inv_percent=100, tsl=True)


class Population:
    def __init__(self, generation_size, n_genes, gene_ranges, n_best, mutation_rate, strategy_blueprint):
        self.population = [
            Individual(n_genes, gene_ranges)
            for _ in range(generation_size)
        ]
        self.n_genes = n_genes
        self.n_best = n_best
        self.generation_size = generation_size
        self.mutation_rate = mutation_rate
        self.gene_ranges = gene_ranges
        self.strategy_blueprint = strategy_blueprint

    def evaluate_fitness(self, individual, df):
        # Reset balance before each evaluation
        individual.backtester.balance = individual.initial_balance
        individual.backtester.reset_results()

        genes = individual.genes
        plan = self.strategy_blueprint(
            data_df=df,
            rsi_over_bought=genes[0],
            rsi_over_sold=genes[1],
            bb_len=genes[2],
            n_std=genes[3] / 10,
            rsi_len=genes[4],
            log_indicators=False
        )
        strategy = Strategy(strategy=plan)
        results = individual.backtester.backtesting(strategy=strategy, symbol='-', df=strategy.df)
        return results.get('fitness_function', 0)

    def selection(self, df):
        # Sort individuals based on fitness function
        fitness_values = [self.evaluate_fitness(individual, df) for individual in self.population]
        # Pair fitness values with individuals and sort by fitness
        sorted_population = [
            individual for _, individual in sorted(
                zip(fitness_values, self.population), key=lambda x: x[0], reverse=True
            )
        ]
        self.population = sorted_population # Update the population with the sorted one
        return self.population[:self.n_best]

    def crossover(self, df):
        selected = self.selection(df=df)
        new_population = selected[:self.n_best].copy() # Keep the best individuals

        for i in range(self.generation_size - self.n_best): # Create new individuals
            # Randomly select two parents from the best individuals
            parent_indices = np.random.choice(len(selected), size=2, replace=False)
            parent1, parent2 = selected[parent_indices[0]], selected[parent_indices[1]]

            # Randomly select crossover point
            point = np.random.randint(1, self.n_genes)

            # Perform crossover between parents
            child_genes = parent1.genes[:point] + parent2.genes[point:]
            child = Individual(self.n_genes, self.gene_ranges)
            child.genes = child_genes
            new_population.append(child)

        self.population = new_population

    def mutation(self):
        for individual in self.population:
            for j in range(self.n_genes):
                if np.random.random() <= self.mutation_rate:
                    # Mutate a gene
                    new_gen = np.random.randint(
                        self.gene_ranges[j][0], self.gene_ranges[j][1]
                    )
                    # Avoid assigning the same value as the current one
                    while new_gen == individual.genes[j]:
                        new_gen = np.random.randint(
                            self.gene_ranges[j][0], self.gene_ranges[j][1]
                        )
                    individual.genes[j] = new_gen