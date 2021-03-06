from collections import namedtuple

import numpy as np
import pandas as pd
import pytest

from semeio.jobs.correlated_observations_scaling.scaled_matrix import DataMatrix


def test_get_scaling_factor():
    new_event = namedtuple("named_dict", ["keys", "threshold"])
    event = new_event(["one_random_key"], 0.95)
    np.random.seed(123)
    input_matrix = np.random.rand(10, 10)

    matrix = DataMatrix(pd.DataFrame(data=input_matrix))
    assert matrix.get_scaling_factor(event) == np.sqrt(10 / 6.0)


@pytest.mark.parametrize(
    "threshold,expected_result", [(0.0, 1), (0.83, 4), (0.90, 5), (0.95, 6), (0.99, 7)]
)
def test_get_nr_primary_components(threshold, expected_result):
    np.random.seed(123)
    input_matrix = np.random.rand(10, 10)
    components, _ = DataMatrix._get_nr_primary_components(input_matrix, threshold)
    assert components == expected_result


def test_std_normalization():
    input_matrix = pd.DataFrame(np.ones((3, 3)))
    input_matrix.loc["OBS"] = np.ones(3)
    input_matrix.loc["STD"] = np.ones(3) * 0.1
    expected_matrix = [[10.0, 10.0, 10.0], [10.0, 10.0, 10.0], [10.0, 10.0, 10.0]]
    matrix = DataMatrix(pd.concat({"A_KEY": input_matrix}, axis=1))
    result = matrix.std_normalization(["A_KEY"])
    assert (result.loc[[0, 1, 2]].values == expected_matrix).all()
