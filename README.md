# CEITEC Nano Core Facility BlueBox

<img width="1600" height="500" alt="luebox_reneder_v3" src="https://github.com/user-attachments/assets/18011d01-acb8-4f4e-9f0f-2409e8dedea6" />

BlueBoxes are an extension for the core facility Ceitec Nano booking/ reservation system (https://today.ceitec.cz/nano and https://booking.ceitec.cz/) created with the intention of easing the reservation process and increasing the effectiveness of instrument usage in the core facility. 

The basic usage idea of creating the BlueBoxes is to authorise previously created reservations by swiping the user's card (RFID) over the RFID reader inside the BlueBox. The authorisation process is then initiated, checking user credentials and the presence of a reservation linked with the user and equipment. If authorisation is successful, the initial time of the reservation is edited to correspond to real time. If the user does not authorise the reservation, it is cancelled after a timeout, providing a free slot for another user. Additional features are: the ability to stop a reservation from the BlueBox if needed, and the ability to extend the running reservation on the spot from the BlueBox.

BlueBoxes are designed to be relatively minimalistic, cheap, yet functional devices operating on the Raspberry Pi 4, with an LCD display and an RFID reader.

RPi4 was selected because it provides LAN/Ethernet and WIFI connectivity, the Python language is relatively easy to program, and there are numerous existing libraries for peripheral modules and RPi4. Used modules (RFID reader, LCD display, buttons) are widely available.

The [electronic](../../wiki/Hardware) side of the BlueBoxes is composed of modules. Due to still running development (discovering required functions), the modularity and swapability of modules were prioritised over the possible compact size of the custom PCB (maybe in the future). 

BlueBox case is 3D [printed](../../wiki/Printing) from PLA filament.
 
