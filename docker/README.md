Install [Docker](https://www.docker.com/) and ensure the daemon is started on your machine.

# Build (for developers)

From the project root (../../)[../../] do:
```bash
docker build --platform linux/amd64 . -f docker/GUI/Dockerfile -t ephys2_gui
```
(The explicit `--platform` call is required if building on an Apple Silicon or other non-`x86_64` machines.)

# Run (for users)

Pull the latest Docker image from the GitLab:
```bash
docker pull registry.gitlab.com/olveczkylab/ephys2/ephys2_gui
```
(if you ran the build command above, no need to do this.)

## Linux
```bash
xhost +local:root
docker run -it \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /:/mnt/ \
  -w /mnt/host_mnt \
  -e DISPLAY=unix$DISPLAY \
  ephys2_gui
```

## MacOS
The following instructions are copied from [this runbook](https://joshuamccall.com/articles/docker.html).

```bash
brew install xquartz socat
```
Restart your machine, then open XQuartz. Open `Preferences -> Security`, and ensure both boxes are checked. Then in a separate terminal, run:
```bash
socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\"
```
Finally, run:
```bash
ip=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
xhost + $ip
docker run -it \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /:/mnt/ \
  -w /mnt/host_mnt \
  -e DISPLAY=$ip:0 \
  ephys2_gui
```
(It's best to run these commands together since your IP address may change periodically.)

## Windows
