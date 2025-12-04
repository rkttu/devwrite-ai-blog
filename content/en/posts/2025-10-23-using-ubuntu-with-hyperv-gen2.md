---
title: "Booting Ubuntu on Hyper-V Generation 2 VM in Windows 10/11 Pro"
date: 2025-10-23T00:00:00+09:00
draft: false
slug: "using-ubuntu-with-hyperv-gen2"
tags:
  - Hyper-V
  - Ubuntu
  - Virtualization
  - Windows
categories:
  - Development Environment
translationKey: "using-ubuntu-with-hyperv-gen2"
cover:
  image: "images/posts/using-ubuntu-with-hyperv-gen2.jpg"
  alt: "Server virtualization environment image"
tldr: "If Ubuntu won't boot on a Hyper-V Gen 2 VM, change the Secure Boot template to 'Microsoft UEFI Certificate Authority'."
---

## Getting Started

Windows Pro includes Hyper-V by default. Without installing any additional virtualization software, you can create and manage virtual machines directly within the operating system. In this article, I'll walk you through how to boot Ubuntu using a Hyper-V Generation 2 virtual machine.

First, open PowerShell with administrator privileges and enter the following command to enable the Hyper-V feature:

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

Once the installation is complete, please reboot your system.

Next, launch "Hyper-V Manager" and create a new virtual machine. Make sure to select Generation 2 for the generation, allocate at least 4GB of memory, and specify at least 20GB of disk space.

For the network adapter, select "Default Switch" to get immediate internet connectivity without any additional configuration.

Now download the ISO image from the [official Ubuntu website](https://ubuntu.com/download/desktop), then connect it to the virtual machine's DVD drive under "Image file". In the Firmware settings, move the DVD drive to the top of the boot order so you can boot directly from the ISO.

## The Important Part

Up to this point, it's all standard procedure. However, when you actually try to install Ubuntu, you'll often encounter errors like "No bootable device" or "Start boot option" that prevent booting.

**The reason is simple: Hyper-V Generation 2 VMs use a Windows-specific UEFI Secure Boot template by default.**

To solve this problem, after creating the virtual machine, you must navigate to "Settings → Security".

Here, check **'Enable Secure Boot'**, and change the 'Template' option below to **"Microsoft UEFI Certificate Authority"**.
If this setting is not configured correctly, Ubuntu's bootloader will be recognized as an unsigned image and UEFI will block it from booting.
In other words, no matter how many times you recreate the ISO file or disk configuration, Ubuntu will never boot if this setting is missing.

Once you complete the above steps, the Ubuntu installation screen will appear normally, and you can proceed with the installation as guided.

Ubuntu 20.04 and later versions include Hyper-V integration services by default, so features like clipboard sharing, automatic screen resolution adjustment, and time synchronization work right out of the box without installing additional drivers.

In conclusion, to boot Ubuntu on a Hyper-V Generation 2 VM, you must set the 'Secure Boot template' to Microsoft UEFI Certificate Authority.

As long as you don't forget this one setting, you can reliably run Ubuntu and set up your development environment even in a Windows Pro environment.
