# Local Install

Follow these instructions to build `ephys2` on your local machine!

**Note: Installing on Windows is not great. I would really recommend MacOS or Linux. The GUI will not work at all on Windows unfortunately due to WSL not easily supporting X11 applications.**


## 0. Prep for Windows installation
If you are building on Windows, there are a few extra steps. The easiest (and so far only successful way we've managed to do it) is to use Windows Subsystem for Linux (WSL), a recently developed compatibility layer that allows you to completely simulate a unix environment in Windows without a virtual machine.

### Enable WSL
First, enable the WSL feature in windows by opening Windows Powershell ***in Administrative Mode*** and executing the following:

```
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
```
Restart computer, re-open Windows Powershell (again as Administrator) and install the WSL environment by executing the following:
```bash
wsl --install -d Ubuntu
```
\
You will need to restart your computer after this installation finishes. After the restart, you should be able to open a new application called 'Ubuntu' which gives you direct access to a unix shell.

The central difference between the Windows and Linux install from here on out is that you have to do pretty much everything through the command-line in that Ubuntu (WSL) shell.

## 1. Clone Ephys2 Repo

Install git if you haven't yet: `sudo apt install git` on WSL/Linux, `git --version` on Mac (the command-line will then prompt you to install it).

Change directory to where you want to store the source code, then run the following and cd into that folder once it is done:
```bash
git clone https://gitlab.com/OlveczkyLab/ephys2.git
```

## 2. Run the ephys installer
In the command-line, cd to the installer folder of your newly cloned repo:

```bash
cd ephys2/ephys2/installer
```

and then run the following command:
```bash
bash installer.sh
```

After giving the shell your password and selecting the install and conda options, the rest should be done automatically!!

**Note: The full version of the install will take some time. It is downloading and compiling several requirement libraries and toolsets from source. Count on it taking 15-20 minutes.**

# Windows: accessing cluster drives from WSL shell
In order to access data to open/sort with ephys2, you will likely need to mount one of the cluster storage drives (Isilon/Lustre). The Ubuntu shell has your Windows `C:\` drive mounted by default under `/mnt/c/`, but you will need to mount any additional drives manually.

## Map network drive in Windows

In order to mount a network drive in the Ubuntu shell, you first must map the network drive to a drive letter in Windows. 

Assuming that you already have Isilon or Lustre mounted on your Windows PC, open Windows File Explorer and go to ***This PC***. 

At the top of the window near the toolbars, you should see a button to 'Map network drive'. Click it and select a drive letter to mount the network address to (from this point on, the instructions will assume the drive is mapped to `Z:\`).

## Mount network drive in WSL shell
First make a folder under `/mnt` corresponding to the drive you wish to mount:
```bash
sudo mkdir /mnt/z
```
\
Then edit your `fstab` file so that the shell mounts the network drive to this folder by default:

```bash
sudo gedit /etc/fstab
```

and add the following line to the end of the file (again assuming a drive letter of `Z:\`):
```bash
Z: /mnt/z drvfs defaults 0 0
```
\
Finally, activate your fstab file from the current shell:
```bash
sudo mount -a
```
\
You can now access all of the files in your network drive in the Ubuntu shell by entering `cd /mnt/z/`. 

# Using ephys2

## Run the pipeline without parallelization:
```bash
python -m ephys2.run workflow.yaml
```
## Run the pipeline with MPI (recommended):
```bash
mpirun -np $N_PROCS python -m ephys2.run workflow.yaml
```

where `$N_PROCS` is the number of parallel threads you want to use. (This will depend on how many threads your local computer has.)

## Run the GUI
```bash
python -m ephys2.gui
```

# Extra commands
## Run with debug statements:
```bash
mpirun -np $N_PROCS python -m ephys2.run workflow.yaml --verbose
```
Thread 0 will print debug statements.
## Profile the pipeline's serial performance: 
```bash
python -m ephys2.run workflow.yaml --profile
``` 
This can tell you which stage of your pipeline is the bottleneck in terms of speed.

## Profile the pipeline's parallel performance: 
```bash
mpirun -np $N_PROCS python -m ephys2.run workflow.yaml --profile
``` 
Thread 0 will print its profile upon completion. This can tell you how much time is spent in computation versus communication.