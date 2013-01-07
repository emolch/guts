
import unittest
import calendar
import math
import re
import sys

sys.path[0:0] = [ '../src' ]

from guts import *

class SamplePat(StringPattern):
    pattern = r'[a-z]{3}'

class SampleChoice(StringChoice):
    choices = [ 'a', 'bcd', 'efg' ]

basic_types = (Bool, Int, Float, String, Complex, Timestamp,
        SamplePat, SampleChoice)

def tstamp(*args):
    return float(calendar.timegm(args))

samples = {}
samples[Bool] = [ True, False ]
samples[Int] = [ 2**n for n in [1,30] ] #,31,65] ] 
samples[Float] = [ 0., 1., math.pi, float('inf'), float('-inf'), float('nan') ]
samples[String] = [ '', 'test', 'abc def', '<', '\n', '"', '\'', 
        ''.join(chr(x) for x in range(32,128)) ] # chr(0) and other special chars don't work with xml...
samples[Complex] = [ 1.0+5J, 0.0J, complex('inf'), complex(math.pi,1.0) ]
samples[Timestamp] = [ 0.0, 
        tstamp(2030,1,1,0,0,0), 
        tstamp(1960,1,1,0,0,0),
        tstamp(2010,10,10,10,10,10) + 0.000001]

samples[SamplePat] = [ 'aaa', 'zzz' ]
samples[SampleChoice] = [ 'a', 'bcd', 'efg' ]

regularize = {}
regularize[Bool] = [ (1, True), (0, False), ('0', False), ('False', False) ]
regularize[Int] = [ ('1', 1), (1.0, 1), (1.1, 1) ]
regularize[Float] = [ ('1.0', 1.0), (1, 1.0), ('inf', float('inf')) ]
regularize[String] = [ (1, '1') ]
regularize[Timestamp] = [ 
        ('2010-01-01 10:20:01', tstamp(2010,1,1,10,20,1)),
        ('2010-01-01T10:20:01', tstamp(2010,1,1,10,20,1)),
        ('2010-01-01T10:20:01.11Z', tstamp(2010,1,1,10,20,1)+0.11),
        ('2030-12-12 00:00:10.11111', tstamp(2030,12,12,0,0,10)+0.11111)
]

class TestGuts(unittest.TestCase):

    def assertEqualNanAware(self, a, b):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return 
        
        self.assertEqual(a,b)

    def testChoice(self):
        class X(Object):
            m = StringChoice.T(['a', 'b'])

        x = X(m='a')
        x.validate()
        x = X(m='c')
        with self.assertRaises(ValidationError):
            x.validate()

    def testUnion(self):

        class X1(Object):
            m = Union.T(members=[Int.T(), StringChoice.T(['small', 'large'])])

        class U(Union):
            members = [ Int.T(), StringChoice.T(['small', 'large']) ]
    
        class X2(Object):
            m = U.T()

        X = X2
        x1 = X(m='1')
        with self.assertRaises(ValidationError):
            x1.validate()

        x1.validate(regularize=True)
        self.assertEqual(x1.m, 1)

        x2 = X(m='small')
        x2.validate()
        x3 = X(m='fail!')
        with self.assertRaises(ValidationError):
            x3.validate()
        with self.assertRaises(ValidationError):
            x3.validate(regularize=True)

    def testTooMany(self):

        class A(Object):
            m = List.T(Int.T())
            xmltagname = 'a'

        a = A(m=[1,2,3])

        class A(Object):
            m = Int.T()
            xmltagname = 'a'
        
        with self.assertRaises(ArgumentError):
            a2 = load_xml_string(a.dump_xml())

    def testDeferred(self):
        class A(Object):
            p = Defer('B.T', optional=True)

        class B(Object):
            p = A.T()

        a = A(p=B(p=A()))

    def testListDeferred(self):
        class A(Object):
            p = List.T(Defer('B.T'))
            q = List.T(Defer('B.T'))

        class B(Object):
            p = List.T(A.T())

        a = A(p=[B(p=[A()])], q=[B(),B()])

    def testSelfDeferred(self):
        class A(Object):
            a = Defer('A.T', optional=True)

        a = A(a=A(a=A()))

    def testContentStyleXML(self):

        class Duration(Object):
            unit = String.T(optional=True, xmlstyle='attribute')
            uncertainty = Float.T(optional=True)
            value = Float.T(optional=True, xmlstyle='content')

            xmltagname = 'duration'

        s = '<duration unit="s"><uncertainty>0.1</uncertainty>10.5</duration>'
        dur = load_xml_string(s)
        self.assertEqual(dur.value, float('10.5'))
        self.assertEqual(dur.unit, 's')
        self.assertEqual(dur.uncertainty, float('0.1'))
        self.assertEqual(re.sub(r'\n\s*', '', dur.dump_xml()), s)
    
    
def makeBasicTypeTest(Type, sample, sample_in=None, xml=False):

    if sample_in is None:
        sample_in = sample

    def basicTypeTest(self):

        class X(Object):
            a = Type.T()
            b = Type.T(optional=True)
            c = Type.T(default=sample)
            d = List.T(Type.T())
            e = Tuple.T(1, Type.T())
            xmltagname = 'x'

        x = X(a=sample_in, e=(sample_in,))
        x.d.append(sample_in)
        if sample_in is not sample:
            with self.assertRaises(ValidationError):
                x.validate()

        x.validate(regularize=sample_in is not sample)
        self.assertEqualNanAware(sample, x.a)
        
        if not xml:
            x2 = load_string(x.dump())

        else:
            x2 = load_xml_string(x.dump_xml())

        self.assertEqualNanAware(x.a, x2.a)
        self.assertIsNone(x.b)
        self.assertIsNone(x2.b)
        self.assertEqualNanAware(sample, x.c)
        self.assertEqualNanAware(sample, x2.c)
        self.assertTrue(isinstance(x.d, list))
        self.assertTrue(isinstance(x2.d, list))
        self.assertEqualNanAware(x.d[0], sample)
        self.assertEqualNanAware(x2.d[0], sample)
        self.assertEqual(len(x.d), 1)
        self.assertEqual(len(x2.d), 1)
        self.assertTrue(isinstance(x.e, tuple))
        self.assertTrue(isinstance(x2.e, tuple))
        self.assertEqualNanAware(x.e[0], sample)
        self.assertEqualNanAware(x2.e[0], sample)
        self.assertEqual(len(x.e), 1)
        self.assertEqual(len(x2.e), 1)

    return basicTypeTest

for Type in samples:
    for isample, sample in enumerate(samples[Type]):
        for xml in (False, True):
            setattr(TestGuts, 'testBasicType' + Type.__name__ + 
                    str(isample) + ['','XML'][xml], 
                    makeBasicTypeTest(Type, sample, xml=xml))

for Type in regularize:
    for isample, (sample_in, sample) in enumerate(regularize[Type]):
        for xml in (False, True):
            setattr(TestGuts, 'testBasicTypeRegularize' + Type.__name__ +
                    str(isample) + ['','XML'][xml], 
                    makeBasicTypeTest(Type, sample, sample_in=sample_in, xml=xml))
                
if __name__ == '__main__':
    unittest.main()

