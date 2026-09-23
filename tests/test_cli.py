import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import cli
from tests.test_lookahead import random_walk_df


def run_with_input(fn, answers):
    """Run fn answering input() with the given answers, returns what was printed."""
    out = io.StringIO()
    with patch('builtins.input', side_effect=answers), redirect_stdout(out):
        result = fn()
    return result, out.getvalue()


class InputHelpersTest(unittest.TestCase):

    def test_ask_uses_default_on_enter(self):
        value, _ = run_with_input(lambda: cli.ask('x', 'btc'), [''])
        self.assertEqual(value, 'btc')

    def test_ask_repeats_until_valid(self):
        validate = lambda v: None if v > 0 else 'positivo'
        value, printed = run_with_input(lambda: cli.ask('x', None, int, validate), ['abc', '-1', '5'])
        self.assertEqual(value, 5)
        self.assertIn('Valor invalido', printed)
        self.assertIn('positivo', printed)

    def test_ask_number_keeps_type_of_default(self):
        value, _ = run_with_input(lambda: cli.ask_number('x', 2.0), ['2,5'])
        self.assertEqual(value, 2.5)
        value, _ = run_with_input(lambda: cli.ask_number('x', 20), [''])
        self.assertIsInstance(value, int)

    def test_ask_choice_rejects_out_of_range(self):
        value, printed = run_with_input(lambda: cli.ask_choice('?', [('a', 'A'), ('b', 'B')]), ['3', '2'])
        self.assertEqual(value, 'b')
        self.assertIn('entre 1 y 2', printed)

    def test_ask_yes_no(self):
        self.assertTrue(run_with_input(lambda: cli.ask_yes_no('?'), ['s'])[0])
        self.assertFalse(run_with_input(lambda: cli.ask_yes_no('?', True), ['n'])[0])
        self.assertTrue(run_with_input(lambda: cli.ask_yes_no('?', True), [''])[0])


class BacktestFlowTest(unittest.TestCase):

    def test_backtest_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, 'MARKETS_DIR', tmp):
            random_walk_df().to_csv(os.path.join(tmp, 'TEST-USDT-1m.csv'), index=False)
            # csv 1, strategy 1, Enter for every parameter, don't save, don't plot
            answers = ['1', '1'] + [''] * 12 + ['n', 'n']
            _, printed = run_with_input(cli.run_backtest, answers)
        self.assertIn('RESULTADOS', printed)
        self.assertIn('Ganancia neta', printed)

    def test_backtest_without_data(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, 'MARKETS_DIR', tmp):
            _, printed = run_with_input(cli.run_backtest, [])
        self.assertIn('No hay datos descargados', printed)


if __name__ == '__main__':
    unittest.main()
