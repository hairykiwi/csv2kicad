#csv2kicad_energymicro

##About
A KiCad library generator which accepts structured CSV data as input.

###Useage
Either one user specified .csv file name as a command line argument, or none. If a file name is specified, it is reflected in the names of the LIB and DCM output files generated. If none is supplied, all .csv files in the current working directory are processed and the two output file types share a common (fixed) name.

##Input data - source
The structure of the CSV data used ***must*** match that of the files available from [Energy Micro](http://www.energymicro.com/) for its range of EFM32 ultra low power ARM Cortex MCUs.

Current CSV data for the entire EFM32 family can be found in the zip file associated with the Application Note: ***AN0002 Hardware Design Considerations***, here: http://www.energymicro.com/downloads/application-notes

**Note:** The zipped Energy Micro CSV data which is included in this git repo should be considered **for demo only** and will **not** be maintained.

##Output
For each device (CSV file), four units are generated:
- Unit 1 : PAx/PBx pins,
- Unit 2 : PCx/PDx pins,
- Unit 3 : PEx/PFx pins,
- Unit 4 : Power pins.

###Stylistic conformity
Generated components are consistently similar in appearance.
Additionally, minimum spacing between groups of pins of related functionality in all 'Units 4' is ensured by rule.

**Note:** KiCad unfortunately lacks the ability to specify a position for the component name relative to the box outline of *each* unit, however, the user can move it to the desired location - typically the lower left corner - after inserting the component in a schematic.

##Corrections, suggestions and constructive feedback
All 144 components in the library have been checked for consistency of appearance, but not for absolute correctness.

If you find any problem, please raise an issue on github - and/or fork this project, correct the problem and submit a pull request.

Feedback is gratefully received. Many aspects of this script could no doubt be improved upon. As a novice programmer, my intention was to make it as easy to debug and repurpose as possible, so that it might be adapted to generate data for other similar components with relative ease.
As such, I am not interested in its outright performance so much as its maintainability by other, equally novice programmers.

If you feel it could be in anyway improved, tidied, extended or adapted please send comments to me at:
info at meadtimemachines dot co dot uk

##Legal
***No warranty is expressed or implied.***

No content related to this repo, either static or generated, should be considered as having been in anyway endorsed or reviewed by Energy Micro SA, Norway.

All intellectual property belonging to any third party mentioned shall remain respectively so.

###Licence
[CC-BY-SA 3.0](http://creativecommons.org/licenses/by-sa/3.0/)

*csv2kicad_energymicro* is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License - you are strongly encouraged to improve upon and hack *csv2kicad_energymicro*.
