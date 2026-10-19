"""The shelf-life simulation (eval/shelf_life_sim.py) runs on the real engines and is reproducible."""

import importlib.util
import json

from app.config import REPO_ROOT


def _sim():
    spec = importlib.util.spec_from_file_location("shelf_life_sim", REPO_ROOT / "eval" / "shelf_life_sim.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_small_run_is_reproducible_and_shelf_life_never_finances_more(tmp_path, monkeypatch):
    sim = _sim()
    outs = []
    for i in range(2):
        out = tmp_path / f"run{i}"
        monkeypatch.setattr("sys.argv", ["sim", "--n", "6", "--seed", "11", "--out", str(out)])
        sim.main()
        outs.append(json.loads((out.with_suffix(".json")).read_text()))
    assert outs[0] == outs[1]
    s = outs[0]["summary"]
    assert outs[0]["golden_check"] == [19000, 10800, 8200]
    assert s["financed"]["slc"]["median"] <= s["financed"]["blind"]["median"]
    assert s["financed_unsold"]["slc"]["median"] <= s["financed_unsold"]["blind"]["median"]
