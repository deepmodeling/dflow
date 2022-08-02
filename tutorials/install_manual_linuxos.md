# Install on LinuxOS
## Container Engine
There are different container engine. But we recommend to use Docker.
This guide shows your how to install Docker Engine (not Docker Desktop). This is a useful guide if you are using dflow on a cloud. 
### Download
Go to Docker official website to follow the official download guide: [Get Docker](https://docs.docker.com/engine/install/#server)

We will show you how to install Docker Engine on a Ubuntu platform: [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

### Install using the repository 
This guide is copied from: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository.

#### Set up the repository
1.  Update the `apt` package index and install packages to allow `apt` to use a
    repository over HTTPS:

    ```console
    $ sudo apt-get update

    $ sudo apt-get install \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    ```

2.  Add Docker's official GPG key:

    ```console
    $ sudo mkdir -p /etc/apt/keyrings
    $ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    ```

3.  Use the following command to set up the repository:

    ```console
    $ echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] {{ download-url-base }} \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    ```

#### Install Docker Engine

1. Update the `apt` package index, and install the _latest version_ of Docker
   Engine, containerd, and Docker Compose, or go to the next step to install a specific version:

    ```console
    $ sudo apt-get update
    $ sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
    ```

    > Receiving a GPG error when running `apt-get update`?
    >  
    > Your default umask may not be set correctly, causing the public key file
    > for the repo to not be detected. Run the following command and then try to
    > update your repo again: `sudo chmod a+r /etc/apt/keyrings/docker.gpg`.

2.  To install a _specific version_ of Docker Engine, list the available versions
    in the repo, then select and install:

    a. List the versions available in your repo:

    ```console
    $ apt-cache madison docker-ce

    docker-ce | 5:20.10.16~3-0~ubuntu-jammy | https://download.docker.com/linux/ubuntu jammy/stable amd64 Packages
    docker-ce | 5:20.10.15~3-0~ubuntu-jammy | https://download.docker.com/linux/ubuntu jammy/stable amd64 Packages
    docker-ce | 5:20.10.14~3-0~ubuntu-jammy | https://download.docker.com/linux/ubuntu jammy/stable amd64 Packages
    docker-ce | 5:20.10.13~3-0~ubuntu-jammy | https://download.docker.com/linux/ubuntu jammy/stable amd64 Packages
    ```

    b. Install a specific version using the version string from the second column,
       for example, `5:20.10.16~3-0~ubuntu-jammy`.

    ```console
    $ sudo apt-get install docker-ce=<VERSION_STRING> docker-ce-cli=<VERSION_STRING> containerd.io docker-compose-plugin
    ```

### Verify the installation 
Run the `hello-world` official image to verify the installation.
```bash
docker run hello-world
```
This command downloads a test image and runs it in a container. When the
container runs, it prints a message and exits.

## Kubernetes
To use kubernetes, we can install minikube, a local kubernetes.

### Before installation
Check if you are the root user. Minikube does not allow root user to start. Follow the following guide to add a user. See the original issue here: https://github.com/kubernetes/minikube/issues/7903
#### Add new user
```bash
adduser developer 
#add the user. Follow the prompt
usermod -aG sudo developer
```
#### Login to the newly created user
```bash
su - developer
```
#### Add user to the Docker Group
```bash
sudo groupadd docker
sudo usermod -aG docker $USER
- Re-Login or Restart the Server
```

### Download 
#### Up-to-date version
Go to minikube official website to download: [Minikube](https://minikube.sigs.k8s.io/docs/start/)
#### Older version
**NOTE: this is the recommended route for users in China**. The minikube image repository for the up-to-date version is not correct, which leads to minikube start failure. 
- Install older version from the official github repository: [Releases · kubernetes/minikube](https://github.com/kubernetes/minikube/releases)
- Install older version using [mirror in China](https://npmmirror.com/): [minikube](https://registry.npmmirror.com/binary.html?path=minikube/) (The latest version that works is 1.25.2)

Command to install minikube older version (1.25.2)
```bash
curl -o minikube -L https://registry.npmmirror.com/-/binary/minikube/v1.25.2/minikube-linux-amd64
```
#### Install 
Install you downloaded minikube to `/usr/local/bin`:
```bash
sudo install minikube /usr/local/bin/minikube
```

#### Verify the installation 
```bash
minikube version
```


