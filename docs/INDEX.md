# 📚 PDSS Documentation Index

Welcome to the Procurement Decision Support System (PDSS) documentation!

---

## 🎯 Quick Start

**New to PDSS?** Start here:
1. [Platform Overview](./PLATFORM_OVERVIEW.md) - Understand what PDSS does
2. [Installation Guide](./installation/LINUX_SETUP.md) or [Windows Setup](./installation/WINDOWS_SETUP.md)
3. [User Guide](./USER_GUIDE.md) - Learn how to use the platform
4. [Procurement Workflow](./features/PROCUREMENT_WORKFLOW.md) - Understand the complete workflow

---

## 📖 Main Documentation

### Core Documentation
- **[Platform Overview](./PLATFORM_OVERVIEW.md)** 
  Complete system overview, features, architecture, and technology stack

- **[User Guide](./USER_GUIDE.md)**
  End-user documentation for all roles (PM, PMO, Procurement, Finance)

- **[Admin Guide](./ADMIN_GUIDE.md)**
  System administration, configuration, and maintenance

- **[API Documentation](./API_DOCUMENTATION.md)**
  RESTful API reference and integration guide

---

## 🚀 Installation & Setup

### Installation Guides
- **[Linux Installation](./installation/LINUX_SETUP.md)**
  Step-by-step installation for Linux servers

- **[Windows Installation](./installation/WINDOWS_SETUP.md)**
  Step-by-step installation for Windows systems

- **[Docker Setup](./README.md)**
  Quick start with Docker Compose

### Configuration
- **Environment Variables** - Configure `.env` settings
- **Database Setup** - PostgreSQL configuration
- **Security Configuration** - HTTPS, CORS, authentication

---

## 🎓 Feature Guides

### Workflow & Processes
- **[Procurement Workflow](./features/PROCUREMENT_WORKFLOW.md)**
  Complete procurement process from project to payment

- **[Logo Integration](./features/LOGO_INTEGRATION.md)**
  Branding customization guide

### Module-Specific Guides
- **Project Management** - Creating and managing projects
- **Item Management** - Master catalog and project items
- **Finalization Process** - PMO item approval workflow
- **Procurement Options** - Supplier comparison and selection
- **Optimization Engine** - Decision analysis and Pareto fronts
- **Financial Tracking** - Invoice and payment management
- **Analytics & Reports** - Business intelligence and insights

---

## 👥 Role-Based Guides

### By User Role

**Administrator**
- [Admin Guide](./ADMIN_GUIDE.md)
- User management
- System configuration
- Database administration
- Security & backups

**PMO (Project Management Office)**
- Project oversight
- Item finalization workflow ⭐
- Analytics and reporting
- User guide sections

**Project Manager (PM)**
- [User Guide](./USER_GUIDE.md#working-with-projects)
- Project creation
- Item management
- Progress tracking

**Procurement Team**
- [Procurement Workflow](./features/PROCUREMENT_WORKFLOW.md#phase-4-procurement-options)
- Viewing finalized items
- Creating supplier options
- Option comparison

**Finance Team**
- [Financial Tracking](./USER_GUIDE.md#financial-tracking)
- Decision optimization
- Payment tracking
- Cash flow management
- Analytics and forecasting

---

## 🔧 Technical Documentation

### Architecture & Design
- [Platform Overview - Architecture](./PLATFORM_OVERVIEW.md#architecture)
- System components
- Database schema
- API design patterns
- Security architecture

### API Reference
- [API Documentation](./API_DOCUMENTATION.md)
- Authentication
- Endpoints by module
- Request/response formats
- Error handling
- Rate limiting

### Development
- **Contributing Guidelines** - How to contribute
- **Code Style Guide** - Coding standards
- **Testing Guide** - Unit and integration tests
- **Deployment Guide** - Production deployment

---

## 🐛 Troubleshooting

### Common Issues
- **Can't see items in Procurement?**
  → Items must be finalized by PMO/Admin first

- **Login issues?**
  → Check username/password, verify user is active

- **Database connection errors?**
  → Verify Docker containers are running

- **API errors?**
  → Check backend logs: `docker-compose logs backend`

### Resources
- **[Admin Guide - Troubleshooting](./ADMIN_GUIDE.md#troubleshooting)**
- **[Common Issues](./troubleshooting/COMMON_ISSUES.md)** (coming soon)
- **[FAQ](./troubleshooting/FAQ.md)** (coming soon)
- **[Debugging Guide](./troubleshooting/DEBUGGING.md)** (coming soon)

---

## 📚 Reference Materials

### Quick Reference

**Common Tasks**
| Task | Guide | Role |
|------|-------|------|
| Create a project | [User Guide](./USER_GUIDE.md#working-with-projects) | PM/PMO |
| Add project items | [User Guide](./USER_GUIDE.md#managing-project-items) | PM/PMO |
| Finalize items | [Procurement Workflow](./features/PROCUREMENT_WORKFLOW.md#phase-3-item-finalization-key-gate) | PMO/Admin |
| Create procurement options | [Procurement Workflow](./features/PROCUREMENT_WORKFLOW.md#phase-4-procurement-options) | Procurement |
| Run optimization | [User Guide](./USER_GUIDE.md#analytics--reports) | Finance/Admin |
| Track payments | [User Guide](./USER_GUIDE.md#financial-tracking) | Finance |

**System Commands**
```bash
# Start platform
docker-compose up -d

# Stop platform
docker-compose down

# View logs
docker-compose logs -f backend

# Backup database
docker-compose exec postgres pg_dump -U postgres procurement_dss > backup.sql

# Access database
docker-compose exec postgres psql -U postgres -d procurement_dss
```

**Default Ports**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Database: `localhost:5432`

---

## 🔐 Security & Compliance

### Security Documentation
- Authentication & authorization
- Role-based access control (RBAC)
- Password policies
- Data encryption
- Audit logging
- Backup & recovery

### Best Practices
- [Admin Guide - Security](./ADMIN_GUIDE.md#security--access-control)
- Regular password changes
- User access reviews
- Security updates
- Backup procedures

---

## 📈 Analytics & Reporting

### Available Reports
- Project summary reports
- Procurement performance
- Supplier analysis
- Cost trends
- Budget variance
- Timeline adherence
- Cash flow forecasts

### Dashboards
- Executive dashboard
- Project dashboards
- Procurement dashboards
- Financial dashboards
- Analytics & forecasting

---

## 🔄 Updates & Releases

### Version History
- **v1.0.0** (2025-10-20) - Initial release
  - Core procurement workflow
  - Item finalization feature
  - Logo integration
  - Multi-currency support
  - Decision optimization engine

### Coming Soon
- **v1.1.0**
  - Email notifications
  - Advanced reporting
  - Bulk operations
  - Mobile responsive design

- **v2.0.0**
  - AI-powered recommendations
  - Predictive analytics
  - Supplier rating system

---

## 📞 Support & Community

### Getting Help

**Documentation**
- Read relevant guide above
- Check troubleshooting section
- Review API documentation
- Check FAQ

**Technical Support**
- Email: <support-email>
- Issue Tracker: <github-issues>
- Documentation: This site

**Training & Consulting**
- User training sessions
- Administrator workshops
- Custom development
- System integration

---

## 📝 Contributing

We welcome contributions!

- **Report Bugs** - Submit issues on GitHub
- **Suggest Features** - Share your ideas
- **Improve Documentation** - Submit pull requests
- **Share Feedback** - Help us improve

---

## 📜 License & Legal

- **License:** [Specify License]
- **Privacy Policy:** [Link to policy]
- **Terms of Service:** [Link to terms]

---

## 🏢 About

**Developed by:** InoTech

**Technology Stack:**
- Frontend: React + TypeScript + Material-UI
- Backend: FastAPI + Python
- Database: PostgreSQL
- Deployment: Docker + Docker Compose

**Built with ❤️ for better procurement decisions**

---

## 📅 Document Updates

This documentation is actively maintained. Last updated: **October 20, 2025**

**Document Update Schedule:**
- Major features: Updated immediately
- Minor changes: Weekly
- Version releases: With each release
- Security updates: As needed

---

## 🗺️ Documentation Roadmap

**Coming Soon:**
- Video tutorials
- Interactive demos
- Extended API examples
- Mobile app guide
- Integration examples
- Performance tuning guide
- Disaster recovery guide
- Compliance checklists

---

## Quick Navigation

### By Topic
- [📱 Features](#-feature-guides)
- [👥 Roles](#-role-based-guides)
- [🔧 Technical](#-technical-documentation)
- [🐛 Help](#-troubleshooting)
- [📚 Reference](#-reference-materials)

### By Task
- [Getting Started](#-quick-start)
- [Installation](#-installation--setup)
- [User Tasks](#-role-based-guides)
- [Admin Tasks](#-technical-documentation)
- [API Integration](#-technical-documentation)

---

*Have questions? Check the [User Guide](./USER_GUIDE.md) or [Admin Guide](./ADMIN_GUIDE.md)*

*Need technical details? See [API Documentation](./API_DOCUMENTATION.md)*

*Want to understand workflows? Read [Procurement Workflow](./features/PROCUREMENT_WORKFLOW.md)*

---

**Welcome to PDSS! Let's make procurement decisions easier.** 🚀

