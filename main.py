from datetime import datetime
from datetime import date
import json
import re
import requests
import xml.etree.ElementTree as ET


class Spending:
    # 0 tag = 1
    def __init__(self, index, amount, currency, time, calendar_date, category="Unknown"):
        # self.index = Spending.tag
        self.index = index
        self.amount = amount
        self.currency = currency
        self.time = time if time is not None else None
        self.date = calendar_date if calendar_date is not None else None
        self.category = category
        # Spending.tag += 1

    def timing(self):
        self.time = f"{datetime.now().hour}:{datetime.now().minute}"
        self.date = f"{date.today().day}.{date.today().month}.{date.today().year}"


#  def categorizing(self): TODO:implement categorizing function with dictionary of
#      while True:
#         pass
#     self.category=4

class Day:
    def __init__(self, calendar_date=f"{date.today().day}.{date.today().month}.{date.today().year}",
                 cnst=0, currency="RUB", money_left=0):
        self.date = calendar_date  # dd.mm.yyyy
        self.constraint = cnst
        self.currency = currency
        self.money_left = money_left
        self.spending = []

    def add_spending(self, spend: Spending):
        self.spending.append(spend)

    def find_money(self):
        k = self.constraint
        for s in self.spending:
            k -= s.amount
        self.money_left = k


# http://www.cbr.ru/development/sxml/
# https://docs.python.org/3/library/xml.etree.elementtree.html
def bank(dat="04/12/2020", lang="rus"):
    try:
        if lang == "rus":
            req = requests.get(f"http://www.cbr.ru/scripts/XML_daily.asp?date_req={dat}")
            get(req)
        elif lang == "eng":
            req = requests.get(f"http://www.cbr.ru/scripts/XML_daily_eng.asp?date_req={dat}")
            get(req)
        else:
            print("Do not know this language:")
    except:
        print("Something went wrong")


def get(r):
    if r.status_code == 200:
        root = ET.fromstring(r.content)
        for currency in root.findall("Valute"):
            name = currency.find("Name").text
            if name in ("Доллар США", "US Dollar", "Евро", "Euro"):  # Hardcoded
                value = currency.find("Value").text
                print(f"{name} - {value} RUB")
    else:
        print("Something went wrong with a request")


def input_special_str(msg, our_tuple: iter, err_msg):
    while True:
        answer = input(msg)
        if answer in our_tuple:
            return answer
        else:
            print(err_msg)


def input_data(msg: str) -> int:
    while True:
        try:
            d = int(input(msg))
            return d
        except ValueError:
            print("Try again, the INPUT should be integer ")


def input_custom(input_msg, condition, err_msg,):
    while True:
        try:
            choice = int(input(input_msg))
            if condition(choice):
                return choice
            else:
                print(err_msg)
        except ValueError:
            print("Incorrect format")


def input_with_mask(msg, mask):
    while True:
        pass_number = input(msg)
        match = re.match(mask, pass_number)
        if match:
            return pass_number
        else:
            print("Incorrect Format")


# TODO: implement bot functionality
# TODO: BOt all interactions with user should be rewritten


# https://docs.python.org/3/library/json.html
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Spending, Day)):  # hardcoded
            key = f"__{obj.__class__.__name__}__"
            return {key: obj.__dict__}
        return json.JSONEncoder.default(self, obj)


def join_obj(objects: iter, encoder=MyEncoder):  # from many json objects makes tree
    data = {}
    for obj in objects:
        key = f"__{obj.__class__.__name__}__"
        obj = json.loads(encoder().encode(obj))[key]
        if key in data:
            data[key].append(obj)
        else:
            data[key] = [obj]
    data = json.dumps(data, cls=MyEncoder, separators=(',', ':'))
    return data


def fill_in_file(file_name, data):
    with open(file_name, "w", encoding="UTF-8") as f:
        f.write(data)
        f.close()


def take_from_file(file_name):
    with open(file_name, "r", encoding="UTF-8") as f:
        data = f.read()
        return data


def json_to_list(file_name: str):  # converts json objects to proper python objects
    list_days = []
    for day in json.loads(take_from_file(file_name))["__Day__"]:
        d = Day(day["date"])
        for dic in day["spending"]:
            obj = dic["__Spending__"]
            s = Spending(obj["index"], obj["amount"], obj["currency"], obj["time"], obj["date"], obj["category"])
            d.add_spending(s)
        list_days.append(d)
    return list_days


def find_today(list_days: list) -> (Day, bool):
    tday = Day()
    flag = False
    for day in list_days:
        if day.date == f"{date.today().day}.{date.today().month}.{date.today().year}":
            tday = day
            flag = True
    return tday, flag


def create_new_spending(spendings):
    spent = Spending(index=0, amount=0, currency="RUB", time=None, calendar_date=None, category="Unknown")
    spent.amount = input_data(f"\nSent me amount of {spent.currency} you spent today: ")
    while True:
        flag = input(f"Would you like to change currency from {spent.currency}? y/n:")
        if flag == "y":
            spent.currency = input("Enter a currency: ")
            break
        elif flag == "n":
            break
        else:
            print("No such option:")
    spent.index = len(spendings)
    spent.timing()
    spendings.append(spent)


def show_spendings_day(day: Day):
    if len(day.spending) == 0:
        print("No spendings in this day")
    else:
        for s in day.spending:
            if s.category == "Unknown":
                print(f"{s.amount} {s.currency} was spent at {s.time}")
            else:
                print(f"{s.amount} {s.currency} was spent at {s.time} buying {s.category}")


def show_spendings_month(list_days, month):
    flag = False
    for day in list_days:
        if day.date[3:5] == str(month) and day.date[6:10] == str(date.today().year):
            flag = True
            print(day.date)
            show_spendings_day(day)
    if not flag:
        print("No days found in this month")


def starting_message():
    print("Hello we will help you to get used to writing down your spendings")
    input("Enter any symbol if you are ready to start: ")
    print("Sent period in days, for which you would like to keep a budget ")
    period = input_custom("Your period: ", lambda x: x > 0, "Enter a positive number")
    print(f"Sent your budget for {period} days")
    budget = input_custom(f"Your budget for {period} days: ", lambda x: x >= 0, "Enter a non-negative number")
    print(f"You have {budget} RUB for {period} days ")
    flag = input_special_str("Are input data correct? y/n: ", ("y", "n"), "Unidentified symbol. Enter 'y' or 'n' ")

    if flag == "n":
        while True:
            print("If you want to change period sent 'p'")
            print("If you want to change budget sent 'b'")
            print("If you don't want to make any changes sent 'exit' ")
            choice = input_special_str("", ("p", "b", "exit"), "invalid input: Enter b for changing budget OR "
                                                               "p for changing period OR exit to go back")
            if choice == "p":
                period = input_custom("Your period: ", lambda x: x > 0, "Enter a positive number")
            elif choice == "b":
                budget = input_custom(f"Your budget for {period} days: ", lambda x: x >= 0,
                                      "Enter a non-negative number")
            elif choice == "exit":
                break

    print(f"Great!\nYou have {budget} RUB for {period} days ")
    print(f"OR only {round(budget / period)} RUB per day")
    return period, budget


def main_menu():
    days = json_to_list("spend.json")
    today, found = find_today(days)

    ch0 = input_special_str("Would you like to change period/budget y/n: ", ("y", "n"), "There is no such option")
    if ch0 == "y":
        global gbudget, gperiod
        gperiod, gbudget = starting_message()
        today.constraint = round(gbudget / gperiod)
        today.find_money()

    while True:
        print('\nChoose an option:')
        print('1 - view spendings')
        print('2 - correct spendings')
        print('3 - add new spending')
        print('4 - view exchange rates from CB')
        print('5 - exit the application')
        ch = input_custom('Your choice: ', lambda x: x in (1, 2, 3, 4, 5), "There is no such option")

        if ch == 1:
            while True:
                print('\nChoose an option:')
                print("1 - view today's spendings: ")
                print("2 - view spendings by date: ")
                print("3 - view this month spendings: ")
                print("4 - view spendings by month: ")
                # print("5 - view this year spendings: ")
                # print("6 - view spendings by year: ")  # view spendings from t1 to t2
                print('5 - exit to the main menu')
                ch1 = input_custom('Your choice: ', lambda x: x in (1, 2, 3, 4, 5), "There is no such option")

                if ch1 == 1:  # view today's spendings
                    show_spendings_day(today)
                elif ch1 == 2:  # view spendings by date
                    f_date = input_with_mask("Enter date dd.mm.yyyy: ", r"(\d{2})\.(\d{2})\.(\d{4})")
                    flag = False
                    for day in days:
                        if day.date == f_date:
                            flag = True
                            show_spendings_day(day)
                    if not flag:
                        print(f"Day with this date is not found ")
                elif ch1 == 3:  # view this month spendings
                    show_spendings_month(days, date.today().month)
                elif ch1 == 4:  # view spendings by month
                    f_month = input_with_mask("Enter month mm: ", r"(\d{2})")
                    show_spendings_month(days, f_month)
                elif ch1 == 5:  # exit to the main menu
                    break

        elif ch == 2:  # need to be changed
            while True:
                print('\nChoose an option:')
                print("1 - correct day's spendings: ")
                print("2 - delete all spendings by date: ")
                ch31 = input_custom('Your choice: ', lambda y: y in (1, 2), "There is no such option")

                if ch31 == 2:

                    # ch29 = input_custom('Your choice: ', f, "There is no such option")
                    f_date = input_with_mask("Enter date dd.mm.yyyy: ", r"(\d{2})\.(\d{2})\.(\d{4})")
                    flag = False
                    for day in days:
                        if day.date == f_date:
                            flag = True
                            show_spendings_day(day)
                    if not flag:
                        print(f"Day with this date is not found ")

                    ch30 = input('Are you sure you want to delete this day from your spending list (y/n)? ')
                    if ch30 == 'y':
                        # spend.json.pop(index - 1)
                        print('Day successfully deleted from the contact book.')
                        input('Press Enter to return to the main menu')
                        main_menu()

                elif ch31 == 1:
                    print('?')

        elif ch == 3:
            create_new_spending(today.spending)
            today.money_left -= today.spending[-1].amount
            print(f"You have only {today.money_left} {today.currency} for today")
        elif ch == 4:  # view exchange rates
            time = input_with_mask("Enter date dd.mm.yyyy: ", r"(\d{2})\.(\d{2})\.(\d{4})")
            time = time[0:2] + "/" + time[3:5] + "/" + time[6:10]
            bank(time, "eng")
        elif ch == 5:  # exit the application
            break

    if found:
        i = 0
        i_today = -1
        for day in days:
            if day.date == today.date:
                i_today = i
            i += 1
        if i_today >= 0:
            days[i_today] = today
    else:
        days.append(today)
    fill_in_file("spend.json", join_obj(days, encoder=MyEncoder))


"""--------------------------------------------------------"""
# s1 = Spending(1, 0, "RUB", "11:23", "01.01.2021", "PRESENT")
# s2 = Spending(2, 1230, "RUB", "15:23", "01.01.2021", "TREE")
# s3 = Spending(3, 4535, "RUB", "12:54", "02.02.2020", "LAPTOP")
# list_of_spendings1 = [s1, s2, s3]
# day1 = Day()
# day1.add_spending(s1)
# day1.add_spending(s2)
# day2 = Day("13.12.2020")
# day2.add_spending(s3)
# days1 = [day1, day2]
"""--------------------------------------------------------"""
gperiod = 30  # gperiod its a Global Period
gbudget = 30000   # gbudget it's a global  budget

main_menu()
