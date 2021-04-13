import pytest
from masstable import Table


def test_runs():
    assert Table("AME2003")


def test_not_in():
    expected = 389
    ame2003 = Table("AME2003")
    ame1995 = Table("AME1995")
    Table("AME2003").intersection(Table("AME1995"))
    assert ame2003.not_in(ame1995)[8:, 8:].count == expected


def test_select():
    A_equal_265 = lambda Z, N: Z + N == 265
    result = Table("AME2003").select(A_equal_265)
    assert result.count == 1


def test_s1p():
    result = Table("AME2003").s1p[2, 2].values[0]
    expected = 19.81
    assert result == pytest.approx(expected, 0.01)


def test_list_indexing():
    magic_nuclei = [(20, 28), (50, 50), (50, 82), (82, 126)]
    result = Table("AME2012").binding_energy[magic_nuclei]
    assert len(result) == 4

def test_condition_filtering():
    A_equal_265 = lambda Z, N: Z + N == 265
    result = Table("AME2003")[A_equal_265]
    assert result.count == 1
    
