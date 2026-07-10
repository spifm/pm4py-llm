import json

import pytest

from source.core.dfg.dfg_frequency import (
    frequency_threshold_for_ratio,
    get_min_transition_frequency,
)


def _keep(freqs, threshold):
    return [f for f in freqs if f > threshold]


def test_unique_boundary_keeps_expected_count():
    freqs = [10, 8, 6, 4, 2]
    # ratio 40% -> target 2 -> boundary_freq = 8 -> threshold 7
    assert frequency_threshold_for_ratio(freqs, 40) == 7
    assert _keep(freqs, 7) == [10, 8]


def test_ties_round_up_keep_whole_tier():
    freqs = [10, 5, 5, 5, 2]
    # ratio 40% -> target 2 -> boundary_freq = 5 -> threshold 4 -> keeps whole tier of 5s
    threshold = frequency_threshold_for_ratio(freqs, 40)
    assert threshold == 4
    assert _keep(freqs, threshold) == [10, 5, 5, 5]


def test_full_ratio_keeps_all():
    freqs = [9, 7, 3, 1]
    threshold = frequency_threshold_for_ratio(freqs, 100)
    assert _keep(freqs, threshold) == freqs


def test_small_ratio_rounds_up_to_at_least_one():
    freqs = [9, 7, 3, 1]
    # ratio 1% -> ceil(4*0.01)=1 -> boundary_freq=9 -> threshold 8
    assert frequency_threshold_for_ratio(freqs, 1) == 8
    assert _keep(freqs, 8) == [9]


@pytest.mark.parametrize("ratio", [0, -5, 100.1, 150])
def test_invalid_ratio_raises(ratio):
    with pytest.raises(ValueError):
        frequency_threshold_for_ratio([1, 2, 3], ratio)


def test_empty_freqs_raises():
    with pytest.raises(ValueError):
        frequency_threshold_for_ratio([], 20)


def test_get_min_transition_frequency(tmp_path):
    dfg = {
        "start_activities": [{"activity": "A", "freq": 5}],
        "end_activities": [{"activity": "C", "freq": 2}],
        "transitions": [
            {"src": "A", "tgt": "B", "freq": 5},
            {"src": "B", "tgt": "C", "freq": 2},
            {"src": "A", "tgt": "C", "freq": 8},
        ],
    }
    dfg_path = tmp_path / "dfg.json"
    dfg_path.write_text(json.dumps(dfg), encoding="utf-8")

    assert get_min_transition_frequency(str(dfg_path)) == 2


def test_get_min_transition_frequency_no_transitions(tmp_path):
    dfg_path = tmp_path / "dfg.json"
    dfg_path.write_text(json.dumps({"transitions": []}), encoding="utf-8")

    assert get_min_transition_frequency(str(dfg_path)) is None

