import numpy as np
import matplotlib.pyplot as plt
from common import probeId2Name, frontendId2Name, fileId2Name
from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import aws_delays, aws_distances
from common import true_fe_for_file, true_file_for_fe


def scatterplot_within_aws():
    """
    """
    Xs, Ys = list(), list()
    for frontend in cdgeb_frontends:
        for filename in cdgeb_files:

            distance = aws_distances[(frontend, filename)]
            delay = aws_delays[(frontend, filename)]
            
            Xs.append(distance)
            Ys.append(delay)

    slope = np.linalg.lstsq(np.array(Xs)[:, np.newaxis], np.array(Ys), rcond=None)[0][0]

    plt.scatter(Xs, Ys)

    # Generate points for the trendline
    trendline_x = np.linspace(min(Xs), max(Xs), 100)
    trendline_y = slope * trendline_x  # y = slope * x

    # Plot the trendline
    plt.plot(trendline_x, trendline_y, color='red', label=f'Trendline: y = {slope:.5e}x')
    
    plt.xlabel('Distance [km]')
    plt.ylabel('Time (single-direction) [s]')
    plt.title(f'Within AWS')
    plt.legend()

    plt.show()

def scatterplot_within_aws_12_17():
    """
    Ad-hoc implementation
    """
    Xs, Ys = list(), list()
    Xs12, Ys12 = list(), list()
    Xs17, Ys17 = list(), list()
    for frontend in cdgeb_frontends:
        for filename in cdgeb_files:

            distance = aws_distances[(frontend, filename)]
            delay = aws_delays[(frontend, filename)]


            if frontend == 'cdgeb-server-12' or filename == true_file_for_fe['cdgeb-server-12']:
                Xs12.append(distance)
                Ys12.append(delay)
            elif frontend == 'cdgeb-server-17' or filename == true_file_for_fe['cdgeb-server-17']:
                # some server-17 measurements will match with previous block and will not get here.
                Xs17.append(distance)
                Ys17.append(delay)
            else:    
                Xs.append(distance)
                Ys.append(delay)
    
    slope = np.linalg.lstsq(np.array(Xs+Xs12+Xs17)[:, np.newaxis], np.array(Ys+Ys12+Ys17), rcond=None)[0][0]

    plt.scatter(Xs, Ys)
    plt.scatter(Xs12, Ys12, label='cdgeb-server-12')
    plt.scatter(Xs17, Ys17, label='cdgeb-server-17')

    # Generate points for the trendline
    trendline_x = np.linspace(min(Xs), max(Xs), 100)
    trendline_y = slope * trendline_x  # y = slope * x

    # Plot the trendline
    plt.plot(trendline_x, trendline_y, color='red', label=f'Trendline: y = {slope:.5e}x')
    
    plt.xlabel('Distance [km]')
    plt.ylabel('Time (single-direction) [s]')
    plt.title(f'Within AWS')
    plt.legend()

    plt.show()


scatterplot_within_aws_12_17()
