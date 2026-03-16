# Distributed Network Load Test Launcher

## Overview

This repository contains a simple distributed testing setup used to simulate large numbers of systems accessing a network resource simultaneously.

The system works using a **controller–client model**:

* Client machines contain a `run.bat` script.
* A host (controller) machine triggers the execution of the test script.
* All clients start generating network requests at roughly the same time.

This setup helps simulate real scenarios such as **online examinations where hundreds of students access a server simultaneously**.

---

# System Components

## 1. Client Script

`run.bat`

This script must be placed on every client machine participating in the test.

Responsibilities of the script:

* Connect to the host machine
* Check the configured test version
* Download or locate the correct test script
* Execute the test file

### Important

Make sure the **host path is correctly configured inside the script** before deployment.

Example configuration inside the script:

HOST_PATH=\HOST_IP\test_share

The host path must point to the shared directory on the controller machine where test files are stored.

---

# Client Setup

1. Copy `run.bat` to every client machine.
2. Verify that the host path inside the script is correct.
3. Ensure the client machine can access the host machine through the network.
4. Test the script on one machine before deploying to all systems.

---

# Host (Controller) Setup

The host machine controls which test will run.

Steps:

1. Place all test scripts in the host shared folder.
2. Update the **test version or test filename** on the host system.
3. When the clients run `run.bat`, they will automatically execute the selected test.

This allows the controller machine to change test scenarios without modifying every client machine.

---

# Running the Test

1. Ensure all client machines have the `run.bat` script.
2. Confirm the host machine is reachable from the network.
3. Set the test version or test file on the host machine.
4. Trigger the clients to execute the script.

All client machines will begin executing the selected test script and start generating network requests.

---

# Notes

* Run a small test with a few machines before running the full load test.
* Make sure the network share permissions allow clients to access the host directory.
* Monitor network performance during the test to identify latency or congestion issues.

---

# Purpose

This system was used to simulate large-scale network activity to evaluate how the campus network performs when hundreds of systems access an online service simultaneously.
