from mon.ivs import BANDS, DEFENDER_IV, band_of


def test_the_bands_cover_every_iv_with_no_gap():
    assert sorted(b for b, _ in BANDS) == ["20+", "sub-10", "sub-20"]
    assert {band_of(iv) for iv in range(32)} == {"sub-10", "sub-20", "20+"}


def test_each_band_has_one_representative_value():
    assert dict(BANDS) == {"sub-10": 5, "sub-20": 15, "20+": 27}


def test_the_defender_is_always_perfect():
    assert DEFENDER_IV == 31
