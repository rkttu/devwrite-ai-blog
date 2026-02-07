---
title: "Docker Container Basics"
date: 2025-12-05T12:00:00+09:00
draft: true
slug: "docker-basics"
tags:
  - Docker
  - Container
  - DevOps
categories:
  - Development Environment
translationKey: "docker-basics"
description: "Learn the fundamentals of Docker, from installation to running your first container step by step."
tldr: "Learn the fundamentals of Docker, from installation to running your first container step by step."
cover:
  image: "images/posts/docker-basics.jpg"
  alt: "Image representing containers and server infrastructure"
---

Docker is a platform that allows you to run applications in isolated environments called containers. In this post, we'll explore Docker basics from concepts to running your first container.

## What is Docker?

Docker is a container-based virtualization platform. Unlike traditional virtual machines (VMs), containers share the host OS kernel, making them lighter and faster.

### Containers vs Virtual Machines

| Feature | Container | Virtual Machine |
|---------|-----------|-----------------|
| Startup time | Seconds | Minutes |
| Resource usage | Low | High |
| Isolation level | Process level | Full OS level |
| Image size | MBs | GBs |

## Installing Docker

### Windows

1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Run the installer and follow the instructions.
3. Enable the WSL 2 backend.

### macOS

```bash
brew install --cask docker
```

### Linux (Ubuntu)

```bash
# Set up the repository
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# Add Docker's GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

## Running Your First Container

Once installation is complete, let's run your first container.

```bash
docker run hello-world
```

This command performs the following:

1. Checks if the `hello-world` image exists locally
2. Downloads the image from Docker Hub if not found
3. Creates and runs a container from the image
4. Outputs a message and exits

## Common Docker Commands

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List images
docker images

# Stop a container
docker stop <container_id>

# Remove a container
docker rm <container_id>

# Remove an image
docker rmi <image_id>
```

## Exercise: Running an Nginx Web Server

Let's run a practical container. We'll run an Nginx web server in a container.

```bash
docker run -d -p 8080:80 --name my-nginx nginx
```

- `-d`: Run in background (detached mode)
- `-p 8080:80`: Map host port 8080 to container port 80
- `--name my-nginx`: Assign a name to the container

Visit `http://localhost:8080` in your browser to see the Nginx welcome page.

## Next Steps

Now that you've learned the basics of Docker, explore these topics:

- **Dockerfile**: Building custom images
- **Docker Compose**: Managing multiple containers
- **Docker Volume**: Managing data persistence
- **Docker Network**: Container-to-container communication

Docker makes development environment setup and deployment much easier. Happy containerizing! 🐳
