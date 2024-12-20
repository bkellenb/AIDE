# Installing AIDE

* [Compatibility](#compatibility)
* [New installation](#new-installation)
    * [Microsoft Windows](#microsoft-windows)
        * [With the Installer](#with-the-installer)
    * [macOS](#macos)
        * [With the Installer](#with-the-installer-1)
    * [Ubuntu / Debian](#ubuntu--debian)
        * [With the Installer](#with-the-installer-2)
        * [With Docker](#with-docker-1)
* [Manual installation](#manual-installation)
    * [Microsoft Windows](#microsoft-windows-1)
    * [Ubuntu / Debian](#ubuntu--debian-1)
* [Migration from previous versions of AIDE](#migration-from-previous-versions-of-aide)
    * [from AIDE v1](#from-aide-v1)
    * [from AIDE v2](#from-aide-v2)



## Compatibility

Below is a compatibility matrix of operating systems (OS), Python, and PyTorch:

| **OS** | **Python** | **PyTorch** | **verified** | **comments** |
|---|---|---|---|---|
| Ubuntu 24.04 LTS | 3.9 to 3.11 | 2.0.0 and above | ✅ | Python 3.10 and above: Detectron2 requires GCC ver. 9 or higher. |
| macOS 11 to 14.4.1 | 3.9 to 3.11 | 2.0.0 and above | ✅ | Python 3.8 and below cause problems with imagecodecs library under macOS with Apple Silicon:  [see here](https://github.com/cgohlke/imagecodecs/issues/72). |
| Microsoft Windows 10 | 3.9 to 3.11 | 2.0.0 and above |  | Requires WSL2 |


Updates on compatibility:
* November 21, 2024: minimum Ubuntu version is 24.04 LTS (due to rasterio requiring GDAL >= 3.5,
  which is not available on older distributions).
  AIDE will soon require Python >= 3.10 due to the [Ultralytics](https://github.com/ultralytics/ultralytics) dependency.


_Note:_ You can help complete these compatibility matrices! Since we cannot test every possible
hard- and software combination, we would love to hear feedback regarding experiences and (in-)
compatibilities. Please report the following:
* Installation log (as produced by the installer)
* Terminal/command line output (as much as is available; make sure to remove sensitive information)
* Information about your operating system (Linux: `uname -a`; macOS: `sw_vers`), as well as versions
  of Python (`python -V`) and CUDA (`nvidia-smi`).

Thank you very much!



## New installation

### Microsoft Windows

_Note:_ these are preliminary instructions and still subject to extensive testing. They currently apply to Windows 11; Windows 10 will follow.


#### With the Installer

__Prerequisites:__ You need Windows 10 or greater and support for [Windows Subsystem for Linux](https://docs.microsoft.com/en-gb/windows/wsl/install-manual) to install and use AIDE on a Windows machine.

1. Install the [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-gb/windows/wsl/install-manual). Select "Ubuntu 20.04.4 LTS" as an image in the Microsoft store.
2. If not running, open a new WSL shell: click "Start", type "wsl", select "wsl - Run command". All the rest below must be issued in this new command window.
3. Install [Conda](https://conda.io/) (important: download the Linux binaries); follow any instructions during the install process:
```bash
cd ${HOME}
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh   # follow instructions prompted

source .bashrc
```
4. Create Python environment and clone AIDE repository:
```bash
conda create -y -n aide python=3.9
conda activate aide

git clone https://github.com/bkellenb/AIDE.git && cd AIDE
```
5. Launch installer and follow the instructions:
```bash
./install/install_debian.sh
```

6. To start AIDE: open a WSL shell if not already open (see Step 2 above how to do so) and issue these commands:
```bash
cd ${HOME}/aerial_wildlife_detection
conda activate aide
export AIDE_CONFIG_PATH=config/settings.ini
export AIDE_MODULES=LabelUI,AIController,AIWorker,FileServer
export PYTHONPATH=.
./AIDE.sh start
```

#### With Docker

Coming soon.


### macOS

_Note:_ these are preliminary instructions and still subject to extensive testing.

#### With the Installer

1. Install [Homebrew](https://brew.sh/):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. Clone the AIDE repository:
```bash
git clone https://github.com/bkellenb/AIDE.git && cd AIDE
```
3. Launch installer and follow the instructions:
```bash
    ./install/install_darwin.sh
```
4. To start AIDE:
```bash
cd ${HOME}/aerial_wildlife_detection
export AIDE_CONFIG_PATH=config/settings.ini
export AIDE_MODULES=LabelUI,AIController,AIWorker,FileServer
export PYTHONPATH=.
./AIDE.sh start 0 python3.9
```

_NOTES:_
* The macOS installer uses Homebrew instead of Conda and installs a dedicated version of Python
  (3.9). You _can_ use Conda as well by providing an extra flag to the installation script:
  `--python_exec=/path/to/python`. Don't forget to provide this path to the `AIDE.sh` script as
  well.
* Launch Agents (_i.e._, starting AIDE services upon login) are under development and not yet
  supported.
* The entire script has been tested on an Apple Silicon-based machine, but not yet under the x86
  architecture. It likely still contains lots of bugs, so treat it as an alpha.
* macOS 11 or greater is strongly recommended (tested up to macOS 14.4.1).
* Both the default `zsh` and `bash` should work.
* April 25, 2024: Python 3.8 causes issues under macOS with Apple Silicon due to `imagecodecs`
  dependency. The default Python version for the macOS installer has therefore been bumped to 3.9.
  See [install_manual.md](install_manual.md) for more details.


#### With Docker

If you wish to install AIDE in a self-contained environment instead of the host operating system,
you can do so with Docker:

1. Download and install [Docker](https://docs.docker.com/desktop/install/mac-install/). Once copied
   from the disk image, open the Docker application and accept the license agreement.
2. Clone the AIDE repository: `git clone https://github.com/bkellenb/AIDE.git && cd AIDE`
3. **Important:** modify the `docker/settings.ini` file and replace the default super user
   credentials (section `[Project]`) with new values. Make sure to review and update the other
   default settings as well, if needed.
4. Install:
    ```bash
        cd docker
        docker compose build
        cd ..
    ```
5. Launch:
    * With Docker:
    ```bash
        cd docker
        docker compose up
    ```



### Ubuntu / Debian

#### With the Installer

1. Install a Python environment manager, such as [Conda](https://conda.io/) (recommended and used
   below) or [Virtualenv](https://virtualenv.pypa.io):
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh   # follow instructions prompted

source .bashrc
```
2. Create a new Python environment for AIDE:
```bash
    conda create -y -n aide python=3.9
    conda activate aide
```
3. Clone the AIDE repository:
```bash
git clone https://github.com/bkellenb/AIDE.git && cd AIDE
```
4. Launch installer and follow the instructions:
```bash
    ./install/install_debian.sh
```

__Tip:__ the installer also supports more advanced configurations; you can check it out by calling
`./install/install_debian.sh --help`.



#### With Docker

If you wish to install AIDE in a self-contained environment instead of the host operating system,
you can do so with Docker:

1. Download and install [Docker](https://docs.docker.com/engine/install) as well as [Docker
   Compose](https://docs.docker.com/compose/install)
2. If you want to use a GPU, you have to install the NVIDIA container toolkit:
```bash
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
```
3. Clone the AIDE repository: `git clone https://github.com/bkellenb/AIDE.git && cd AIDE`
4. **Important:** modify the `docker/settings.ini` file and replace the default super user credentials (section `[Project]`) with new values. Make sure to review and update the other default settings as well, if needed.
5. Install:
    ```bash
        cd docker
        sudo docker compose build
        cd ..
    ```
    _Note:_ for older versions, you might have to issue `sudo docker-compose build` (with a hyphen) instead.
6. Launch:
    * With Docker:
    ```bash
        sudo docker/docker_run_cpu.sh     # for machines without a GPU
        sudo docker/docker_run_gpu.sh     # for AIWorker instances with a CUDA-enabled GPU (strongly recommended for model training)
    ```
    * With Docker Compose (note that Docker Compose currently does not provide support for GPUs):
    ```bash
        cd docker
        sudo docker-compose up
    ```

### Manual installation


#### Microsoft Windows

__Prerequisites:__ You need Windows 10 or greater and support for [Windows Subsystem for Linux](https://docs.microsoft.com/en-gb/windows/wsl/install-manual) to install and use AIDE on a Windows machine.

1. Install the [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-gb/windows/wsl/install-manual). Select "Ubuntu 20.04.4 LTS" as an image in the Microsoft store.
2. If not running, open a new WSL shell: click "Start", type "wsl", select "wsl - Run command".
3. Follow the instructions [here](install_manual.md) for instructions on configuring an instance of AIDE.
4. Then, see [here](launch_aide.md) for instructions on launching an instance of AIDE. Be aware that all commands must be issued in a WSL shell as explained in Step 2 above.


### Ubuntu / Debian

See [here](install_manual.md) for instructions on configuring an instance of AIDE.

After that, see [here](launch_aide.md) for instructions on launching an instance of AIDE.



## Migration from previous versions of AIDE

### from AIDE v1
If you have [AIDE v1](https://github.com/bkellenb/AIDE/tree/v1) already running and want to upgrade its contents to AIDE v3, see [here](upgrade_from_v1.md).

### from AIDE v2
1. Create a back up of your data and PostgreSQL database prior to upgrading.
2. Clone the latest v3 repository
3. Make sure your configuration *.ini file is correct (the same as for your existing v2 installation can be used) and that the AIDE root path is set to the new v3 repository (check `systemd` processes as well if AIDE got installed via the installer script).
4. Restart all AIDE services. Upon next launch, the database schema will automatically be updated to v3 specifications.