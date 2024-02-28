import pytest
from amendmerge.utils import CountDifference

def test_CountDifference():

    s1 = 'This is a string'
    s2 = 'This is also a string'
    s3 = ''
    s4 = None

    qval = None

    assert CountDifference(qval=qval).distance(s1,s2) == 1
    assert CountDifference(qval=qval).distance(s2,s1) == -1
    assert CountDifference(qval=qval).distance(s1,s3) == -4
    assert CountDifference(qval=qval).distance(s3,s1) == 4
    with pytest.raises(AttributeError):
        CountDifference(qval=qval).distance(s4,s1)

    qval = 1

    assert CountDifference(qval=qval).distance(s1,s2) == len(s2) - len(s1)
    assert CountDifference(qval=qval).distance(s2,s1) == len(s1) - len(s2)
    assert CountDifference(qval=qval).distance(s1,s3) == -len(s1)
    assert CountDifference(qval=qval).distance(s3,s1) == len(s1)
    with pytest.raises(AttributeError):
        CountDifference(qval=qval).distance(s4,s1)
