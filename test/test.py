#!/usr/bin/python3
"""Module Docstring"""


def get_numbers_from_file(file_name):
    with open(file_name, mode='rb') as file:
        for line in file:
            yield int(line)


def get_even_numbers(list_of_numbers):
    for number in list_of_numbers:
        if number % 2 == 0:
            yield number


def normalize(list_of_numbers):
    if iter(list_of_numbers) is iter(list_of_numbers):
        raise TypeError("Must supply a container")
    total = sum(list_of_numbers)
    for number in list_of_numbers:
        yield number / total


class number_reader:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, mode='rb') as file:
            for line in file:
                yield int(line)


def main():
    """Function Docstring"""
    ints = number_reader("numbers.txt")
    # ints = get_numbers_from_file("numbers.txt")
    print(list(ints))
    name = 'bob'
    text = f"hello {name}"
    print(text)

    even_numbers = get_even_numbers(ints)
    print(list(even_numbers))

    normalized = normalize(ints)
    print(list(normalized))


if __name__ == '__main__':
    main()
