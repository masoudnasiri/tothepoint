# Quick Start Guide - Windows

Get Procurement DSS running on Windows in 5 minutes!

## Step 1: Install Docker Desktop

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install Docker Desktop
3. Start Docker Desktop and wait for it to be ready (green icon in system tray)

## Step 2: Download the Project

Download or clone the project to your computer.

## Step 3: Run the System

1. Open Command Prompt in the project folder
2. Double-click `start.bat` or run:
   ```cmd
   start.bat
   ```

That's it! The system will:
- Build the Docker images
- Start the database
- Start the backend API
- Start the frontend application

## Step 4: Access the Application

Open your browser and go to: **http://localhost:3000**

Login with:
- **Username**: admin
- **Password**: admin123

## Troubleshooting

### If Docker Desktop won't start:
1. Make sure virtualization is enabled in your BIOS
2. Enable WSL 2 in Windows Features
3. Restart your computer

### If ports are in use:
1. Close other applications using ports 3000, 8000, or 5432
2. Or change the ports in `docker-compose.yml`

### If you get permission errors:
1. Run Command Prompt as Administrator
2. Or add your user to the Docker Users group

## Available Commands

| Command | What it does |
|---------|-------------|
| `setup-windows.bat` | Check if your system is ready |
| `start.bat` | Start the system |
| `stop.bat` | Stop the system |
| `logs.bat` | View system logs |
| `reset.bat` | Reset all data |
| `check-system.bat` | Check system requirements |

## System Requirements

- Windows 10 (Build 19041+) or Windows 11
- 4GB+ RAM
- Docker Desktop
- Ports 3000, 8000, 5432 available

## Need Help?

1. Check the full [WINDOWS_SETUP.md](WINDOWS_SETUP.md) guide
2. Run `check-system.bat` to diagnose issues
3. Check Docker Desktop is running (green icon in system tray)
4. Try restarting Docker Desktop

## What's Next?

Once the system is running:
1. Login as admin
2. Create users for your team
3. Set up projects
4. Add procurement options
5. Configure budgets
6. Run optimization!

For detailed instructions, see the main [README.md](README.md).
