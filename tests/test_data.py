"""Tests for the data-cleaning logic (no network — uses synthetic frames)."""

import pandas as pd
import pytest

from footpred.data import TeamIndex, encode_matches, normalize_teams


def test_normalize_teams_applies_former_name_map():
    df = pd.DataFrame({
        "home_team": ["Ireland", "Brazil"],
        "away_team": ["Spain", "Gold Coast"],
    })
    name_map = {"Ireland": "Northern Ireland", "Gold Coast": "Ghana"}
    out = normalize_teams(df, name_map)
    assert out.loc[0, "home_team"] == "Northern Ireland"
    assert out.loc[1, "away_team"] == "Ghana"
    assert out.loc[1, "home_team"] == "Brazil"  # unchanged


def test_team_index_is_bijective_and_sorted():
    df = pd.DataFrame({
        "home_team": ["Brazil", "Argentina"],
        "away_team": ["Chile", "Brazil"],
    })
    idx = TeamIndex.from_matches(df)
    assert idx.teams == sorted(idx.teams)
    assert idx.n_teams == 3
    for t in idx.teams:
        assert idx.teams[idx.to_id[t]] == t


def test_encode_matches_maps_ids_and_drops_unknown():
    df = pd.DataFrame({
        "home_team": ["Brazil", "Mars"],
        "away_team": ["Chile", "Chile"],
    })
    index = TeamIndex(teams=["Brazil", "Chile"],
                      to_id={"Brazil": 0, "Chile": 1})
    enc, _ = encode_matches(df, index)
    assert len(enc) == 1  # "Mars" row dropped
    assert enc.iloc[0]["home_id"] == 0
    assert enc.iloc[0]["away_id"] == 1
