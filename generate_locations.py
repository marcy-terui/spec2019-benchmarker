import json

from faker import Factory

fake = Factory.create('en_US')
cities = {}
for i in range(2000):
    cities[str(i)] = fake.city()

json.dump(cities, open('location.json', 'w'))
