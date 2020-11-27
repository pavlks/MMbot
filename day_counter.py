import calendar
from datetime import date, timedelta
from tabulate import tabulate


def time_period(name, birth, start, end):
    b_date = date.fromisoformat(birth).strftime('%d-%b-%Y')
    startdate_str = date.fromisoformat(str(start)).strftime('%d-%m-%Y')
    startdate = date.fromisoformat(str(start)) - timedelta(days=1)
    if not end:
        enddate = date.today()
        third_line = ['конец', 'активен']
    else:
        enddate = date.fromisoformat(str(end))
        enddate_str = enddate.strftime('%d-%m-%Y')
        third_line = ['конец', enddate_str]
    total_months = int()
    prev_date = startdate
    next_date = startdate
    while next_date <= enddate:
        month_days = calendar.monthrange(next_date.year, next_date.month)[1]
        prev_date, next_date = next_date, next_date + timedelta(days=month_days)
        if next_date <= enddate:
            total_months += 1

    days = enddate - prev_date
    total_days = days.days
    weeks = (enddate - prev_date).days // 7
    weekdays = (enddate - prev_date).days % 7

    last_sunday = not bool(date.isoweekday(enddate) - weekdays > 0)
    count_sundays = weeks + last_sunday

    if total_months > 0:
        months = f'{total_months} мес '
    else:
        months = ''
    if total_days > 0:
        days = f'{total_days}({count_sundays}) дн'
    else:
        days = ''

    time_line = f'{months}{days}'
    #first_line = ['дата рожд', birth]
    second_line = ['начало', startdate_str]
    forth_line = ['прошло', time_line]
    table = [second_line, third_line, forth_line]

    result_part1 = f'<b>{name}</b> {b_date}'
    result_part2 = "<code>" + tabulate(table, tablefmt="pretty") + "</code>"
    result = result_part1 + '\n' + result_part2
    return result
