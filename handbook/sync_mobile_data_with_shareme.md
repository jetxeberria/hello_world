# Sync mobile data with Share Me

- Configure FTP connection in computer
  - Install FTP service: `apt-get install vsftpd`
  - Start FTP service: `/etc/init.d/vsftpd start`

- Run app "ShareMe" on smartphone
  - Options logo > Konektatu ordenagailura > Hasi > SD Txartela edo Barneko memorioa
  - Helbide bat emango didate: `ftp://192.168.1.129:2121`

- Open directory in computer (nautilus)
  - Other Locations > Connect to Server > Enter server address...
  - Write `ftp://192.168.1.129:2121` > Connect 
  - Registered user > Type credentials configured in App

- Saioa hasteko datuak App-ean zehazten dira:
  - Options logo > Konektatu ordenagailura > Ezarpenak logo > Saioa Hasi
  - Idatzi izena eta passahitza: By default those to log in workstation
