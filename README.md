# dhcp-snooping-script
Python Script for DHCP Snooping Configuration

Hi! Thanks for downloading my script!

The dhcp-snooping-script is an automation that I made for the company that I work in order to solve a problem with dhcp that resulted in repetitive calls. It's functionality is to access the hosts via ssh and configure the trusted, untrustworthy ports and limit rates. The logs are registered on the folder "reports". 

Network is not my area of expertise and I'm studying data analysis, so this was a personal challenge that I set myself and managed to deal with. Feel free to edit the code!

----------------------------------------


Instructions:

1. SSH Connection:
	You need to have ssh installed on your disk! If u don't have it's not going to work.


2. parameters.txt:
	You have to define the variables on the "parameters.txt"!

	user ----------------> User for host access
	Example: user=myuser

	password ------------> Password for host access
	Example: password=mypass

	csv_path ------------> Path for csv file
	Example: csv_path=C:\Users\User\Documents\dhcp-snooping-script\example.csv
	Example: csv_path=example.csv (for when the csv file is on the same directory of the script)

	exclusive_vlans -----> Vlans that should not enter the configuration;
	Example: exclusive_vlans=1,2,4,10 (for excluding the vlans 1, 2, 4 and 10)

	trust_port_name -----> Standardized port name for trust ports.
	Example: trust_port_name=linkport

	specific_text -------> Identification of exception ports through the specific text containing check.
	Example: specific_text=link_0 (for adding every port that has "link_0" on their names);

	specific_limit_rate -> Specific limit rate for exception ports;
	Example: specific_limit_rate=50 (for setting the limit rate for the exception ports)

	default_limit_rate --> Default limit rate;
	Example: default_limit_rate=10

	ignore_errors -------> Bool expression (True/False) for ignoring errors and skiping for next step. Its best use is during testing;
	Example: ignore_errors=False

	simulation ----------> Bool expression (True/False) for simulating the configuration;
	Example: simulation=True

	timeout -------------> Maximum connection time in seconds.
	Example: timeout=60


3. CSV File:
	The csv file should be standardized exactly like the example for working. The order of implementation is ascending (from top to bottom).

	1 column -> Addresses

	2 column -> Run Script ('Y' for yes, 'N' for no)

	3 column -> Allow Untrusted ('Y' for yes, 'N' for no)
	The "Allow Untrusted" is for switches at the edge of in-row clusters
	
	For better comprehension, check the "example.csv" file

4. IMPORTANT NOTE
	BEFORE RUNNING THE SCRIPT MAKE SURE THE IMPLEMENTATION ORDER COMPLIES WITH THE CLUSTERS!!

----------------------------------------


If you downloaded somewhere... Here's my github.
https://github.com/caiython

Contact me: caiocvlopes@gmail.com

----- Script developed by Caiython -----
