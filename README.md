<img width="720" height="292" alt="圖片1" src="https://github.com/user-attachments/assets/f3004281-8579-424d-9c55-97150451cdeb" />

** You could load and save left top frame's entries with the "Load and Save" button, for your convenience =) **

How to change BIOS tokens: (except password)
1) enter bmc ip , username and pw, then press "Dump"
2) BIOS configuration file dump as txt
3) tokens shows on the treeview side (right hand side)
4) double click on the value, and it shows several options, pick the one you want to change
5) click "Revise" to create an edited txt file
6) click "Patch" to revise tokens in BIOS
7) click "Reboot" to apply new changes

Change PW:
1) enter bmc ip , username and pw, and PW attribute name (default should be SETUP001)
  2a) if BIOS haven't set any PW, leave it blank and just enter the new pw
    3a) press "change PW"
    4a) press "Reboot"
  2b) if BIOS have set PW before, enter old PW and new PW, then press "Change PW"
    3a) press "change PW"
    4a) press "Reboot"
