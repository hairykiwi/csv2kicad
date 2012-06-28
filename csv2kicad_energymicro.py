#!/usr/bin/python
########################################################################
########################################################################
"""
##                        csv2kicad_energymicro
##
## A KiCad library generator which accepts structured CSV data as input.
##
## The structure of the CSV data used *must* match that of the files
## available from Energy Micro for its range of EFM32 ultra low power
## ARM Cortex MCUs.
##
## Current CSV data for the entire EFM32 family can be found in the zip
## file associated with the Application Note:
## 'AN0002 Hardware Design Considerations' here:
## http://www.energymicro.com/downloads/application-notes
##
## For each device (CSV file), four units are generated in the LIB
## output file:
## Unit 1 : PAx/PBx pins,
## Unit 2 : PCx/PDx pins,
## Unit 3 : PEx/PFx pins,
## Unit 4 : Power pins.
##
## Generated components are consistently similar in appearance.
## Additionally, minimum spacing between groups of pins of related
## functionality in all 'Units 4' is ensured by rule.
##
## Designed by:
## Hamish Mead ( info at meadtimemachines dot co dot uk )
## for the Mead Time Machines open source watch project:
## http://meadtimemachines.com - if nothing of much interest is seen
## there, you're a wee bit early, a tad too late, or nothing ever came
## of it - such are the nuances and nuiscance of time.
##
## Corrections, suggestions and constructive feedback:
## If you find any problem, please raise an issue on github - and/or
## fork this project, correct the problem and submit a pull request.
##
## Feedback:
## Is gratefully received. Many aspects of this script could no doubt be
## improved upon. As a novice programmer, my intention was to make it as
## easy to debug and repurpose as possible, so that it might be adapted
## to generate data for other similar components with relative ease.
## As such, I am not interested in its outright performance so much as
## its maintainability by other, equally novice programmers. If you feel
## it could be in anyway improved, tidied, extended or adapted please
## send comments to me at:
## info at meadtimemachines dot co dot uk -
##
## Legal:
## No warranty is expressed or implied.
## - Neither this file nor any generated output data should be
## considered as having been in anyway endorsed or reviewed by
## Energy Micro SA, Norway.
## - All intellectual property belonging to any third party mentioned
## shall remain respectively so.
##
## License:
## CC BY-NC-SA 3.0 http://creativecommons.org/licenses/by-sa/3.0/
## Creative Commons Attribution-ShareAlike 3.0 Unported
## http://creativecommons.org/licenses/by-sa/3.0/legalcode
## You are strongly encouraged to improve upon and hack this.
##
"""
########################################################################
## Credits:
## Many thanks to Abhijit Bose( info@adharlabs.in ) for writing
## libgen - Library Generator Program for Kicad Schematics V0.1
## https://github.com/AdharLabs/Kicad-tools/blob/master/libgen/libgen.py
## It provided great insight on where to start, on this, my first
## python project.
##
## Special thanks to the python community too, for all the tricky
## questions asked at stackoverflow.com especially - and other examples
## provided around the web. Without these, writing this would have taken
## much, much longer.
##
## Version History:
## 0.4.1 2012-06-28
##     - Placement of AVDD_z and IOVDD_z now determined by comparing
##       minimum spacing requirements of each.
##     - A DCM file is also now automatically created.
##
## 0.3 - Unit 4 (power) height now depends on multiple pin row counters.
##     - Unit 4 pin (X,Y) position now determined by calculation and
##     - lookup values.
##
## 0.2 - Fixed bug in regex preventing reading of (A)VSS power pins.
##     - Unit 4 (power) height now dependent on package pin count.
##     - "/" removed after each pin where no alternate function exists.
##     - Blank row inserted between PXzz and PYaa within each unit.
##
## 0.1   2012-06-18 - Initial version.
##
## TODO:
## - Utilise the KiCad component 'alias' function to reduce output file-
##   size.
## - Impart more data to DCM file as and when it becomes available in
##   easily processed form from Energy Micro.
## - Investigate using a python dictionary function in place of the
##   'collection of fixed-position pins' for Unit 4 pin arrangement -
##   probably of more relevance to repurposing this script.
##
########################################################################
########################################################################
# IMPORT >
import os, sys, argparse, re, csv, datetime
from collections import Counter
from itertools import groupby

########################################################################
# EXPORT >
__author__ = "Hamish Mead (info at meadtimemachines dot co dot uk)"
__version__ = "0.4"

########################################################################
# DEBUG > Print Additional Debug Messages
# if needed, make _debugflag = 1 for verbose, or 2 for limited.
# Note that 2 requires local editing of "_debugflag == x" lines
_debugflag = 2

########################################################################
# GLOBAL VARIABLES >
header_flag = 0

########################################################################
# TEMPLATES >

template_lib_header = """EESchema-LIBRARY Version 2.3 Date: {dtg}
#encoding utf-8
#generated by: {sfname} - v{filever}
#
"""

template_lib_body = """# {compname}
#
DEF {compname} U 0 40 Y Y 4 L N
F0 "U" {refposx} {refposy} 60 H V L BNN
F1 "{compname}" {nameposx} {nameposy} 60 H V L BNN
$FPLIST
 {footprint}
$ENDFPLIST
DRAW
{comp_pin_data}ENDDRAW
ENDDEF
#
"""
template_lib_footer = """# End Library
"""

template_dcm_header = """EESchema-DOCLIB  Version 2.0  Date: {dtg}
#encoding utf-8
#generated by: {sfname} - v{filever}
#
"""

template_dcm_body = """$CMP {compname}
D Family: {chipname}, Package: {footprint}, Package size: {fpsize}
K Energy Micro energymicro EFM32 32bit ARM Cortex Flash Microcontroller MCU
F http://www.energymicro.com/downloads/datasheets
$ENDCMP
#
"""

template_dcm_footer = """# End Doc Library
"""

########################################################################
# SORTING FUNCTIONS >

# Natural alphanumeric sort
# From http://stackoverflow.com/questions/4836710/does-python-have-a-
# built-in-function-for-string-natural-sort
def natural_sort(list, key=lambda s:s):
  """
  Sort the list into natural alphanumeric order.
  """
  def get_alphanum_key_func(key):
    convert = lambda text: int(text) if text.isdigit() else text
    return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
  sort_key = get_alphanum_key_func(key)
  list.sort(key=sort_key)

# Sort table by multiple columns
# Adapted from http://www.saltycrane.com/blog/2007/12/how-to-sort-table-
# by-columns-in-python/
def sort_table(table, cols):
  """ sort a table by multiple columns
      table: a list of lists (or tuple of tuples) where each inner
             list represents a row.
      cols:  a list (or tuple) specifying the column numbers to sort
             by. e.g. (1,0) would sort by column 1, then by column 0.
  """
  for col in reversed(cols):
    natural_sort(table, key=lambda x: x[col])
  return table

########################################################################
########################################################################
# PRIMARY DATA GENERATING FUNCTION
#
########################################################################
# Stage 1
# Get device description data: name, chip name, package and pin count
# (Some of these values are as yet not utilised)


def efm2kicad_generator(f_in):

  global header_flag

  script_file_name = sys.argv[0]

  # A few containers
  csv_list_str = []
  em_data_list = []
  em_data1 = []
  readnames = []
  data = []
  data1 = []
  sorted_table = []
  out_table = []
  unit_boxes = []
  final = []
  final1 = []
  final2 = []

  with open(f_in, 'rb') as f:

    if _debugflag == 1:
      print "\n\nROW IN FILE"

    # Read in the device CSV file
    for row in csv.reader(f, delimiter=';'):
      csv_list_str.append(row)

      if _debugflag == 1:
        print row

  # Get part name from R2,C1
  part_name_row = csv_list_str[2-1]
  part_name = part_name_row[1]
  # Get chip name from R3,C1
  chip_name_row = csv_list_str[3-1]
  chip_name = chip_name_row[1]
  # Get package type from R4,C1
  package_row = csv_list_str[4-1]
  package = package_row[1]
  # Get pin count from R6,C1
  pin_cout_row = csv_list_str[6-1]
  pin_count = pin_cout_row[1]
  # Get package size from R7,C1
  package_dims_row = csv_list_str[7-1]
  package_dims = package_dims_row[1]

  # Delete header rows ready for pin data extraction
  del csv_list_str[0:8+1]

  # Reassemble the data into a list of lists for the next stage
  for row in csv_list_str:
    em_data_list.append(';'.join(map(str, row)))

  if _debugflag == 1:
    print "\n\nEM_DATA_LIST"
    print em_data_list

########################################################################
# Stage 2
# Tidy and format data using regex's

  # perform some line by line regex editing
  for line in em_data_list:
    line = re.sub(r'//\s(?=\w)','', line )
    # Insert Unit column header
    line = re.sub(r'(Pin.name;)', '\\1Unit;' ,line)
    # Insert Unit number based on Pin Names and append a "/" between
    # pin Name and pin Functionality
    line = re.sub(r'((PA|PB)\d{1,2});', '\\1/;1;' ,line)
    line = re.sub(r'((PC|PD)\d{1,2});', '\\1/;2;' ,line)
    line = re.sub(r'((PE|PF)\d{1,2});', '\\1/;3;' ,line)
    line = re.sub(r'(^\w*\d{1,2};(IOVD.*?|A{0,1}VSS.*?|A{0,1}VDD.*?|RESE.*?|DECO.*?|USB_.*?));', '\\1;4;' ,line)
    # Replace any SPACE and COMMA delimiters
    line = re.sub(r' #','_#', line )
    line = re.sub(r' / ','/', line )
    line = re.sub(r',','-', line )
    line = re.sub(r'\s','_', line ) # inserts underscores in headings
    # Abbreviate Pin Types to KiCAD pin type terminology
    # (partial kicad type listing - expand as required)
    line = re.sub(r'(?i)unknown', 'U', line) # (?i) = Ignore case
    line = re.sub(r'(?i)power', 'W', line) # 'W' is specifically POWER IN
    line = re.sub(r'(^\d{1,2};USB_VREGO;4);W;', '\\1;w;', line) # 'w' is specifically POWER OUT
    line = re.sub(r'(?i)passive', 'P', line)
    em_data1.append(line)

  # Reformat the data ready for reordering columns
  # Split the regex'd lines at ";" and place them in another container

  for line in em_data1:
    readnames.append(line.split(';'))

  if _debugflag == 1:
    print "\n\nREADNAMES"
    print readnames

########################################################################
# Stage 3
# Reorder columns
# From http://stackoverflow.com/questions/6117868/...
# ...write-csv-columns-out-in-a-different-order-in-python
#
# Original order:
# "'// Pin id'  'Pin name'  'Pin type'  'Functionality'"


  # The new order in which to arrange the columns
  writenames = "Pin_name;Functionality;Pin_id;Unit;Pin_type".split(";")

  if _debugflag == 1:
    print "\n\nWRITENAMES"
    print writenames

  # Create a dictionary using the column headings in the first row
  name2index = dict((k, v) for v, k in enumerate(readnames[0]))

  if _debugflag == 1:
    print "\n\nNAMES TO INDEX"
    print name2index

  # Create a list of the keys based on the existing column headings,
  # and ordered according to the desired column order
  writeindices = [name2index[k] for k in writenames]

  if _debugflag == 1:
    print "\n\nWRITE INDICIES"
    print writeindices

  if _debugflag == 1:
    print "\n\nDATA ROW"

  # Place the reordered columns in another container
  for row in readnames:
    data_row = [row[i] for i in writeindices]
    data.append(data_row)
    if _debugflag == 1:
      print data_row
########################################################################
# Stage 4A
# Group the data into units and sort pin names within those units
# using the natural alphanumeric sort function
# From http://lists.ironpython.com/htdig.cgi/users-ironpython.com/...
# 2009-January/009556.html
#
# Stage 4B
# Insert pin (Y) position data
#
# Unique Power Unit (4) pin names to position in a predefined layout:
# ['RESETn',
# 'AVDD_0', 'AVDD_1', 'AVDD_2',
# 'AVSS_0', 'AVSS_1', 'AVSS_2',
# 'DECOUPLE',
# 'IOVDD_0', 'IOVDD_1', 'IOVDD_2', 'IOVDD_3',
# 'IOVDD_4', 'IOVDD_5', 'IOVDD_6',
# 'USB_VBUS', 'USB_VREGI', 'USB_VREGO',
# 'VDD_DREG',
# 'VSS(1 to n)', 'VSS_DREG', 'VSS_PAD']


  # Column location (within list) of the Units and pin_names values
  unit_col = 3
  pinname_col = 0

  # Determine pin count within each sub-group of Unit 4 (power) pins
  for row in data:
    # If not a GPIO pin, copy the row to a new list
    if not re.match(r'^P\w\d{1,2}', row[0]):
      data1.append(row[0])

  # Delete the first (header) row in the new list
  del data1[0]

  if _debugflag == 1:
    print "\n\nDATA1"
    print data1

  # Count total instances of each GROUP of pin names
  # eg AVDD_1, _2, _3 = AVDD : 3
  # This compares names after triming the last char off each using:
  count_dict_pin_name = Counter(row[0:5] for row in data1)

  # Extract the useful counts from above into vars
  avdd_tot = count_dict_pin_name['AVDD_']
  avss_tot = count_dict_pin_name['AVSS_']
  iovdd_tot = count_dict_pin_name['IOVDD']
  vss_tot = count_dict_pin_name['VSS']
  vssdreg_flag = bool(count_dict_pin_name['VSS_D'])
  usbv_flag = bool(count_dict_pin_name['USB_V'])

  if _debugflag == 1:
    print "\n\nCOUNT INSTANCES OF ASSOCIATED POWER PIN"
    print count_dict_pin_name

  # First get the headings
  heading = data[0]

  # Delete the heading row - leaving data rows
  del data[0]

  # First unit number in a multi unit component
  unit_number = 0

  # Unit 4 (only) has a fixed width
  unit4_width = 1000

  pin_length = 300

  # LEFT side pin text orientation (note apparent reverse orientation!)
  # and size: format = 'R pin_name_size pin_number_size'
  pin_left_lts = (str(pin_length) + ' R 50 50')
  #pin_left_txt_size = ' R 50 50'
  #pin_left_lts = str(pin_length) + pin_left_txt_size

  # LEFT side pin (X) position
  pin_l_x = str(0)

  # RIGHT side pin text orientation (note apparent reverse orientation!)
  # and size: format = 'L pin_name_size pin_number_size'
  pin_right_lts = (str(pin_length) + ' L 50 50')
  #pin_right_txt_size = ' L 50 50'
  #pin_right_lts = str(pin_length) + pin_right_txt_size

  # RIGHT side pin (X) position
  pin_r_x = str(unit4_width + 2 * pin_length)

  # Location of first pin in each Unit group
  pin_y_spacing = 100

  # Y offset from top & bottom pins to top or bottom of Unit box outline
  pin_y_box_offset = 150

  # Collection of fixed-position pins, pin relative offset values, and
  # pin orientation, length and text size in Unit 4 (power)
  up1 = ['RESETn', 0,  pin_left_lts]
  up2 = ['DECOUPLE', 0, pin_right_lts]
  up3 = ['IOVDD_n', 6, pin_right_lts]
  up4 = ['USB_VBUS', 4, pin_left_lts]
  up5 = ['USB_VREGI', 6, pin_left_lts]
  up6 = ['USB_VREGO', 7, pin_left_lts]
  up7 = ['VDD_DREG', 2, pin_right_lts]
  up8 = ['VSS_DREG',3, pin_right_lts]
  up9 = ['VSS', 3, pin_right_lts]
  up10 = ['AVDD', 4, pin_left_lts]
  up11 = ['AVSS', 2, pin_left_lts]

  # Position of Unit reference, eg U1
  ref_pos_x = 30 + pin_length
  ref_pos_y = 30 + pin_y_box_offset

  # Position of PartUnit reference, eg U1
  name_pos_x = 330 + pin_length
  name_pos_y = 30 + pin_y_box_offset

  if _debugflag == 1:
    print "\n\nROW IN SORT_TABLE"

  # Determine placement of AVDD_n (max) and IOVDD_n (max) by comparing
  # existance of USB function with pin count of IOVDD and AVDD.
  avdd_iovdd_comp = [0,0] # A compare container

  # Max required (Y) position of AVDD_n(max)
  avdd_iovdd_comp[0] = (usbv_flag * up6[1] + up10[1] + avdd_tot)

  # Max required (Y) position of IOVDD_n(max)
  avdd_iovdd_comp[1] = (iovdd_tot + up3[1])
  avdd_iovdd_max = max(avdd_iovdd_comp)
  #print avdd_comp # Debug
  #print avdd_max # Debug

  # Sort the data by Unit, then by pin name
  for row in sort_table(data, (unit_col,pinname_col)):

    if _debugflag == 1:
      print row

    # If the Unit number is not the same as that of the previous row,
    # reset the counters
    if int(row[unit_col]) != unit_number:
      counter_row_in_unit = 0
      unit_row_sub_flag = 0
      unit_number += 1
      iovdd_row_counter = 0
      vss_row_counter = 0
      avdd_row_counter = 0
      avss_row_counter = 0

    # Within each unit insert a blank row between PXnn and PYnn
    if unit_row_sub_flag == 0:
      if re.match(r'^PB|PD|PF\d{1,2}', row[pinname_col]):
        unit_row_sub_flag = 1
        counter_row_in_unit += 1

    # Insert the pin position data based on
    # pin name order in each Unit group

    # Unit 1 to 3: pins ordered according to alphanumeric sort by name
    row.insert(0, 'X') # Kicad designator for a pin line = "X"
    row.insert(-1, '1')
    row.insert(-3, pin_l_x) # Default pin X-pos
    row.insert(-3, str(-(pin_y_spacing * counter_row_in_unit))) # Pin Y-pos
    row.insert(-3, pin_left_lts) # Default pin LEFT, length & text sizes

    # Reset pin
    if row[1] == up1[0]:
      row[1] = '~RESET~' # double '~' displays vinculum over pin name
      row[5] = str(-(up1[1] * pin_y_spacing))
      row[6] = up1[2] # Pin length, direction and text size
      row[9] = 'P I' # Elect.type: P=Passive, Graphic style: I=Inv.Pin

    # Decouple
    if row[1] == up2[0]:
      row[4] = pin_r_x # Pin X-position
      row[5] = str(-(up2[1] * pin_y_spacing)) # Pin Y-pos
      row[6] = up2[2] # Pin length, direction and text size

    # IOVDD_x
    if re.match('IOVDD_\d', row[1]):
      row[4] = pin_r_x # Pin X-position
      row[5] = str(-(avdd_iovdd_max - iovdd_tot + iovdd_row_counter) * \
                      pin_y_spacing) # Pin Y-pos
      row[6] = up3[2] # Pin length, direction and text size
      iovdd_row_counter += 1

    # USB_VBUS
    if row[1] == up4[0]:
      row[4] = pin_l_x # Pin X-position
      row[5] = str(-(up4[1] * pin_y_spacing)) # Pin Y-pos
      row[6] = up4[2] # Pin length, direction and text size

    # USB_VREGI
    if row[1] == up5[0]:
      row[4] = pin_l_x # Pin X-position
      row[5] = str(-(up5[1] * pin_y_spacing)) # Pin Y-pos
      row[6] = up5[2] # Pin length, direction and text size

    # USB_VREGO
    if row[1] == up6[0]:
      row[4] = pin_l_x # Pin X-position
      row[5] = str(-(up6[1] * pin_y_spacing)) # Pin Y-pos
      row[6] = up6[2] # Pin length, direction and text size

    # VDD_DREG
    if row[1] == up7[0]:
      row[4] = pin_r_x # Pin X-position
      row[5] = str(-(avdd_iovdd_max - iovdd_tot - up7[1]) * \
                      pin_y_spacing) # Pin Y-pos
      row[6] = up7[2] # Pin length, direction and text size

    # VSS_DREG
    if row[1] == up8[0]:
      vss_dreg_flag = 2
      row[4] = pin_r_x # Pin X-position
      row[5] = str(-(up8[1] + avdd_iovdd_max) * pin_y_spacing) # Pin Y-pos
      #row[5] = str(-(up8[1] + iovdd_tot + 6) * pin_y_spacing) # Pin Y-pos
      row[6] = up8[2] # Pin length, direction and text size

    # VSS
    if re.match('VSS(?!.D)', row[1]):
      row[4] = pin_r_x # Pin X-position
      row[5] = str(-(avdd_iovdd_max + up9[1] + (vssdreg_flag * 2) + \
                      vss_row_counter) * pin_y_spacing) # Pin Y-pos
      row[6] = up9[2] # Pin length, direction and text size
      vss_row_counter += 1
      # vss_max (vss or vss_pad) determines box height
      vss_max = (avdd_iovdd_max + up9[1] + (vssdreg_flag * 2) + \
                      vss_row_counter - 1)

    # AVDD_n - v0.4
    if re.match('AVDD_.', row[1]):
      row[4] = pin_l_x # Pin X-position
      row[5] = str(-(avdd_iovdd_max - avdd_tot + avdd_row_counter) * \
                      pin_y_spacing) # Pin Y-pos
      row[6] = up10[2] # Pin length, direction and text size
      avdd_row_counter += 1

    # AVSS_n
    if re.match('AVSS_.', row[1]):
      row[4] = pin_l_x # Pin X-position
      row[5] = str(-(avdd_iovdd_max + up9[1] + (vssdreg_flag * 2) + \
                      vss_tot + avss_row_counter - avss_tot) * \
                      pin_y_spacing) # Pin Y-pos
      row[6] = up11[2] # Pin length, direction and text size
      avss_row_counter += 1

    counter_row_in_unit += 1
    sorted_table.append(row)

  if _debugflag == 1:
    print "\n\nvss_max, vssdreg_flag, avss_tot, \
          avss_row_counter, iovdd_row_counter"
    print vss_max, vssdreg_flag, avss_tot, \
          avss_row_counter, iovdd_row_counter

########################################################################
# Stage 5
# Create (sub) unit box outlines

  # Create a dictionary of pins per unit
  count_dict = Counter(row[7] for row in data)
  if _debugflag == 1:
    print "\n\nCOUNT DICT"
    print count_dict

  x_min = pin_length
  y_max = pin_y_box_offset

  # Group by unit number
  for unit, group in groupby(sorted_table, lambda x: x[7]):

    if int(unit) < 4:
      # (2 * spacing accounts for blank row between PXnn and PYnn)
      y_min = -(pin_y_spacing * int(count_dict[unit])
                + pin_y_box_offset)
      x_max = (max([len(row[1] + row[2]) for row in group]) *
                45 + 300  + pin_length)
    else:
      # For Unit 4 (power unit)
      y_min = -(vss_max * pin_y_spacing + pin_y_box_offset)
      x_max = unit4_width + pin_length
    boxrow = "S %s %s %s %s %s 1 0 N" % (x_min,
              y_max, x_max, y_min, unit)
    unit_boxes.append(boxrow.split(','))

  # Put it all together
  for row in unit_boxes:
    final.append(';'.join(map(str, row)))

  for row in sorted_table:
    final.append(';'.join(map(str, row)))

  if _debugflag == 1:
    print "\n\nFINAL"
    print final

  # Strip out the last remaining delimiters
  for line in final:
    line = re.sub(r'/;','/', line ) # Between pin name and function
    line = re.sub(r';;',' ', line ) # As occurs in Unit 4
    line = re.sub(r';',' ', line )
    line = re.sub(r'/ ',' ', line ) # As occurs when pin is GPIO only
    line += "\n"
    final1.append(line)

  final2 = ''.join(str(n) for n in final1)

  if _debugflag == 1:
    print "\n\nFINAL 2"
    print final2

  now = datetime.datetime.now()
  date_time_group = now.strftime("%Y-%m-%d %X")

  # Open output file for appending data
  f_out_lib = open(fdest_lib, 'a')
  f_out_dcm = open(fdest_dcm, 'a')

  if header_flag == 0:
    header_flag = 1
    output_lib = template_lib_header.format(dtg =     date_time_group,
                                            sfname = script_file_name,
                                            filever = __version__)

    output_dcm = template_dcm_header.format(dtg =     date_time_group,
                                            sfname = script_file_name,
                                            filever = __version__)

    f_out_lib.write(output_lib)
    f_out_dcm.write(output_dcm)

  output_lib = template_lib_body.format(compname =      part_name,
                                        footprint =     package,
                                        refposx =       str(ref_pos_x),
                                        refposy =       str(ref_pos_y),
                                        nameposx =      str(name_pos_x),
                                        nameposy =      str(name_pos_y),
                                        comp_pin_data = final2)


  output_dcm = template_dcm_body.format(compname =      part_name,
                                        chipname =      chip_name,
                                        footprint =     package,
                                        fpsize =        package_dims)


  f_out_lib.write(output_lib)
  f_out_dcm.write(output_dcm)

  f_out_lib.close()
  f_out_dcm.close()

########################################################################
# HELP >

user_help = """

 A Kicad library generator that accepts CSV data formatted according
 to the layout of the CSV files from Energy Micro, for its range of
 EFM32 ultra low power ARM Cortex MCUs.

The format of all csv input files must conform to layout shown in the
snippet below, but only insofar as elemental device data is located
in the rows and 'cells' as implied. Comments anchors; "//" are not
necessary.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BEGIN SNIPPET ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//--------------------------------------------------------------------
// Part name;EFM32GG330F1024
// Chip name;Gecko
// Package;QFN64
// Package type;QFN
// Pin count;64
// Package dimensions;9mm x 9mm
//--------------------------------------------------------------------
// Pins
// Pin id;Pin name;Pin type;Functionality
1;PA0;Unknown;GPIO_EM4WU0 / I2C0_SDA #0 / ... / TIM0_CC0 #0,1,4
...
65;VSS_PAD;Power;
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ END SNIPPET ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Where:
'Pin id' is device pin number. Alphanumeric Pin id's are valid.
'Pin name' is required.
'Pin type' must either conform to those currently used by Energy Micro,
('PASSIVE', 'UNKNOWN', or 'POWER') - or to the Kicad standard:
  I: INPUT
  O: OUTPUT
  B: Bi-Directional
  T: TRISTATE
  P: PASSIVE
  U: UNSPECIFIED
  W: POWER INPUT
  w: POWER OUTPUT
  C: OPEN COLLECTOR
  E: OPEN EMITTER
  N: NOT CONNECTED


Kicad LIB and DCM textual content rules:
DESCRIPTION (D in DCM file) may contain any alphanumeric or
special character including a SPACE.

KEYWORDS (K in DCM file) is a SPACE delimited field and may only
contain alphanumeric characters, including UNDERSCORE.


Note that any SPACE and COMMA characters appearing in the input are
reformatted in the output to conform to Kicad requirements and/or
best practise.i.e. SPACEs either side of a FWD SLASH between alternate
functions, (" / ") are removed, a SPACE within an alternate
function, ("I2C0_SDA #0") is replaced with an UNDERSCORE, and COMMAs
are replaced with DASHs: (TIM0_CC0_#0,1,4).

Latest CSV data for Energy Micro devices can be found in the zip file
associated with: 'AN0002 - Hardware Design Considerations',
available from: http://www.energymicro.com/downloads/application-notes

------------------------------------------------------------------------
Disclaimer:
 - Short:
 Alway check the output, foool!
 - Verbose:
 Nothing shall be taken to imply that Energy Micro AS, Norway endorse
 or in anyway recommends this file, its output or any other associated
 file(s). While the validity of the output has been thoroughly checked
 by the author, no responsibility shall be accepted for any errors or
 ommisions resulting in any subsequential losses or damages to the
 user or other parties, howsoever related.
------------------------------------------------------------------------

When the optional <inputfile.csv> is provided, its name is reflected in
the output .LIB (library) and .DCM (documentation) file names.
If no <inputfile.csv> is supplied, csv2kicad_energymicro processes all
CSV files in the current working directory and informs the user of the
(fixed) file names after processing is complete.

"""

########################################################################
# MAIN FUNCTION >

# Output file names
fdest_lib = "energymicro-efm32.lib"
fdest_dcm = "energymicro-efm32.dcm"

# A file counter for user feedback
fcounter = 0

# Get the working directory
working_dir = os.getcwd()

if __name__ == "__main__" :

  parser = argparse.ArgumentParser(
  usage='%(prog)s [<inputfile.csv>]',
  formatter_class=argparse.RawDescriptionHelpFormatter,
  description = user_help)

  parser.add_argument('inputfile', nargs = '?', help = 'An optional \
                      csv file. if none is specified, all csv files in \
                      the current working directory are processed.')

  arguments = parser.parse_args()

  f_in = arguments.inputfile

  # If a file name argument is NOT supplied, process ALL CSV files in
  # the working directory and write kicad data to .lib and .dcm files
  if not sys.argv[1:]:

    print "Working..."

    # Clear the contents of the output files if they already exist
    f_out_lib = open(fdest_lib, 'w')
    f_out_lib.write('')
    f_out_lib.close()

    f_out_dcm = open(fdest_dcm, 'w')
    f_out_dcm.write('')
    f_out_dcm.close()

    # For each file in the working directory with a .csv extension
    for filename in os.listdir(working_dir):
      if filename.endswith(".csv"):

        # Processed files counter
        fcounter += 1

        if _debugflag == 2:
          print filename

        # Call the primary data generating function
        efm2kicad_generator(filename)

  # If a CSV file name argument IS supplied, reflect that name in the
  # output file names, replacing the .csv with .lib and .dcm
  else:

    # Check the input file exists
    if not os.path.isfile(f_in):
      raise IOError("\nPlease check the file exists.")

    else:
      if not f_in.endswith(".csv"):
        raise IOError("\nPlease provide a file with a .csv extension.")

      # The name of the lib and dcm files is based on the input file
      # (Match any character - match the dot - match any character)
      foutname = re.match('(.*)\..*', f_in)

      # Create the destination library file name
      fdest_lib = (str(foutname.group(1))+ '.lib')

       # Create the destination documentation file name
      fdest_dcm = (str(foutname.group(1))+ '.dcm')

      # Clear the contents of the output files if they already exist
      f_out_lib = open(fdest_lib, 'w')
      f_out_lib.write('')
      f_out_lib.close()

      f_out_dcm = open(fdest_dcm, 'w')
      f_out_dcm.write('')
      f_out_dcm.close()

      # Call the main data conversion function
      efm2kicad_generator(f_in)

      fcounter = 1

  # Write the library file footer
  f_out_lib = open(fdest_lib, 'a')
  f_out_lib.write(template_lib_footer)
  f_out_lib.close()

  # Write the documentation file footer
  f_out_dcm = open(fdest_dcm, 'a')
  f_out_dcm.write(template_dcm_footer)
  f_out_dcm.close()

  # Provide some feedback about what was processed,
  # and name of the new library files.
  if fcounter > 1:
    outsubstring = " CSV files were "
  else:
    outsubstring = " CSV file was "

  print "\n"+ str(fcounter) + outsubstring +"processed.\n\
The following two files were created or updated:\n" +\
fdest_lib + "\n" + fdest_dcm + "\n\n"

########################################################################
