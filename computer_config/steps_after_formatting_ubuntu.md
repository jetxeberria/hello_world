## FORMAT COMPUTER:
- Turn of computer
- Plug usb-live with ubuntu
- Turn on computer
- Press F11 (jetxeberria-ws) to open boot menu
- Boot from USB
- Press Install ubuntu
- Continue until program recognizes in which partitions there are operative systems installed and below options arise:  

  1. install ubuntu partition
  2. erase all disk and install ubuntu partition
  3. something else

- Select option 3
- Then you see all the partitions of plugged disks. In case of jetxeberria-ws there are 2 disks. One SDD (sda) and one HDD (sdb):
Following the partitions description written in "Distribucion_de_particiones.md":
  - select all partitions to be mounted in their corresponding mount point /dev/sda2, /dev/sda5, /dev/sda6, /dev/sda7, /dev/sdb5, /dev/sdb6, /dev/sdb8)
  - format the partitions related with ubuntu system  (/dev/sda2, /dev/sda5, /dev/sda6, /dev/sda7, /dev/sdb5, /dev/sdb6), excluding the partition mounted at /home (/dev/sdb8)
  - SWAP partitions will be automatically selected to be formatted
  - ignore the partitions of windows (/dev/sda1, /dev/sda3, /dev/sda4) and the partition of data shared between linux and windows (/dev/sdb9)

- Continue until ubuntu is installed


## POST-FORMAT:

### General update
  - sudo apt-get update
  - sudo apt-get upgrade


### Add linux data partition
- Mount at boot by adding to /etc/fstab:
  ```bash
  # /media/jetxeberria/linux_storage manually set
  UUID=602880C531541E82 /media/jetxeberria/linux_storage ntfs defaults 0 2
  ```
- Restart and ensure home folders point to linux data partition. 
  ```bash
  cd ~
  ls -l
  ```

- If home partition has been formated. You'll need to:
  - Lowercase Desktop, Templates and Public
  ```bash
  mv Desktop desktop
  mv Templates templates
  mv Public public
  ```

  - Delete remaining folders in HOME and create links to those of linux_store partition
  ```bash
  rm -r Downloads Documents Music Video Pictures
  ```

- If links are in red/missing, update/make symbolic links
  ```bash
  ln -s /media/jetxeberria/linux_storage/data/documents/ documents
  ln -s /media/jetxeberria/linux_storage/data/downloads/ downloads
  ln -s /media/jetxeberria/linux_storage/data/video/ video
  ln -s /media/jetxeberria/linux_storage/data/music/ music
  ln -s /media/jetxeberria/linux_storage/data/pictures/ pictures
  ```

- Ensure configured user directories are properly written (lowercase) in $HOME/.config/user-dirs.dirs
  ```bash
  XDG_DESKTOP_DIR="$HOME/desktop"
  XDG_DOWNLOAD_DIR="$HOME/downloads"
  XDG_TEMPLATES_DIR="$HOME/templates"
  XDG_PUBLICSHARE_DIR="$HOME/public"
  XDG_DOCUMENTS_DIR="$HOME/documents"
  XDG_MUSIC_DIR="$HOME/music"
  XDG_PICTURES_DIR="$HOME/pictures"
  XDG_VIDEOS_DIR="$HOME/videos"
  ```



### Update nautilus bookmarks

- If home folders links have been updated / newly added, nautilus bookmarks must be updated.
- Open nautilus in the folder to make a bookmark from
  ```
  nautilus /media/jetxeberria/linux_partition/data/documents
  ```
- In option "Bookmarks" select "Bookmark this location" (CTRL+D)


### Install basic programs

#### terminator
```bash
sudo apt-get install terminator
```

#### keepassxc
```bash
sudo add-apt-repository ppa:phoerious/keepassxc
sudo apt-get update
```

### Foxit Reader
free from web

#### Configure firefox
- Log in account
- Enable bookmarks tab

#### git
```bash
sudo apt-get install git
```

##### Configure

git config --global user.email "etxeberria_92@hotmail.com"
git config --global user.name "jetxeberria"

##### Set SSH key
- Create SSH key
```bash
ssh-keygen -t rsa -b 4096 -c "workstation"
```
- Add SSH key to SSH-Agent
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```
Copy public key to your GitLab / GitHub user account
```bash
cat ~/.ssh/id_rsa | xclip -sel clip
```
- Go to `https://github.com/settings/keys` and CTRL+V


#### virtualenv
```bash
sudo apt-get install virtualenv
```

#### visual studio code
- Download .deb from https://code.visualstudio.com/
- Install with `dpkg -i ~/downloads/code_1.47.2-1594837870_amd64.deb`
- Run with `code .`


#### telegram
- Download tar from https://desktop.telegram.org/
- Untar in ~/documents/programs/telegram/
- Export executable path. Add in ~/.bashrc:
  ```bash
  export PATH=/media/jetxeberria/linux_partition/data/documents/programs/telegram:$PATH
  ```
- Rename Telegram executable for telegram

#### nmap
```bash
sudo apt-get install nmap
```

#### gimp

- Download flatpakref from https://www.gimp.org/downloads/
- Move launcher to dedicated folder (~/documents/programs/flatpak)
- Install GIMP:

```bash
flatpak install ~/documents/programs/flatpak/org.gimp.GIMP.flatpakref
```

OR with APT

```bash
sudo apt-get install gimp
```

#### flatpak


```bash
sudo apt install flatpak
```

- If below Ubuntu18.10, do previously:

```bash
sudo add-apt-repository ppa:alexlarsson/flatpak
sudo apt update
```

### vlc

Download a snap from: https://www.videolan.org/vlc/
Install with software "Software"


#### support exfat (by default supported in linux kernel >5.4)
```bash
sudo add-apt-repository universe
sudo apt update
sudo apt install exfat-fuse exfat-utils
```


### Add network printer

- Go to "printers" in Dash menu
- Press "Add"
- Press "Find Network Printer" and write printer IP if not found automatically
- Find printer IP with nmap
  - Find your IP with `ifconfig`. Suppose it's 192.168.1.20
  - Map your net with `sudo nmap -sn 192.168.1.0/24`
  - Test the resulting IPs
- Select drivers HP > Officejet 4500 g510n-z

### Upgrade to Ubuntu 18.04 from 16.04

- Run 
Issue: After update, Unity / Ubuntu doesn't launch, change graphical drivers to nvidia:
- Log in with virtual terminal (CTRL + ALT + F2)
- See current drivers in use: `sudo lshw -c display`
- See instalable drivers for your device: `sudo ubuntu-drivers devices`
- Install recommended driver: `sudo ubuntu-drivers autoinstall`
- Reboot: `sudo shutdown -r now`
- See current drivers in use: `sudo lshw -c display`

