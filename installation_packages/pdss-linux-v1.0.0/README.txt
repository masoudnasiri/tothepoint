========================================================================
  PROCUREMENT DECISION SUPPORT SYSTEM (PDSS)
  Linux Installation Package v1.0.0
========================================================================

BUILD INFORMATION:
  Version: 1.0.0
  Build Date: 2025-10-22 00:30:04
  Platform: Linux

SYSTEM REQUIREMENTS:
  - Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+)
  - Docker Engine 20.10+
  - Docker Compose 1.29+
  - 4GB RAM minimum (8GB recommended)
  - 10GB free disk space

INSTALLATION INSTRUCTIONS:
  1. Ensure Docker and Docker Compose are installed
  2. Run: chmod +x install.sh
  3. Run: sudo ./install.sh
  4. Follow the on-screen instructions
  5. Access the system at http://localhost:3000

MANAGEMENT SCRIPTS (in scripts folder):
  - start.sh          Start the PDSS system
  - stop.sh           Stop the PDSS system
  - restart.sh        Restart the PDSS system
  - status.sh         Check system status
  - logs.sh           View system logs
  - backup.sh         Backup database
  - uninstall.sh      Uninstall PDSS

DEFAULT CREDENTIALS:
  Admin:       admin / admin123
  Finance:     finance1 / finance123
  PM:          pm1 / pm123
  Procurement: proc1 / proc123

  IMPORTANT: Change passwords after first login!

DOCUMENTATION:
  See the 'docs' folder for complete documentation

========================================================================
  Created: 2025-10-22 00:30:04
  Package: pdss-linux-v1.0.0
========================================================================
