import csv
import argparse
from pypif import pif
from pypif.obj import *
import os


def lfa457_to_pif(closed_csv):
    print("FILE IDENTIFIED AS LFA-457: {}").format(closed_csv)

    # create chemical system and property array
    my_pif = ChemicalSystem()
    my_pif.ids = [os.path.basename(closed_csv).split("_")[0]]
    my_pif.properties = []

    # Store index so that iteration can start at next row. Default to False when no header is found.
    header_row_index = False

    # Initialize arrays for diffusivity and conditions (time and temp)
    temp_array = []
    time_array = []
    diffusivity_array = []

    with open(closed_csv, 'rU') as open_csv:
        reader = csv.reader(open_csv)
        for index, row in enumerate(reader):

            # meta data is stored above property with header column = row[0]

            # ensure row has values
            if len(row) == 0:
                continue

            # set properties based on row[0]
            if '#Material' in row[0]:
                my_pif.chemical_formula = row[1].strip()

            if "#Instrument" in row[0]:
                measurement_device = Instrument(name=row[1].replace("#", ""))

            if "#Thickness_RT/mm" in row[0]:
                thickness = Property(name="Thickness", scalars=row[1], units="mm")

            if "#Diameter/mm" in row[0]:
                diameter = Property(name="Diameter", scalars=row[1], units="mm")

            if "#Date" in row[0]:
                date = Value(name="Experiment date", scalars=row[1].strip())

            if "#Atmosphere" in row[0]:
                atmosphere = Value(name="Atmosphere", scalars=row[1].strip())

            if "#Gas_flow/(ml/min)" in row[0]:
                flow = Value(name="Flow rate", scalars=row[1], units="ml/min")

            # shot number defines header_row
            if "#Shot" in row[0] and "Std_Dev" in row[4]:
                header_row_index = index
                header_row = row
                for h_index, h in enumerate(header_row):
                    if "Temperature" in h:
                        temp_index = h_index
                    if "Diffusivity" in h:
                        diff_index = h_index
                    if "Std_Dev" in h:
                        std_index = h_index
            if "#Shot" in row[0] or "#Time/min" in row[0]:
                header_row_index = index
                header_row = row
                for h_index, h in enumerate(header_row):
                    if "Temperature" in h:
                        temp_index = h_index
                    if "Diffusivity" in h:
                        diff_index = h_index
                    std_index = False

            # we could find header row and collect all rows after it or regex row[0] for a decimal number
            if header_row_index:
                if index > header_row_index:
                    if row[temp_index] and row[diff_index]:
                        temp_array.append(row[temp_index])
                        if std_index:
                            diffusivity_array.append(row[diff_index]+"$\pm$"+row[std_index])
                        else:
                            diffusivity_array.append(row[diff_index])

    heat_capacity = Property('Diffusivity', scalars=diffusivity_array, units='mm$^2$/s')
    temp = Value(name='Temperature', scalars=temp_array, units='$^\circ$C')
    #time = Value(name='Time', scalars=time_array, units='min')

    heat_capacity.conditions = [temp, date, atmosphere, flow]
    heat_capacity.instrument = measurement_device
    heat_capacity.files = FileReference(relative_path=os.path.basename(closed_csv))

    my_pif.properties.append(heat_capacity)
    my_pif.properties.append(thickness)
    my_pif.properties.append(diameter)

    return my_pif


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='*', help='path to LFA csv')

    args = parser.parse_args()

    for f in args.csv:
        print("PARSING: {}".format(f))
        pifs = lfa457_to_pif(f)
        f_out = f.replace(".csv", ".json")
        print("OUTPUT FILE: {}").format(f_out)
        pif.dump(pifs, open(f_out, "w"), indent=4)