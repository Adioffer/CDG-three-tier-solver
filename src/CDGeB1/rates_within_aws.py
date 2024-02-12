import numpy as np
from common import Continent, frontend_continents
from common import probeId2Name, frontendId2Name, fileId2Name
from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import aws_delays, aws_distances
from common import real_fe_for_file


def evaluate_rates(filter_allow):
    """ Evaluate the communication rates within AWs network.
    filter_allow: a filter over the measurements (for example - filter out inter-continent measurements)
    return: rate [km/s]
    """
    Xs, Ys = list(), list()
    for frontend in cdgeb_frontends:
        for filename in cdgeb_files:
            if not filter_allow(frontend, filename):
                continue

            distance = aws_distances[(frontend, filename)]
            delay = aws_delays[(frontend, filename)]
            
            Xs.append(distance)
            Ys.append(delay)

    slope = np.linalg.lstsq(np.array(Xs)[:, np.newaxis], np.array(Ys), rcond=None)[0][0]

    return round(1 / slope, 2)

def rates_aws():
    rates_all = evaluate_rates(lambda a, b: True) # Allow all measurements
    print("Rates within AWS (All measuremenets):", rates_all)
    
    rates = dict()
    for continent_a in Continent:
        for continent_b in Continent:
            rate = evaluate_rates(lambda frontend, filename: ((frontend_continents[frontend] == continent_a) and \
                                                (frontend_continents[real_fe_for_file[filename]] == continent_b)))
            print(f'Rates within AWS ({continent_a} to {continent_b}):', rate)
            rates[(continent_a, continent_b)] = rate
    
    return rates

def pretty_print(rates):
    from rich.console import Console
    from rich.table import Table

    # Extract unique row headers and column headers
    rows = sorted(set(str(key[0]) for key in rates))
    columns = sorted(set(str(key[1]) for key in rates))

    # Create a Rich table
    table = Table(title="Data Table")

    # Add the columns to the table, first column for row headers
    table.add_column("Row\\Column", justify="right", style="cyan", no_wrap=True)
    for column in columns:
        table.add_column(column, justify="center")

    # Add rows and their corresponding data to the table
    for row in rows:
        row_data = [str(rates.get((row, column), "")) for column in columns]
        table.add_row(row, *row_data)

    # Print the table
    console = Console()
    console.print(table)

rates = rates_aws()

# print(str(rates).replace('<Continent.AS: \'', '').replace('<Continent.EU: \'', '').replace('<Continent.AMN: \'', '').replace('<Continent.AU: \'', '').replace('<Continent.ANS: \'', '').replace('\'>', ''))
print(str(rates).replace('<','').replace(': \'Asia\'>', '').replace(': \'Europe\'>', '').replace(': \'N. America\'>', '').replace(': \'S. America\'>', '').replace(': \'Australia\'>', '').replace('inf', 'float(\'inf\')'))
pretty_print(rates)
