from django.test import TestCase

# Create your tests here.



class A():


    def __init__(self):

        self._name = 'hello'
        self.__first = 'word'


a = A()

print(a._name)

