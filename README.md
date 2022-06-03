# **CSSE4011 Project - Activity Classification with Thingy52**
## Zues - Yellow

## **Members**
### Brandon Lawler
### ChunWei (James) Tang

## **PC Software**

This is the PC based software constructed for `CSSE4011 Project B4 - Activity Classification with Thingy52` (2022). The `thingy52` is setup to capture acceleration, magnetometer and gyroscope data and send it to the base node USB device which received the data via `bluetooth` and send it to the computer program via `serial` communication.

The following program is constructed to receive the serial input, and using the `K Nearest Neighbour` machine learning algorithm determine the current activity being completed by the user. The base activities include `Sitting, Standing, Walking, and Running`. 

The program is also required to upload all the data to the influx cloud database for storage and easy vieweing of the data.

The program also has the ability to add other classifications and train these new activities. The process of installing, configuring and training this program is outlined below.

### **Setup**

Download the `python` software following this link:
    https://www.python.org/downloads/

Install the `pip` software following this guide:
    https://pip.pypa.io/en/stable/installation/

Install the required `packages` for this program:
```SHELL
$ cd CSSE4011-Project-PC
$ pip install -r requirements.txt
```

### **Starting the Program**

Once the setup process is complete the program can be run by running the following command:
```SHELL
$ python main.py
```

If you are wanting to clear the training data, you can run the following command - be warned that this will delete all training data:
```SHELL
$ python main.py --clear
```

### **Configuring the Program**

Once the program is running, the user can configure the program by selecting the `Config Tab` at the top of the screen. From here you can input the serial COM port for the program to connect to. Furthermore, you can add new activity classifications to the program by typing the name of the activity and pressing the `Add` button. Finally, all but the base classifications can be removed by pressing the `Trash Can` Icon on the right side of the classification.

### **Training Data**

Once the program is running, the user can add new training data by going to the `Train Tab`, then using the drop down select box to select the activity to be trained. The user can then use the `Start` button to start the collection of data from the Serial input. This will update the KNN Algorithm when it is next run.

### **Active Mode**

Once the program is running, and once the training data has been downloaded from the Influx database. On the `Active Tab`, once downloaded the user can press the start button to begin the active mode. The program will then begin to collect data from the serial input and using the trained KNN algorithm will determine the current activity being completed.
