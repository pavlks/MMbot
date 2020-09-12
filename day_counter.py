import calendar
from datetime import date, timedelta
from tabulate import tabulate


def time_period(name, birth, start, end):
    startdate = date.fromisoformat(str(start)) - timedelta(days=1)
    if not end:
        enddate = date.today()
        third_line = ['конец', 'активен']
    else:
        enddate = date.fromisoformat(str(end))
        third_line = ['конец', enddate]
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
    second_line = ['начало', startdate]
    forth_line = ['прошло', time_line]
    table = [second_line, third_line, forth_line]

    result_part1 = f'<b>{name}</b> {birth}'
    result_part2 = "<code>" + tabulate(table, tablefmt="pretty") + "</code>"
    result = result_part1 + '\n' + result_part2
    return result
