from collections import UserDict
from datetime import datetime
from itertools import islice
from abc import ABC, abstractmethod
import re
import json
try:
    import pyttsx3
except ModuleNotFoundError as error:
    print(error)

input_line = "-" * 50 + "\n"\
    "Input command \n"\
    "(example: 'add name phone_number')"


class AddressBook(UserDict):
    def add_record(self, record) -> str:
        if record.name.value not in self.data.keys():
            self.data[record.name.value] = record
            return f'Contact {record.name} create successful'
        return f'Contact {record.name} already exist'

    def delete_record(self, name) -> str:
        self.data.pop(name)
        return f'Contact {name} deleted successful'

    def iterator(self, start=None, stop=None):
        keys = islice(self.data.keys(), start, stop)
        result = '\n'.join(
            f'{i}: +{", +".join(p.value for p in self.data.get(i).phones)}, birthday {self.data.get(i).birthday}' for i in keys)

        yield result


class Field:
    def __init__(self, value):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            if len(value) > 2:
                self._value = value
        except ValueError:
            raise ValueError(
                "Value must be a string of length of at least 2")

    def __repr__(self) -> str:
        return self._value


class Birthday:
    def __init__(self, value="13 October 1990"):
        self._value = None
        self.value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value):
        try:
            self._value = datetime.strptime(value, '%d-%m-%Y').date()
        except ValueError:
            raise ValueError(
                "Invalid date format. Please use format: DD-MM-YYYY")

    def __repr__(self) -> str:
        return self._value.strftime('%d-%m-%Y')


class Name(Field):

    @Field.value.setter
    def value(self, value):
        try:
            if value.isalpha():
                super(Name, Name).value.__set__(self, value)
        except ValueError:
            raise ValueError(
                "Value must be a string of alphabetical characters")


class Record:
    def __init__(self, name: Name, phone=None, birthday=None):
        self.name = name
        self.phones = [phone] if phone else []
        self.birthday = birthday

    def add_phone(self, phone):
        self.phones.append(phone)
        return f'{phone} added to contact {self.name}'

    def change_phone(self, old_phone, new_phone) -> str:
        if old_phone not in self.phones:
            self.phones.remove(old_phone)
            self.phones.append(new_phone)
            return f'Phone {old_phone} changed to {new_phone}'
        return f'Phone {old_phone} not in {self.name} phones'

    def delet_phone(self, phone):
        self.phones.remove(phone)

    def days_to_birthday(self) -> int:
        if self.birthday:
            today = datetime.now().date()
            target_day = self.birthday.value.replace(year=today.year)
            if target_day < today:
                target_day = self.birthday.value.replace(year=today.year+1)
            difference = (target_day - today).days
            return difference


class Phone(Field):
    @Field.value.setter
    def value(self, value):
        try:
            if re.match(r'^\d{12}$', value):
                super(Phone, Phone).value.__set__(self, value)
        except ValueError:
            raise ValueError("Phone must be in 123456789876 format")

    def __eq__(self, __obj: object) -> bool:
        return self.value == __obj.value

class UserInterface(ABC):

    @abstractmethod
    def display_contacts(self, iter_book):
        pass

    @abstractmethod
    def display_help(self, command_dict):
        pass


class ConsoleInterface(UserInterface):

    def display_contacts(self, iter_book):
        print(iter_book())
        iter_book


    def display_help(self, command_dict):
        print("Available commands:")
        for command in command_dict.keys():
            print(command)


book = AddressBook()
file_name = 'address_book.json'
interface = ConsoleInterface()


def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            print("Контакт не знайдено")
        except ValueError as error:
            print(error)
        except TypeError:
            print("Недостатньо аргументів")
    return wrapper


def iter_book(*args):
    stop = int(input("Input step "))
    start = 0
    step = stop
    while True:
        text = next(book.iterator(start, stop))
        if not text:
            break
        print(text)
        input("Press enter to continue ")
        start += step
        stop += step
    if not text:
        return f"No contacts for print"


def add_record(command):
    splitting_arguments = command.strip().split()
    if len(splitting_arguments) >= 2:
        if len(splitting_arguments) == 3:
            key, name, phone = splitting_arguments
            contact_name = Name(name)
            contact_phone = Phone(phone)
            rec = Record(contact_name, contact_phone)
        elif len(splitting_arguments) == 4:
            key, name, phone, birthday = splitting_arguments
            contact_name = Name(name)
            contact_phone = Phone(phone)
            rec = Record(contact_name, contact_phone, Birthday(birthday))
        if name in book.data.keys() and contact_phone not in book.data.get(name).phones:
            return book.data.get(name).add_phone(contact_phone)
        if contact_name:
            # for Name(None) does not create dict
            result = book.add_record(rec)
            return result


@ input_error
def birthday(command):
    splitting_arguments = command.strip().split()
    key, name = splitting_arguments
    record = book.data.get(name)
    return f"days to birthday {name} - {record.days_to_birthday()}"


@ input_error
def change_record(command):
    arguments = command.strip().split()
    if len(arguments) == 4:
        key, name, phone, new_phone = arguments
        if name in book.data.keys() and Phone(phone) in book.data.get(name).phones:
            return book.data.get(name).change_phone(Phone(phone), Phone(new_phone))


@ input_error
def delete(command):
    argument = command.strip().split()[1]
    if argument:
        return book.delete_record(argument)


def find(command):
    splitting_arguments = command.strip().split()
    names = islice(book.data.keys(), 0, None)
    for name, record in book.data.items():
        if splitting_arguments[1] in name:
            result = f"Contact name:{name},phone:{record.phones},birthday: {record.birthday}"
            return result
        if splitting_arguments[1] in str(record.phones):
            result = f"Contact name:{name},phone:{record.phones},birthday: {record.birthday}"
            return result
    return f"not find math"


def get_func(command):
    arg_list = command.strip().split()
    for key in command_dict.keys():
        if arg_list[0].lower() == 'hello':
            return command_dict[key]
        elif arg_list[0].lower() == key:
            func = command_dict.get(key)
            return func(command)
        elif arg_list[0].lower() in key:
            return command_dict[key]
    raise KeyError("This command doesn't exist")

def help_info(*args):
    interface.display_help(command_dict)
    return "End of the list"

def show_contacts(*args):
    interface.display_contacts(iter_book)
    return "End of the iteration"
def save_book():
    with open(file_name, "w") as fh:
        data = {}
        for i in book.data:
            data[i] = {"name": i, "phones": [p.value for p in book.data.get(
                i).phones], "birthday": str(book.data.get(i).birthday)}
        json.dump(data, fh)


def read_book():
    try:
        with open(file_name, "r") as fh:
            data = json.load(fh)
        return data
    except (FileNotFoundError, AttributeError):
        data = {}
    return data


def parse_data(data):
    for name, rec_dict in data.items():
        phones_list = rec_dict.get("phones")
        phones = []
        for phone in phones_list:
            phones.append(Phone(phone))
        birthday = rec_dict.get("birthday")
        record = Record(Name(name))
        record.phones = phones
        record.birthday = Birthday(birthday)
        book.add_record(record)


command_dict = {"hello": "How can I help you?", "add": add_record, "birthday": birthday, "change": change_record, "delete": delete,"help":help_info,
                "show": show_contacts, "find": find, ("good", "bye", "close", "exit"): "Good bye!"}


def main():
    while True:
        parse_data(read_book())
        command = input(input_line).lower()
        # command = "add test 123456789876 10-02-1990"
        func = get_func(command)
        # engine = pyttsx3.init()
        # engine.say(func)

        # engine.runAndWait()
        print(func)
        save_book()
        if command.split()[0] in ["good", "bye", "close", "exit"]:
            break


if __name__ == '__main__':
    main()
